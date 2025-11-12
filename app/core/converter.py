"""
文档转换核心逻辑
使用Docling进行文档转换
"""
import asyncio
import tempfile
import os
import time
import platform

from docling.document_converter import DocumentConverter as DoclingConverter

from app.core.config import settings


class DocumentConverter:
    """文档转换器"""
    
    def __init__(self):
        """
        初始化转换器
        
        根据配置的设备类型（CPU/GPU）初始化 Docling 转换器
        """
        device = getattr(settings, 'DOCLING_DEVICE', 'cpu')
        
        # 尝试多种方式配置设备
        converter_config = {}
        
        # 方式1: 尝试通过 pipeline_options 配置设备
        try:
            from docling.datamodel.pipeline_options import PipelineOptions
            pipeline_options = PipelineOptions()
            if hasattr(pipeline_options, 'device'):
                pipeline_options.device = device
            converter_config['pipeline_options'] = pipeline_options
        except (ImportError, AttributeError):
            pass
        
        # 方式2: 尝试直接传递 device 参数
        if 'pipeline_options' not in converter_config:
            converter_config['device'] = device
        
        # 初始化转换器
        try:
            self.converter = DoclingConverter(**converter_config)
        except (TypeError, ValueError):
            # 如果参数不支持，使用默认初始化
            # 某些版本的 docling 可能不支持这些参数
            self.converter = DoclingConverter()
    
    async def convert_from_bytes(
        self, 
        content: bytes, 
        file_ext: str
    ) -> str:
        """
        从字节内容转换文档为Markdown
        
        Args:
            content: 文件字节内容
            file_ext: 文件扩展名（如 .pdf, .docx）
            
        Returns:
            Markdown格式的字符串
        """
        # 在事件循环中运行同步的转换操作
        loop = asyncio.get_event_loop()
        
        # 创建临时文件
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                suffix=file_ext,
                delete=False,
                dir=settings.TEMP_DIR
            ) as tmp_file:
                # 写入临时文件
                tmp_file.write(content)
                tmp_file.flush()
                tmp_path = tmp_file.name
            
            # 确保文件句柄已关闭后再进行转换
            # 使用Docling转换
            result = await loop.run_in_executor(
                None,
                self._convert_file,
                tmp_path
            )
            
            return result
        finally:
            # 清理临时文件（在转换完成后）
            if tmp_path and os.path.exists(tmp_path):
                self._safe_delete_file(tmp_path)
    
    def _convert_file(self, file_path: str) -> str:
        """
        同步转换文件（在executor中运行）
        
        Args:
            file_path: 文件路径
            
        Returns:
            Markdown格式的字符串
        """
        # 使用Docling转换文档
        result = self.converter.convert(file_path)
        
        # 获取Markdown内容
        markdown_content = result.document.export_to_markdown()
        
        # 确保转换结果已完全处理，释放文件句柄
        # 在 Windows 上，需要等待文件句柄完全释放
        if platform.system() == 'Windows':
            time.sleep(0.1)  # 短暂等待，确保文件句柄释放
        
        return markdown_content
    
    def _safe_delete_file(self, file_path: str, max_retries: int = 5, retry_delay: float = 0.1):
        """
        安全删除文件，处理 Windows 文件锁定问题
        
        Args:
            file_path: 要删除的文件路径
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        if not os.path.exists(file_path):
            return
        
        for attempt in range(max_retries):
            try:
                os.unlink(file_path)
                return  # 删除成功
            except (OSError, PermissionError) as e:
                if attempt < max_retries - 1:
                    # 等待后重试
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    # 最后一次尝试失败，记录但不抛出异常
                    # 在 Windows 上，文件可能被其他进程占用，这是可以接受的
                    if platform.system() == 'Windows':
                        # Windows 上文件可能被系统索引服务等占用，忽略错误
                        pass
                    else:
                        # 非 Windows 系统，记录错误
                        import logging
                        logging.warning(f"无法删除临时文件 {file_path}: {e}")
    
    async def convert_from_path(self, file_path: str) -> str:
        """
        从文件路径转换文档为Markdown
        
        Args:
            file_path: 文件路径
            
        Returns:
            Markdown格式的字符串
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._convert_file,
            file_path
        )
        return result

