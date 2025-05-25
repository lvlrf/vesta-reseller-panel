# backend/app/services/initial_data.py
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash, generate_id
from app.models.user import User, UserRole
from app.models.agent import Agent
from app.models.credit import Credit
from app.models.setting import Setting
from app.models.product_group import ProductGroup
from app.models.product import Product, ProductType, DurationType

def create_initial_data():
    """Create initial data for the application"""
    db = SessionLocal()
    
    try:
        # Create Super Admin if not exists
        admin_mobile = settings.FIRST_SUPERADMIN_MOBILE
        admin_password = settings.FIRST_SUPERADMIN_PASSWORD
        
        existing_admin = db.query(User).filter(User.mobile == admin_mobile).first()
        if not existing_admin:
            admin_id = generate_id("USR")
            admin = User(
                id=admin_id,
                username=admin_mobile,
                mobile=admin_mobile,
                hashed_password=get_password_hash(admin_password),
                first_name="مدیر",
                last_name="سیستم",
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(admin)
            print(f"Created Super Admin: {admin_mobile}")
        
        # Create default settings
        default_settings = [
            {
                "key": "site_name",
                "value": "VestaResellerPanel",
                "description": "نام سایت",
                "category": "general"
            },
            {
                "key": "card_to_card_info",
                "value": "شماره کارت: 1234-5678-9012-3456\nبانک: ملی\nنام صاحب کارت: شرکت وستا",
                "description": "اطلاعات کارت به کارت",
                "category": "payment"
            },
            {
                "key": "default_commission_rate",
                "value": "10",
                "description": "درصد کمیسیون پیش‌فرض",
                "category": "business"
            },
            {
                "key": "telegram_notifications",
                "value": "true",
                "description": "فعال‌سازی اعلان‌های تلگرام",
                "category": "notification"
            }
        ]
        
        for setting_data in default_settings:
            existing_setting = db.query(Setting).filter(Setting.key == setting_data["key"]).first()
            if not existing_setting:
                setting_id = generate_id("SET")
                setting = Setting(
                    id=setting_id,
                    **setting_data
                )
                db.add(setting)
                print(f"Created setting: {setting_data['key']}")
        
        # Create default product group
        existing_group = db.query(ProductGroup).first()
        if not existing_group:
            group_id = generate_id("PGP")
            product_group = ProductGroup(
                id=group_id,
                name="دست راست",
                description="محصولات برنامه دست راست"
            )
            db.add(product_group)
            
            # Create default product
            product_id = generate_id("PRD")
            product = Product(
                id=product_id,
                name="اشتراک دست راست - ماهانه",
                description="اشتراک یک ماهه برنامه دست راست",
                product_type=ProductType.API_BASED,
                group_id=group_id,
                price=100000,  # 100,000 تومان
                commission_rate=40,  # 40% کمیسیون
                duration_type=DurationType.MONTHS,
                duration_value=1,
                is_active=True,
                has_test_option=True,
                test_duration=3  # 3 روز تست
            )
            db.add(product)
            print("Created default product group and product")
        
        db.commit()
        print("Initial data creation completed successfully")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating initial data: {e}")
        raise e
    finally:
        db.close()
