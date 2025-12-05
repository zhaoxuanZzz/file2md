"""
文档转换核心逻辑
使用Docling进行文档转换，支持vLLM作为推理后端
"""
import asyncio
import tempfile
import os
import time
import platform
import logging
from typing import Optional

from docling.document_converter import DocumentConverter as DoclingConverter

from app.core.config import settings

logger = logging.getLogger(__name__)


def _create_vllm_model():
    """
    创建 vLLM 模型实例
    
    Returns:
        VllmApiModel 实例，如果配置无效则返回 None
    """
    if not settings.VLLM_ENABLED:
        return None
    
    if not settings.VLLM_API_BASE or not settings.VLLM_MODEL_NAME:
        logger.warning("vLLM 已启用但配置不完整，需要设置 VLLM_API_BASE 和 VLLM_MODEL_NAME")
        return None
    
    try:
        from docling.datamodel.pipeline_options import VlmPipelineOptions
        from docling_core.types.doc.labels import DocItemLabel
        from docling.pipeline.vlm_pipeline import VlmPipeline
        
        # 尝试导入 vLLM API 模型
        try:
            from docling.models.vlm_models_api import VllmApiModel, VllmApiOptions
        except ImportError:
            logger.warning("无法导入 VllmApiModel，请确保 docling 版本支持 vLLM")
            return None
        
        # 创建 vLLM API 选项
        vllm_options = VllmApiOptions(
            api_base=settings.VLLM_API_BASE,
            model=settings.VLLM_MODEL_NAME,
            api_key=settings.VLLM_API_KEY if settings.VLLM_API_KEY else None
        )
        
        logger.info(f"vLLM 配置: API地址={settings.VLLM_API_BASE}, 模型={settings.VLLM_MODEL_NAME}")
        return vllm_options
        
    except ImportError as e:
        logger.warning(f"无法导入 vLLM 相关模块: {e}")
        return None
    except Exception as e:
        logger.error(f"创建 vLLM 模型时出错: {e}")
        return None

# 全局转换器实例（单例模式）
_global_converter: Optional['DocumentConverter'] = None


class DocumentConverter:
    """文档转换器"""
    
    def __init__(self):
        """
        初始化转换器
        
        根据配置的设备类型（CPU/GPU）初始化 Docling 转换器
        支持 vLLM 作为推理后端
        """
        device = getattr(settings, 'DOCLING_DEVICE', 'cpu')
        
        # 验证CUDA是否可用
        cuda_available = False
        if device.startswith('cuda'):
            try:
                import torch
                cuda_available = torch.cuda.is_available()
                if cuda_available:
                    logger.info(f"CUDA可用，GPU设备: {torch.cuda.get_device_name(0)}")
                else:
                    logger.warning("配置了CUDA设备，但CUDA不可用，将使用CPU")
                    device = 'cpu'
            except ImportError:
                logger.warning("PyTorch未安装，无法使用GPU，将使用CPU")
                device = 'cpu'
        
        self.device = device
        logger.info(f"初始化Docling转换器，使用设备: {device}")
        
        # 尝试多种方式配置设备
        converter_config = {}
        
        # 检查是否启用 vLLM
        vllm_options = _create_vllm_model()
        
        # 方式1: 尝试通过 pipeline_options 配置设备（推荐方式）
        try:
            from docling.datamodel.pipeline_options import PipelineOptions
            pipeline_options = PipelineOptions()
            
            # 设置设备
            if hasattr(pipeline_options, 'device'):
                pipeline_options.device = device
                logger.info(f"通过PipelineOptions设置设备: {device}")
            
            # 尝试配置OCR相关选项以充分利用GPU
            # Docling主要在OCR和表格识别中使用GPU
            if hasattr(pipeline_options, 'do_ocr') and device.startswith('cuda'):
                # 确保启用OCR以使用GPU
                pipeline_options.do_ocr = True
                logger.info("已启用OCR以充分利用GPU")
            
            # 如果启用了 vLLM，配置 VLM pipeline
            if vllm_options is not None:
                try:
                    from docling.datamodel.pipeline_options import VlmPipelineOptions
                    
                    # 创建 VLM pipeline 选项
                    vlm_pipeline_options = VlmPipelineOptions(
                        vlm_options=vllm_options
                    )
                    
                    # 设置到 pipeline_options
                    if hasattr(pipeline_options, 'vlm_pipeline_options'):
                        pipeline_options.vlm_pipeline_options = vlm_pipeline_options
                        logger.info("已配置 vLLM pipeline 选项")
                    else:
                        logger.warning("当前 docling 版本不支持 vlm_pipeline_options")
                except ImportError as e:
                    logger.warning(f"无法导入 VlmPipelineOptions: {e}")
                except Exception as e:
                    logger.warning(f"配置 vLLM pipeline 时出错: {e}")
            
            converter_config['pipeline_options'] = pipeline_options
        except (ImportError, AttributeError) as e:
            logger.debug(f"无法通过PipelineOptions配置设备: {e}")
        
        # 方式2: 尝试直接传递 device 参数
        if 'pipeline_options' not in converter_config or not converter_config.get('pipeline_options'):
            converter_config['device'] = device
            logger.info(f"直接传递device参数: {device}")
        
        # 初始化转换器
        try:
            self.converter = DoclingConverter(**converter_config)
            logger.info("Docling转换器初始化成功")
            
            # 验证实际使用的设备
            self._verify_device_usage()
        except (TypeError, ValueError) as e:
            logger.warning(f"使用参数初始化失败，尝试默认初始化: {e}")
            # 如果参数不支持，使用默认初始化
            # 某些版本的 docling 可能不支持这些参数
            self.converter = DoclingConverter()
            logger.info("使用默认配置初始化Docling转换器")
    
    def _verify_device_usage(self):
        """验证转换器实际使用的设备"""
        try:
            # 尝试检查转换器内部使用的设备
            if hasattr(self.converter, 'pipeline') and hasattr(self.converter.pipeline, 'device'):
                actual_device = str(self.converter.pipeline.device)
                logger.info(f"转换器实际使用的设备: {actual_device}")
            elif hasattr(self.converter, '_device'):
                actual_device = str(self.converter._device)
                logger.info(f"转换器实际使用的设备: {actual_device}")
            else:
                logger.debug("无法确定转换器实际使用的设备")
        except Exception as e:
            logger.debug(f"验证设备使用情况时出错: {e}")
    
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


def get_converter() -> DocumentConverter:
    """
    获取全局转换器实例（单例模式）
    
    第一次调用时会初始化转换器，后续调用返回同一个实例
    这样可以避免每次请求都重新初始化，提高性能
    
    Returns:
        DocumentConverter实例
    """
    global _global_converter
    if _global_converter is None:
        _global_converter = DocumentConverter()
    return _global_converter

