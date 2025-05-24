pythonfrom typing import List, Dict, Optional, Any
from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import generate_id
from app.models.setting import Setting
from app.schemas.setting import SettingCreate, SettingUpdate


class SettingService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_settings(self) -> List[Setting]:
        """Get all settings"""
        return self.db.query(Setting).all()
    
    def get_setting_by_key(self, key: str) -> Optional[Setting]:
        """Get setting by key"""
        return self.db.query(Setting).filter(Setting.key == key).first()
    
    def create_setting(self, setting_in: SettingCreate) -> Setting:
        """Create a new setting"""
        # Check if setting key already exists
        existing_setting = self.get_setting_by_key(setting_in.key)
        if existing_setting:
            raise ValueError(f"Setting with key '{setting_in.key}' already exists")
        
        # Create setting
        setting_id = generate_id("SET")
        setting = Setting(
            id=setting_id,
            key=setting_in.key,
            value=setting_in.value,
            description=setting_in.description,
            category=setting_in.category
        )
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        
        return setting
    
    def update_setting(self, key: str, setting_in: SettingUpdate) -> Optional[Setting]:
        """Update a setting"""
        setting = self.get_setting_by_key(key)
        if not setting:
            return None
        
        # Update setting fields
        setting.value = setting_in.value
        
        if setting_in.description is not None:
            setting.description = setting_in.description
        
        if setting_in.category is not None:
            setting.category = setting_in.category
        
        self.db.commit()
        self.db.refresh(setting)
        
        return setting
    
    def get_settings_by_category(self, category: str) -> Dict[str, str]:
        """Get settings by category as a dictionary"""
        settings = self.db.query(Setting).filter(Setting.category == category).all()
        
        # Convert to dictionary
        settings_dict = {}
        for setting in settings:
            settings_dict[setting.key] = setting.value
        
        return settings_dict
    
    def bulk_update_settings(self, settings_dict: Dict[str, str]) -> int:
        """Update multiple settings at once"""
        updated_count = 0
        
        for key, value in settings_dict.items():
            setting = self.get_setting_by_key(key)
            if setting:
                setting.value = value
                updated_count += 1
        
        self.db.commit()
        return updated_count