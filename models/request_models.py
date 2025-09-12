from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Модели для запросов, которые не вошли в другие файлы

class HealthCheckResponse(BaseModel):
    status: str
    database: str
    timestamp: str
    error: Optional[str] = None

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None

class SuccessResponse(BaseModel):
    message: str
    status: str = "success"

class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 50

class SearchRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class BulkOperationResponse(BaseModel):
    success_count: int
    failed_count: int
    errors: Optional[List[str]] = None