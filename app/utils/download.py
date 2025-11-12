"""
URL下载工具
"""
import asyncio
import aiohttp
from pathlib import Path
from urllib.parse import urlparse
from typing import Tuple

from app.core.config import settings


async def download_file_from_url(url: str) -> Tuple[bytes, str]:
    """
    从URL下载文件
    
    Args:
        url: 文件URL地址
        
    Returns:
        (文件内容字节, 文件名)的元组
        
    Raises:
        HTTPException: 下载失败时抛出
    """
    timeout = aiohttp.ClientTimeout(total=settings.DOWNLOAD_TIMEOUT)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(url) as response:
                # 检查HTTP状态
                if response.status != 200:
                    raise Exception(f"下载失败，HTTP状态码: {response.status}")
                
                # 检查Content-Length
                content_length = response.headers.get("Content-Length")
                if content_length and int(content_length) > settings.MAX_DOWNLOAD_SIZE:
                    raise Exception(
                        f"文件大小超过限制 ({settings.MAX_DOWNLOAD_SIZE / 1024 / 1024}MB)"
                    )
                
                # 读取内容（限制大小）
                content = b""
                async for chunk in response.content.iter_chunked(8192):
                    content += chunk
                    if len(content) > settings.MAX_DOWNLOAD_SIZE:
                        raise Exception(
                            f"文件大小超过限制 ({settings.MAX_DOWNLOAD_SIZE / 1024 / 1024}MB)"
                        )
                
                # 从URL或Content-Disposition获取文件名
                filename = _extract_filename(url, response.headers)
                
                return content, filename
                
        except aiohttp.ClientError as e:
            raise Exception(f"下载失败: {str(e)}")
        except asyncio.TimeoutError:
            raise Exception(f"下载超时（超过{settings.DOWNLOAD_TIMEOUT}秒）")


def _extract_filename(url: str, headers: dict) -> str:
    """
    从URL或响应头提取文件名
    
    Args:
        url: 文件URL
        headers: HTTP响应头
        
    Returns:
        文件名
    """
    # 尝试从Content-Disposition获取文件名
    content_disposition = headers.get("Content-Disposition", "")
    if "filename=" in content_disposition:
        filename = content_disposition.split("filename=")[1].strip('"\'')
        if filename:
            return filename
    
    # 从URL路径提取文件名
    parsed_url = urlparse(url)
    path = Path(parsed_url.path)
    if path.name:
        return path.name
    
    # 默认文件名
    return "document"

