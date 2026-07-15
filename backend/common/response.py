# backend/schemas.py

from typing import Any
from pydantic import BaseModel

class ResponseModel(BaseModel):
    code: int = 2000
    message: str = "成功"
    data: Any = None  # 或叫 result，根据前端习惯

    class Config:
        json_schema_extra = {
            "example": {
                "code": 2000,
                "message": "操作成功",
                "data": {}
            }
        }