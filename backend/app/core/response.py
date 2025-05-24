# backend/app/core/response.py
from typing import Any, Optional, List, Dict
from pydantic import BaseModel

class ApiResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    meta: Optional[Dict[str, Any]] = None

class PaginatedResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None
    data: List[Any]
    meta: Dict[str, Any]

def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(message: str = "Error", error_code: str = "ERROR") -> Dict[str, Any]:
    return {
        "success": False,
        "message": message,
        "error_code": error_code
    }

def paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    per_page: int = 10,
    message: str = "Success"
) -> Dict[str, Any]:
    return {
        "success": True,
        "message": message,
        "data": items,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
            "has_next": page * per_page < total,
            "has_prev": page > 1
        }
    }
