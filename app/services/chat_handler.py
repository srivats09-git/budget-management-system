from typing import Dict, Any, Optional, List
import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.database_models import Employee, Budget, AOP, CostCenter
from .aop_service import AOPService
from .employee_service import EmployeeService
from .budget_service import BudgetService

class ChatHandler:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.aop_service = AOPService(db_session)
        self.employee_service = EmployeeService(db_session)
        self.budget_service = BudgetService(db_session)
        self.authenticated = False
        self.current_user: Optional[Employee] = None

    def process_message(self, message: str) -> str:
        """Process incoming chat messages"""
        if not self.authenticated:
            if message.strip() == "IKnowYou241202":
                self.authenticated = True
                return "Authentication successful. How can I help you today?"
            return "Please authenticate with the correct code to continue."

        # Set current user if not set
        if not self.current_user and "as" in message.lower():
            ldap_match = re.search(r"as\s+(\w+)", message.lower())
            if ldap_match:
                try:
                    self.current_user = self.db.query(Employee).filter(
                        Employee.ldap == ldap_match.group(1),
                        Employee.is_active == True
                    ).first()
                    if self.current_user:
                        return f"Now operating as {self.current_user.first_name} {self.current_user.last_name}"
                except Exception as e:
                    return f"Error setting user: {str(e)}"

        # Command parsing
        message = message.lower().strip()
        
        try:
            if message.startswith("add user"):
                return self._handle_add_user(message)
            elif message.startswith("remove user"):
                return self._handle_remove_user(message)
            elif message.startswith("show me my organization"):
                return self._handle_show_organization()
            elif message.startswith("show me my budget"):
                return self._handle_show_budget()
            elif message.startswith("chart budgets"):
                return self._handle_chart_budgets(message)
            elif message.startswith("add aop"):
                return self._handle_add_aop(message)
            elif message.startswith("add budget"):
                return self._handle_add_budget(message)
            elif message.startswith("update budget state"):
                return self._handle_update_budget_state(message)
            elif message.startswith("reconcile aop"):
                return self._handle_reconcile_aop(message)
            else:
                return self._handle_external_query(message)
        except Exception as e:
            return f"Error processing request: {str(e)}"

    def _handle_add_user(self, message: str) -> str:
        """Handle add user command with progressive prompting"""
        # Extract provided information
        ldap_match = re.search(r"ldap\s+(\w+)", message)
        fname_match = re.search(r"first name\s+(\w+)", message)
        lname_match = re.search(r"last name\s+(\w+)", message)
        email_match = re.search(r"email\s+(\S+@\S+)", message)
        level_match = re.search(r"level\s+(\d+)", message)
        cc_match = re.search(r"cost center\s+(\w+)", message)
        manager_match = re.search(r"manager\s+(\w+)", message)

        # Build response based on missing information
        missing_info = []
        user_info = {}

        if ldap_match:
            user_info['ldap'] = ldap_match.group(1)
        else:
            missing_info.append("LDAP username")

        if fname_match:
            user_info['first_name'] = fname_match.group(1)
        else:
            missing_info.append("first name")

        if lname_match:
            user_info['last_name'] = lname_match.group(1)
        else:
            missing_info.append("last name")

        if email_match:
            user_info['email'] = email_match.group(1)
        else:
            missing_info.append("email")

        if level_match:
            level = int(level_match.group(1))
            if 1 <= level <= 12:
                user_info['level'] = level
            else:
                return "Level must be between 1 and 12"
        else:
            missing_info.append("level (1-12)")

        if cc_match:
            cost_center = self.db.query(CostCenter).filter_by(code=cc_match.group(1)).first()
            if not cost_center:
                return f"Cost center {cc_match.group(1)} not found"
            user_info['cost_center_code'] = cc_match.group(1)
        else:
            missing_info.append("cost center code")

        if manager_match:
            user_info['manager_ldap'] = manager_match.group(1)

        if missing_info:
            return f"Please provide the following information: {', '.join(missing_info)}"

        try:
            self.employee_service.create_employee(**user_info)
            return f"User {user_info['ldap']} created successfully"
        except Exception as e:
            return f"Error creating user: {str(e)}"

    def _handle_show_organization(self) -> str:
        """Handle show organization command"""
        if not self.current_user:
            return "Please specify your LDAP username first (use 'as <ldap>')"

        try:
            org_structure = self.employee_service.get_organization_hierarchy(self.current_user.ldap)
            
            def format_org_tree(node: Dict, level: int = 0) -> List[str]:
                result = ["  " * level + f"- {node['name']} ({node['ldap']})"]
                for report in node.get('reports', []):
                    result.extend(format_org_tree(report, level + 1))
                return result
            
            if not org_structure:
                return "No organization structure found"
                
            return "Organization Structure:\n" + "\n".join(format_org_tree(org_structure))
        except Exception as e:
            return f"Error retrieving organization: {str(e)}"

    def _handle_show_budget(self) -> str:
        """Handle show budget command"""
        if not self.current_user:
            return "Please specify your LDAP username first (use 'as <ldap>')"

        try:
            budget_summary = self.budget_service.get_organization_budget_summary(self.current_user.ldap)
            
            if not budget_summary:
                return "No budget information found"
                
            result = ["Budget Summary:"]
            result.append(f"\nTotal Budget: ${budget_summary['total']:,.2f}")
            result.append("\nBreakdown by Employee:")
            
            for emp in budget_summary['by_employee']:
                result.append(f"- {emp['name']}: ${emp['amount']:,.2f}")
                
            return "\n".join(result)
        except Exception as e:
            return f"Error retrieving budget: {str(e)}"

    def _handle_chart_budgets(self, message: str) -> Dict:
        """Handle budget charting command"""
        aop_match = re.search(r"for aop\s+(\d+)", message)
        if not aop_match:
            return "Please specify an AOP ID (e.g., 'chart budgets for aop 1')"
            
        try:
            aop_id = int(aop_match.group(1))
            chart_data = self.budget_service.get_budget_chart_data(aop_id)
            
            return {
                "type": "chart",
                "chartType": "bar",
                "data": chart_data
            }
        except Exception as e:
            return f"Error generating chart: {str(e)}"

    def _handle_remove_user(self, message: str) -> str:
        """Handle remove user command"""
        ldap_match = re.search(r"remove user\s+(\w+)", message)
        if not ldap_match:
            return "Please specify the LDAP username to remove"
            
        try:
            ldap = ldap_match.group(1)
            self.employee_service.remove_employee(ldap)
            return f"User {ldap} has been removed"
        except ValueError as e:
            return str(e)

    def _handle_add_aop(self, message: str) -> str:
        """Handle add AOP command"""
        name_match = re.search(r"name\s+\"([^\"]+)\"", message)
        amount_match = re.search(r"amount\s+(\d+(?:\.\d{1,2})?)", message)
        
        if not name_match or not amount_match:
            return "Please provide AOP name and amount (e.g., 'add aop name \"FY2024\" amount 1000000')"
            
        try:
            name = name_match.group(1)
            amount = float(amount_match.group(1))
            aop = self.aop_service.create_aop(name, amount)
            return f"AOP {name} created with amount ${amount:,.2f}"
        except Exception as e:
            return f"Error creating AOP: {str(e)}"

    def _handle_add_budget(self, message: str) -> str:
        """Handle add budget command"""
        if not self.current_user:
            return "Please specify your LDAP username first (use 'as <ldap>')"
            
        # Extract budget information
        aop_match = re.search(r"aop\s+(\d+)", message)
        amount_match = re.search(r"amount\s+(\d+(?:\.\d{2})?)", message)
        project_match = re.search(r"project\s+\"([^\"]+)\"", message)
        desc_match = re.search(r"description\s+\"([^\"]+)\"", message)
        employee_match = re.search(r"for\s+(\w+)", message)
        
        missing = []
        if not aop_match:
            missing.append("AOP ID")
        if not amount_match:
            missing.append("amount")
        if not project_match:
            missing.append("project name (in quotes)")
            
        if missing:
            return f"Please provide: {', '.join(missing)}"
            
        try:
            budget_data = {
                "aop_id": int(aop_match.group(1)),
                "amount": float(amount_match.group(1)),
                "project": project_match.group(1),
                "description": desc_match.group(1) if desc_match else "",
                "employee_ldap": employee_match.group(1) if employee_match else self.current_user.ldap
            }
            
            budget = self.budget_service.create_budget(**budget_data)
            return f"Budget created successfully with ID: {budget.budget_id}"
        except Exception as e:
            return f"Error creating budget: {str(e)}"

    def _handle_update_budget_state(self, message: str) -> str:
        """Handle update budget state command"""
        budget_match = re.search(r"budget\s+(\w+)", message)
        state_match = re.search(r"to\s+(active|inactive)", message)
        
        if not budget_match or not state_match:
            return "Please specify budget ID and state (e.g., 'update budget state BUD001 to inactive')"
            
        try:
            budget_id = budget_match.group(1)
            is_active = state_match.group(1) == 'active'
            self.budget_service.update_budget_state(budget_id, is_active)
            return f"Budget {budget_id} state updated to {state_match.group(1)}"
        except Exception as e:
            return f"Error updating budget state: {str(e)}"

    def _handle_reconcile_aop(self, message: str) -> str:
        """Handle reconcile AOP command"""
        aop_match = re.search(r"reconcile aop\s+(\d+)", message)
        if not aop_match:
            return "Please specify AOP ID (e.g., 'reconcile aop 1')"
            
        try:
            aop_id = int(aop_match.group(1))
            result = self.aop_service.reconcile_aop(aop_id)
            
            status = "compliant" if result['is_compliant'] else "non-compliant"
            return (f"AOP Reconciliation Results:\n"
                   f"AOP Amount: ${result['aop_amount']:,.2f}\n"
                   f"Total Budget: ${result['total_budget']:,.2f}\n"
                   f"Difference: ${result['difference']:,.2f}\n"
                   f"Status: {status}")
        except Exception as e:
            return f"Error reconciling AOP: {str(e)}"

    def _handle_external_query(self, message: str) -> str:
        """Handle non-budget queries using external LLM service"""
        # In a real implementation, this would integrate with an external LLM service
        return "I understand this is a non-budget related query. [External LLM response would be provided here]"