pythonfrom typing import Any, List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin, get_current_super_admin
from app.models.user import User
from app.schemas.setting import SettingCreate, SettingResponse, SettingUpdate
from app.services.setting_service import SettingService

router = APIRouter()

@router.get("/", response_model=List[SettingResponse])
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Retrieve all settings.
    """
    setting_service = SettingService(db)
    settings = setting_service.get_settings()
    return settings

@router.post("/", response_model=SettingResponse)
def create_setting(
    setting_in: SettingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
) -> Any:
    """
    Create a new setting.
    """
    setting_service = SettingService(db)
    setting = setting_service.create_setting(setting_in)
    return setting

@router.get("/{key}", response_model=SettingResponse)
def get_setting(
    key: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Get a setting by key.
    """
    setting_service = SettingService(db)
    setting = setting_service.get_setting_by_key(key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found",
        )
    return setting

@router.put("/{key}", response_model=SettingResponse)
def update_setting(
    key: str,
    setting_in: SettingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
) -> Any:
    """
    Update a setting.
    """
    setting_service = SettingService(db)
    setting = setting_service.get_setting_by_key(key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found",
        )
    
    setting = setting_service.update_setting(key, setting_in)
    return setting

@router.get("/category/{category}", response_model=Dict[str, str])
def get_settings_by_category(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
) -> Any:
    """
    Get settings by category.
    """
    setting_service = SettingService(db)
    settings_dict = setting_service.get_settings_by_category(category)
    return settings_dict

@router.put("/bulk-update")
def bulk_update_settings(
    settings: Dict[str, str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin)
) -> Any:
    """
    Update multiple settings at once.
    """
    setting_service = SettingService(db)
    updated = setting_service.bulk_update_settings(settings)
    return {"updated": updated}