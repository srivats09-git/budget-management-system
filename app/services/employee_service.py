from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from .models import Employee, Budget, AOP

class EmployeeService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_employee(self, ldap: str, first_name: str, last_name: str, 
                       email: str, level: int, cost_center_code: str,
                       manager_ldap: Optional[str] = None) -> Employee:
        """Create or reactivate an employee"""
        # Check for existing inactive employee
        existing_employee = self.db.query(Employee).filter(
            Employee.ldap == ldap
        ).first()
        
        if existing_employee:
            if existing_employee.is_active:
                raise ValueError(f"Employee with LDAP {ldap} already exists")
            # Reactivate employee
            existing_employee.is_active = True
            existing_employee.first_name = first_name
            existing_employee.last_name = last_name
            existing_employee.email = email
            existing_employee.level = level
            self.db.commit()
            return existing_employee
            
        # Create new employee
        employee = Employee(
            ldap=ldap,
            first_name=first_name,
            last_name=last_name,
            email=email,
            level=level,
            cost_center_code=cost_center_code
        )
        
        if manager_ldap:
            manager = self.db.query(Employee).filter(
                Employee.ldap == manager_ldap,
                Employee.is_active == True
            ).first()
            if not manager:
                raise ValueError(f"Manager with LDAP {manager_ldap} not found")
            employee.manager_id = manager.id
            
        self.db.add(employee)
        self.db.commit()
        return employee

    def remove_employee(self, ldap: str) -> None:
        """Remove (deactivate) an employee"""
        employee = self.db.query(Employee).filter(
            Employee.ldap == ldap,
            Employee.is_active == True
        ).first()
        
        if not employee:
            raise ValueError(f"Active employee with LDAP {ldap} not found")
            
        # Check for active budgets
        active_budgets = self.db.query(Budget).filter(
            Budget.employee_id == employee.id,
            Budget.is_active == True,
            Budget.aop_id == AOP.id,
            AOP.state == 'active'
        ).first()
        
        if active_budgets:
            raise ValueError("Cannot remove employee with active budgets")
            
        employee.is_active = False
        self.db.commit()

    def get_organization_hierarchy(self, ldap: str) -> Dict:
        """Get organization hierarchy for an employee"""
        def build_hierarchy(emp: Employee) -> Dict:
            return {
                'ldap': emp.ldap,
                'name': f"{emp.first_name} {emp.last_name}",
                'level': emp.level,
                'reports': [build_hierarchy(report) for report in emp.reports if report.is_active]
            }
            
        employee = self.db.query(Employee).filter(
            Employee.ldap == ldap,
            Employee.is_active == True
        ).first()
        
        if not employee:
            raise ValueError(f"Employee with LDAP {ldap} not found")
            
        return build_hierarchy(employee)

    def get_all_reports(self, ldap: str) -> List[Employee]:
        """Get all reports (direct and indirect) for an employee"""
        def get_reports_recursive(emp: Employee) -> List[Employee]:
            all_reports = []
            for report in emp.reports:
                if report.is_active:
                    all_reports.append(report)
                    all_reports.extend(get_reports_recursive(report))
            return all_reports
            
        employee = self.db.query(Employee).filter(
            Employee.ldap == ldap,
            Employee.is_active == True
        ).first()
        
        if not employee:
            raise ValueError(f"Employee with LDAP {ldap} not found")
            
        return get_reports_recursive(employee)

    def validate_employee_in_org(self, manager_ldap: str, employee_ldap: str) -> bool:
        """Validate if an employee is in manager's organization"""
        reports = self.get_all_reports(manager_ldap)
        return any(report.ldap == employee_ldap for report in reports)