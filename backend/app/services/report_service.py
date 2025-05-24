pythonfrom typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import io
import pandas as pd

from sqlalchemy.orm import Session
from sqlalchemy import func, text
from fastapi import HTTPException, status

from app.models.subscription import Subscription, SubscriptionStatus
from app.models.product import Product
from app.models.agent import Agent
from app.models.user import User
from app.models.credit import Credit
from app.models.transaction import Transaction, TransactionType
from app.models.payment import Payment, PaymentStatus


class ReportService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_admin_dashboard_data(self) -> Dict[str, Any]:
        """Get dashboard data for admin"""
        # Total agents count
        agents_count = self.db.query(func.count(Agent.id)).scalar()
        
        # Active agents count (users that are active)
        active_agents_count = self.db.query(func.count(Agent.id)).join(
            User, Agent.user_id == User.id
        ).filter(User.is_active == True).scalar()
        
        # Total products count
        products_count = self.db.query(func.count(Product.id)).scalar()
        
        # Active products count
        active_products_count = self.db.query(func.count(Product.id)).filter(
            Product.is_active == True
        ).scalar()
        
        # Total subscriptions count
        subscriptions_count = self.db.query(func.count(Subscription.id)).scalar()
        
        # Active subscriptions count
        active_subscriptions_count = self.db.query(func.count(Subscription.id)).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).scalar()
        
        # Pending payments count
        pending_payments_count = self.db.query(func.count(Payment.id)).filter(
            Payment.status == PaymentStatus.PENDING
        ).scalar()
        
        # Total sales amount (from active subscriptions)
        total_sales = self.db.query(func.sum(Subscription.price)).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).scalar() or 0
        
        # Recent subscriptions
        recent_subscriptions = self.db.query(Subscription).order_by(
            Subscription.created_at.desc()
        ).limit(5).all()
        
        # Recent payments
        recent_payments = self.db.query(Payment).order_by(
            Payment.created_at.desc()
        ).limit(5).all()
        
        # Monthly sales (last 6 months)
        monthly_sales = []
        now = datetime.now()
        for i in range(5, -1, -1):
            month_start = datetime(now.year, now.month, 1) - timedelta(days=30*i)
            month_end = datetime(now.year, now.month, 1) - timedelta(days=30*(i-1)) if i > 0 else now
            
            month_sales = self.db.query(func.sum(Subscription.price)).filter(
                Subscription.created_at >= month_start,
                Subscription.created_at < month_end
            ).scalar() or 0
            
            monthly_sales.append({
                "month": month_start.strftime("%Y-%m"),
                "sales": float(month_sales)
            })
        
        # Return dashboard data
        return {
            "agents": {
                "total": agents_count,
                "active": active_agents_count
            },
            "products": {
                "total": products_count,
                "active": active_products_count
            },
            "subscriptions": {
                "total": subscriptions_count,
                "active": active_subscriptions_count
            },
            "payments": {
                "pending": pending_payments_count
            },
            "sales": {
                "total": float(total_sales),
                "monthly": monthly_sales
            },
            "recent_subscriptions": [
                {
                    "id": sub.id,
                    "product_name": sub.product.name,
                    "customer_name": sub.customer_name,
                    "agent_name": f"{sub.agent.user.first_name} {sub.agent.user.last_name}",
                    "price": sub.price,
                    "status": sub.status.value,
                    "created_at": sub.created_at.isoformat()
                }
                for sub in recent_subscriptions
            ],
            "recent_payments": [
                {
                    "id": payment.id,
                    "user_name": f"{payment.user.first_name} {payment.user.last_name}",
                    "amount": payment.amount,
                    "status": payment.status.value,
                    "method": payment.method.value,
                    "created_at": payment.created_at.isoformat()
                }
                for payment in recent_payments
            ]
        }
    
    def get_agent_dashboard_data(self, agent_id: str) -> Dict[str, Any]:
        """Get dashboard data for a specific agent"""
        # Check if agent exists
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError("Agent not found")
        
        # Agent credit balance
        credit = self.db.query(Credit).filter(Credit.agent_id == agent_id).first()
        credit_balance = credit.balance if credit else 0
        
        # Total subscriptions count
        subscriptions_count = self.db.query(func.count(Subscription.id)).filter(
            Subscription.agent_id == agent_id
        ).scalar()
        
        # Active subscriptions count
        active_subscriptions_count = self.db.query(func.count(Subscription.id)).filter(
            Subscription.agent_id == agent_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).scalar()
        
        # Expiring subscriptions (next 7 days)
        now = datetime.now()
        week_later = now + timedelta(days=7)
        expiring_subscriptions_count = self.db.query(func.count(Subscription.id)).filter(
            Subscription.agent_id == agent_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
            Subscription.end_date.isnot(None),
            Subscription.end_date > now,
            Subscription.end_date <= week_later
        ).scalar()
        
        # Total sales amount
        total_sales = self.db.query(func.sum(Subscription.price)).filter(
            Subscription.agent_id == agent_id
        ).scalar() or 0
        
        # Recent subscriptions
        recent_subscriptions = self.db.query(Subscription).filter(
            Subscription.agent_id == agent_id
        ).order_by(
            Subscription.created_at.desc()
        ).limit(5).all()
        
        # Recent transactions
        recent_transactions = []
        if credit:
            recent_transactions = self.db.query(Transaction).filter(
                Transaction.credit_id == credit.id
            ).order_by(
                Transaction.created_at.desc()
            ).limit(5).all()
        
        # Monthly sales (last 6 months)
        monthly_sales = []
        for i in range(5, -1, -1):
            month_start = datetime(now.year, now.month, 1) - timedelta(days=30*i)
            month_end = datetime(now.year, now.month, 1) - timedelta(days=30*(i-1)) if i > 0 else now
            
            month_sales = self.db.query(func.sum(Subscription.price)).filter(
                Subscription.agent_id == agent_id,
                Subscription.created_at >= month_start,
                Subscription.created_at < month_end
            ).scalar() or 0
            
            monthly_sales.append({
                "month": month_start.strftime("%Y-%m"),
                "sales": float(month_sales)
            })
        
        # Return dashboard data
        return {
            "agent": {
                "id": agent.id,
                "name": f"{agent.user.first_name} {agent.user.last_name}",
                "credit_balance": float(credit_balance)
            },
            "subscriptions": {
                "total": subscriptions_count,
                "active": active_subscriptions_count,
                "expiring_soon": expiring_subscriptions_count
            },
            "sales": {
                "total": float(total_sales),
                "monthly": monthly_sales
            },
            "recent_subscriptions": [
                {
                    "id": sub.id,
                    "product_name": sub.product.name,
                    "customer_name": sub.customer_name,
                    "price": sub.price,
                    "status": sub.status.value,
                    "created_at": sub.created_at.isoformat()
                }
                for sub in recent_subscriptions
            ],
            "recent_transactions": [
                {
                    "id": trans.id,
                    "type": trans.type.value,
                    "amount": trans.amount,
                    "balance_after": trans.balance_after,
                    "description": trans.description,
                    "created_at": trans.created_at.isoformat()
                }
                for trans in recent_transactions
            ]
        }
    
    def get_sales_report(
        self, 
        start_date: datetime, 
        end_date: datetime,
        agent_id: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sales report for a specific period"""
        # Base query
        query = self.db.query(Subscription)
        
        # Apply filters
        query = query.filter(
            Subscription.created_at >= start_date,
            Subscription.created_at <= end_date
        )
        
        if agent_id:
            query = query.filter(Subscription.agent_id == agent_id)
        
        if product_id:
            query = query.filter(Subscription.product_id == product_id)
        
        # Get subscriptions
        subscriptions = query.all()
        
        # Calculate totals
        total_count = len(subscriptions)
        total_amount = sum(sub.price for sub in subscriptions)
        
        # Group by product
        product_sales = {}
        for sub in subscriptions:
            product_id = sub.product_id
            product_name = sub.product.name
            
            if product_id not in product_sales:
                product_sales[product_id] = {
                    "product_id": product_id,
                    "product_name": product_name,
                    "count": 0,
                    "amount": 0
                }
            
            product_sales[product_id]["count"] += 1
            product_sales[product_id]["amount"] += sub.price
        
        # Group by agent
        agent_sales = {}
        for sub in subscriptions:
            agent_id = sub.agent_id
            agent_name = f"{sub.agent.user.first_name} {sub.agent.user.last_name}"
            
            if agent_id not in agent_sales:
                agent_sales[agent_id] = {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "count": 0,
                    "amount": 0
                }
            
            agent_sales[agent_id]["count"] += 1
            agent_sales[agent_id]["amount"] += sub.price
        
        # Group by day
        daily_sales = {}
        for sub in subscriptions:
            day = sub.created_at.date().isoformat()
            
            if day not in daily_sales:
                daily_sales[day] = {
                    "day": day,
                    "count": 0,
                    "amount": 0
                }
            
            daily_sales[day]["count"] += 1
            daily_sales[day]["amount"] += sub.price
        
        # Return report data
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "totals": {
                "count": total_count,
                "amount": float(total_amount)
            },
            "by_product": list(product_sales.values()),
            "by_agent": list(agent_sales.values()),
            "by_day": list(daily_sales.values())
        }
    
    def get_financial_report(
        self, 
        start_date: datetime, 
        end_date: datetime,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get financial report for a specific period"""
        # Credit transactions query
        transactions_query = self.db.query(Transaction).join(
            Credit, Transaction.credit_id == Credit.id
        ).filter(
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        )
        
        # Payments query
        payments_query = self.db.query(Payment).filter(
            Payment.created_at >= start_date,
            Payment.created_at <= end_date
        )
        
        # Apply agent filter if provided
        if agent_id:
            transactions_query = transactions_query.filter(Credit.agent_id == agent_id)
            
            # Get agent's user ID
            agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                payments_query = payments_query.filter(Payment.user_id == agent.user_id)
        
        # Get transactions and payments
        transactions = transactions_query.all()
        payments = payments_query.all()
        
        # Calculate transaction totals
        deposits = sum(t.amount for t in transactions if t.type == TransactionType.DEPOSIT)
        withdrawals = sum(abs(t.amount) for t in transactions if t.type == TransactionType.WITHDRAWAL)
        
        # Calculate payment totals
        completed_payments = sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED)
        pending_payments = sum(p.amount for p in payments if p.status == PaymentStatus.PENDING)
        rejected_payments = sum(p.amount for p in payments if p.status == PaymentStatus.REJECTED)
        
        # Group transactions by day
        daily_transactions = {}
        for trans in transactions:
            day = trans.created_at.date().isoformat()
            
            if day not in daily_transactions:
                daily_transactions[day] = {
                    "day": day,
                    "deposits": 0,
                    "withdrawals": 0
                }
            
            if trans.type == TransactionType.DEPOSIT:
                daily_transactions[day]["deposits"] += trans.amount
            else:  # WITHDRAWAL
                daily_transactions[day]["withdrawals"] += abs(trans.amount)
        
        # Group payments by day
        daily_payments = {}
        for payment in payments:
            day = payment.created_at.date().isoformat()
            
            if day not in daily_payments:
                daily_payments[day] = {
                    "day": day,
                    "completed": 0,
                    "pending": 0,
                    "rejected": 0
                }
            
            if payment.status == PaymentStatus.COMPLETED:
                daily_payments[day]["completed"] += payment.amount
            elif payment.status == PaymentStatus.PENDING:
                daily_payments[day]["pending"] += payment.amount
            else:  # REJECTED
                daily_payments[day]["rejected"] += payment.amount
        
        # Return report data
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "transactions": {
                "deposits": float(deposits),
                "withdrawals": float(withdrawals),
                "net": float(deposits - withdrawals)
            },
            "payments": {
                "completed": float(completed_payments),
                "pending": float(pending_payments),
                "rejected": float(rejected_payments)
            },
            "by_day": {
                "transactions": list(daily_transactions.values()),
                "payments": list(daily_payments.values())
            }
        }
    
    def export_sales_report(
        self, 
        start_date: datetime, 
        end_date: datetime,
        agent_id: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> bytes:
        """Export sales report as Excel file"""
        # Get report data
        report_data = self.get_sales_report(
            start_date=start_date,
            end_date=end_date,
            agent_id=agent_id,
            product_id=product_id
        )
        
        # Create Excel writer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_data = {
                'Metric': ['Start Date', 'End Date', 'Total Count', 'Total Amount'],
                'Value': [
                    report_data['period']['start_date'],
                    report_data['period']['end_date'],
                    report_data['totals']['count'],
                    report_data['totals']['amount']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # By Product sheet
            if report_data['by_product']:
                product_df = pd.DataFrame(report_data['by_product'])
                product_df.to_excel(writer, sheet_name='By Product', index=False)
            
            # By Agent sheet
            if report_data['by_agent']:
                agent_df = pd.DataFrame(report_data['by_agent'])
                agent_df.to_excel(writer, sheet_name='By Agent', index=False)
            
            # By Day sheet
            if report_data['by_day']:
                day_df = pd.DataFrame(report_data['by_day'])
                day_df.to_excel(writer, sheet_name='By Day', index=False)
        
        # Return Excel file
        output.seek(0)
        return output.getvalue()
    
    def export_financial_report(
        self, 
        start_date: datetime, 
        end_date: datetime,
        agent_id: Optional[str] = None
    ) -> bytes:
        """Export financial report as Excel file"""
        # Get report data
        report_data = self.get_financial_report(
            start_date=start_date,
            end_date=end_date,
            agent_id=agent_id
        )
        
        # Create Excel writer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Start Date', 'End Date',
                    'Total Deposits', 'Total Withdrawals', 'Net Transactions',
                    'Completed Payments', 'Pending Payments', 'Rejected Payments'
                ],
                'Value': [
                    report_data['period']['start_date'],
                    report_data['period']['end_date'],
                    report_data['transactions']['deposits'],
                    report_data['transactions']['withdrawals'],
                    report_data['transactions']['net'],
                    report_data['payments']['completed'],
                    report_data['payments']['pending'],
                    report_data['payments']['rejected']
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Daily Transactions sheet
            if report_data['by_day']['transactions']:
                transactions_df = pd.DataFrame(report_data['by_day']['transactions'])
                transactions_df.to_excel(writer, sheet_name='Daily Transactions', index=False)
            
            # Daily Payments sheet
            if report_data['by_day']['payments']:
                payments_df = pd.DataFrame(report_data['by_day']['payments'])
                payments_df.to_excel(writer, sheet_name='Daily Payments', index=False)
        
        # Return Excel file
        output.seek(0)
        return output.getvalue()