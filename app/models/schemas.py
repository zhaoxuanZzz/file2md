"""
Pydantic数据模型
"""
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


class UrlConvertRequest(BaseModel):
    """URL转换请求模型"""
    url: HttpUrl = Field(..., description="要转换的文档URL地址")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/document.pdf"
            }
        }


class ConvertResponse(BaseModel):
    """转换响应模型"""
    success: bool = Field(..., description="转换是否成功")
    markdown: str = Field(..., description="转换后的Markdown内容")
    filename: Optional[str] = Field(None, description="文件名")
    url: Optional[str] = Field(None, description="源URL（如果从URL转换）")
    error: Optional[str] = Field(None, description="错误信息（如果转换失败）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "markdown": "# 文档标题\n\n文档内容...",
                "filename": "document.pdf"
            }
        }

