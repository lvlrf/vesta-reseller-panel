pythonfrom typing import Any, List, Optional
import io
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse

from app.api.deps import get_db, get_current_user, get_current_admin
from app.models.user import User, UserRole
from app.services.report_service import ReportService

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get dashboard data for the current user.
    """
    report_service = ReportService(db)
    
    # Different dashboard data based on role
    if current_user.role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        # Admin dashboard data
        dashboard_data = report_service.get_admin_dashboard_data()
    else:
        # Agent dashboard data
        if not current_user.agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found for current user",
            )
        
        dashboard_data = report_service.get_agent_dashboard_data(current_user.agent.id)
    
    return dashboard_data

@router.get("/sales")
def get_sales_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agent_id: Optional[str] = None,
    product_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get sales report.
    """
    report_service = ReportService(db)
    
    # Default dates if not provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # If user is an agent, force agent_id to be the current user's agent id
    if current_user.role == UserRole.AGENT:
        if not current_user.agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found for current user",
            )
        agent_id = current_user.agent.id
    
    report_data = report_service.get_sales_report(
        start_date=start_date,
        end_date=end_date,
        agent_id=agent_id,
        product_id=product_id
    )
    
    return report_data

@router.get("/financial")
def get_financial_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get financial report.
    """
    report_service = ReportService(db)
    
    # Default dates if not provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # If user is an agent, force agent_id to be the current user's agent id
    if current_user.role == UserRole.AGENT:
        if not current_user.agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found for current user",
            )
        agent_id = current_user.agent.id
    
    report_data = report_service.get_financial_report(
        start_date=start_date,
        end_date=end_date,
        agent_id=agent_id
    )
    
    return report_data

@router.get("/export/sales")
def export_sales_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agent_id: Optional[str] = None,
    product_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Export sales report as Excel.
    """
    report_service = ReportService(db)
    
    # Default dates if not provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # If user is an agent, force agent_id to be the current user's agent id
    if current_user.role == UserRole.AGENT:
        if not current_user.agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found for current user",
            )
        agent_id = current_user.agent.id
    
    excel_bytes = report_service.export_sales_report(
        start_date=start_date,
        end_date=end_date,
        agent_id=agent_id,
        product_id=product_id
    )
    
    # Return Excel file
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=sales_report.xlsx"}
    )

@router.get("/export/financial")
def export_financial_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Export financial report as Excel.
    """
    report_service = ReportService(db)
    
    # Default dates if not provided
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # If user is an agent, force agent_id to be the current user's agent id
    if current_user.role == UserRole.AGENT:
        if not current_user.agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found for current user",
            )
        agent_id = current_user.agent.id
    
    excel_bytes = report_service.export_financial_report(
        start_date=start_date,
        end_date=end_date,
        agent_id=agent_id
    )
    
    # Return Excel file
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=financial_report.xlsx"}
    )