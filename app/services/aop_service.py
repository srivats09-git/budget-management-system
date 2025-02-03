from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from .models import AOP, AOPDetail, Budget, AOPState

class AOPService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_aop(self, name: str, total_amount: float) -> AOP:
        """Create a new AOP in draft state"""
        aop = AOP(
            name=name,
            total_amount=total_amount,
            state=AOPState.DRAFT
        )
        self.db.add(aop)
        self.db.commit()
        return aop

    def update_aop_state(self, aop_id: int, new_state: AOPState) -> AOP:
        """Update AOP state with validations"""
        aop = self.db.query(AOP).filter(AOP.id == aop_id).first()
        if not aop:
            raise ValueError("AOP not found")

        if new_state == AOPState.ACTIVE:
            # Check if any other AOP is active
            active_aop = self.db.query(AOP).filter(
                AOP.state == AOPState.ACTIVE,
                AOP.id != aop_id
            ).first()
            if active_aop:
                raise ValueError("Another AOP is already active")
            
            # Validate total budget amounts
            total_budget = self.db.query(func.sum(Budget.amount)).filter(
                Budget.aop_id == aop_id,
                Budget.is_active == True
            ).scalar() or 0.0
            
            if total_budget > aop.total_amount:
                raise ValueError("Total budgets exceed AOP amount")

        aop.state = new_state
        self.db.commit()
        return aop

    def add_aop_detail(self, aop_id: int, cost_center_id: int, amount: float) -> AOPDetail:
        """Add detail to AOP and update total amount"""
        aop = self.db.query(AOP).filter(AOP.id == aop_id).first()
        if not aop:
            raise ValueError("AOP not found")
        
        if aop.state == AOPState.ACTIVE:
            raise ValueError("Cannot modify active AOP directly")
        
        detail = AOPDetail(
            aop_id=aop_id,
            cost_center_id=cost_center_id,
            amount=amount
        )
        self.db.add(detail)
        
        # Update AOP total
        aop.total_amount = self.db.query(func.sum(AOPDetail.amount)).filter(
            AOPDetail.aop_id == aop_id
        ).scalar() or 0.0
        
        self.db.commit()
        return detail

    def reconcile_aop(self, aop_id: int) -> dict:
        """Reconcile AOP with active budgets"""
        aop = self.db.query(AOP).filter(AOP.id == aop_id).first()
        if not aop:
            raise ValueError("AOP not found")
        
        total_budget = self.db.query(func.sum(Budget.amount)).filter(
            Budget.aop_id == aop_id,
            Budget.is_active == True
        ).scalar() or 0.0
        
        return {
            "aop_amount": aop.total_amount,
            "total_budget": total_budget,
            "difference": aop.total_amount - total_budget,
            "is_compliant": total_budget <= aop.total_amount
        }