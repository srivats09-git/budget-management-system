from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class AOPState(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    EOL = "eol"

class AOP(Base):
    __tablename__ = 'aop'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    total_amount = Column(Float, nullable=False, default=0.0)
    state = Column(SQLEnum(AOPState), default=AOPState.DRAFT)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    details = relationship("AOPDetail", back_populates="aop")
    budgets = relationship("Budget", back_populates="aop")

class AOPDetail(Base):
    __tablename__ = 'aop_detail'
    
    id = Column(Integer, primary_key=True)
    aop_id = Column(Integer, ForeignKey('aop.id'))
    cost_center_id = Column(Integer, ForeignKey('cost_center.id'))
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    aop = relationship("AOP", back_populates="details")
    cost_center = relationship("CostCenter")

class CostCenter(Base):
    __tablename__ = 'cost_center'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Employee(Base):
    __tablename__ = 'employee'
    
    id = Column(Integer, primary_key=True)
    ldap = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False)
    cost_center_id = Column(Integer, ForeignKey('cost_center.id'))
    manager_id = Column(Integer, ForeignKey('employee.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    cost_center = relationship("CostCenter")
    manager = relationship("Employee", remote_side=[id])
    reports = relationship("Employee", backref="manager_ref")

class Budget(Base):
    __tablename__ = 'budget'
    
    id = Column(Integer, primary_key=True)
    budget_id = Column(String(50), unique=True, nullable=False)
    aop_id = Column(Integer, ForeignKey('aop.id'))
    employee_id = Column(Integer, ForeignKey('employee.id'))
    project = Column(String(100), nullable=False)
    description = Column(String(255))
    amount = Column(Float, nullable=False)
    pr_amount = Column(Float, default=0.0)
    po_amount = Column(Float, default=0.0)
    receipt_amount = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    aop = relationship("AOP", back_populates="budgets")
    employee = relationship("Employee")
    purchase_requests = relationship("PurchaseRequest", back_populates="budget")
    purchase_orders = relationship("PurchaseOrder", back_populates="budget")

class PurchaseRequest(Base):
    __tablename__ = 'purchase_request'
    
    id = Column(Integer, primary_key=True)
    pr_reference = Column(String(50), unique=True, nullable=False)
    budget_id = Column(String(50), ForeignKey('budget.budget_id'))
    requestor_ldap = Column(String(50), ForeignKey('employee.ldap'))
    amount = Column(Float, nullable=False)
    request_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    budget = relationship("Budget", back_populates="purchase_requests")
    requestor = relationship("Employee", foreign_keys=[requestor_ldap])

class PurchaseOrder(Base):
    __tablename__ = 'purchase_order'
    
    id = Column(Integer, primary_key=True)
    po_number = Column(String(50), nullable=False)
    po_line_number = Column(Integer, nullable=False)
    budget_id = Column(String(50), ForeignKey('budget.budget_id'))
    requestor_ldap = Column(String(50), ForeignKey('employee.ldap'))
    purchase_item = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    order_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    budget = relationship("Budget", back_populates="purchase_orders")
    requestor = relationship("Employee", foreign_keys=[requestor_ldap])
    receipts = relationship("Receipt", back_populates="purchase_order")

class Receipt(Base):
    __tablename__ = 'receipt'
    
    id = Column(Integer, primary_key=True)
    po_number = Column(String(50), nullable=False)
    po_line_number = Column(Integer, nullable=False)
    purchase_item = Column(String(255), nullable=False)
    receipt_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    purchase_order = relationship("PurchaseOrder", 
                                foreign_keys=[po_number, po_line_number],
                                back_populates="receipts")