"""
FastAPI应用主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import routes
from app.core.config import settings
from app.core.converter import get_converter

# 配置日志
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于Docling的文档转Markdown服务",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(routes.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """应用启动时预初始化转换器"""
    logger.info("正在初始化文档转换器...")
    
    # 检查GPU状态
    try:
        from app.utils.gpu_diagnostic import check_cuda_availability, diagnose_gpu_low_usage
        cuda_info = check_cuda_availability()
        if cuda_info["cuda_available"]:
            logger.info(f"检测到GPU: {cuda_info.get('gpu_name', 'Unknown')}")
        else:
            logger.info("未检测到可用的GPU")
        
        # 诊断GPU配置
        device = getattr(settings, 'DOCLING_DEVICE', 'cpu')
        diagnosis = diagnose_gpu_low_usage(device)
        if diagnosis["issues"]:
            logger.warning("GPU配置问题:")
            for issue in diagnosis["issues"]:
                logger.warning(f"  - {issue}")
            logger.info("建议:")
            for suggestion in diagnosis["suggestions"]:
                logger.info(f"  - {suggestion}")
    except Exception as e:
        logger.debug(f"GPU诊断失败: {e}")
    
    try:
        # 预初始化转换器，避免第一次请求时的延迟
        converter = get_converter()
        logger.info("文档转换器初始化完成")
    except Exception as e:
        logger.error(f"转换器初始化失败: {e}", exc_info=True)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/api/v1/gpu-info")
async def get_gpu_info():
    """获取GPU信息和诊断结果"""
    try:
        from app.utils.gpu_diagnostic import get_gpu_usage_info, diagnose_gpu_low_usage
        
        device = getattr(settings, 'DOCLING_DEVICE', 'cpu')
        usage_info = get_gpu_usage_info()
        diagnosis = diagnose_gpu_low_usage(device)
        
        return {
            "gpu_usage": usage_info,
            "diagnosis": diagnosis,
            "configured_device": device
        }
    except Exception as e:
        logger.error(f"获取GPU信息失败: {e}", exc_info=True)
        return {
            "error": str(e),
            "configured_device": getattr(settings, 'DOCLING_DEVICE', 'cpu')
        }

