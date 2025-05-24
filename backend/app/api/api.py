pythonfrom fastapi import APIRouter

from app.api.endpoints import (
    auth,
    agents,
    agent_groups,
    products,
    product_groups,
    subscriptions,
    credits,
    payments,
    reports,
    notifications,
    settings
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(agent_groups.router, prefix="/agent-groups", tags=["agent-groups"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(product_groups.router, prefix="/product-groups", tags=["product-groups"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(credits.router, prefix="/credits", tags=["credits"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])