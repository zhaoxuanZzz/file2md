"""
API路由定义
"""
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.core.config import settings
from app.core.converter import DocumentConverter
from app.models.schemas import UrlConvertRequest, ConvertResponse
from app.utils.download import download_file_from_url

router = APIRouter(tags=["转换"])


@router.get("/supported-formats")
async def get_supported_formats():
    """获取支持的文件格式列表"""
    formats = settings.SUPPORTED_EXTENSIONS.split(",")
    return {
        "formats": [fmt.strip() for fmt in formats],
        "max_file_size": settings.MAX_FILE_SIZE,
    }


@router.post("/convert/file", response_model=ConvertResponse)
async def convert_file(file: UploadFile = File(...)):
    """
    上传文件并转换为Markdown
    
    - **file**: 要转换的文件 (PDF, DOCX, PPTX, XLSX, HTML)
    """
    # 验证文件扩展名
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.SUPPORTED_EXTENSIONS.split(","):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {settings.SUPPORTED_EXTENSIONS}",
        )

    # 读取文件内容
    content = await file.read()
    
    # 验证文件大小
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({settings.MAX_FILE_SIZE / 1024 / 1024}MB)",
        )

    try:
        # 转换文档
        converter = DocumentConverter()
        markdown_content = await converter.convert_from_bytes(content, file_ext)
        
        return ConvertResponse(
            success=True,
            markdown=markdown_content,
            filename=file.filename,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"转换失败: {str(e)}",
        )


@router.post("/convert/url", response_model=ConvertResponse)
async def convert_from_url(request: UrlConvertRequest):
    """
    从URL下载文件并转换为Markdown
    
    - **url**: 文档的URL地址
    """
    try:
        # 下载文件
        file_content, filename = await download_file_from_url(request.url)
        
        # 获取文件扩展名
        file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if file_ext not in settings.SUPPORTED_EXTENSIONS.split(","):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式。支持的格式: {settings.SUPPORTED_EXTENSIONS}",
            )

        # 转换文档
        converter = DocumentConverter()
        markdown_content = await converter.convert_from_bytes(file_content, file_ext)
        
        return ConvertResponse(
            success=True,
            markdown=markdown_content,
            filename=filename,
            url=request.url,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"转换失败: {str(e)}",
        )

