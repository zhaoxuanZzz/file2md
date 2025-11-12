"""
应用配置管理
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    APP_NAME: str = "Doc2MD"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 104857600  # 100MB
    UPLOAD_DIR: str = "./tmp/uploads"
    TEMP_DIR: str = "./tmp/temp"
    
    # URL下载配置
    DOWNLOAD_TIMEOUT: int = 30  # 秒
    MAX_DOWNLOAD_SIZE: int = 104857600  # 100MB
    
    # 支持的文件格式
    SUPPORTED_EXTENSIONS: str = ".pdf,.docx,.pptx,.xlsx,.html,.htm"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # Docling 配置
    # 设备类型: 'cpu' 或 'cuda' 或 'cuda:0' 等
    # 设置为 'cpu' 使用 CPU，设置为 'cuda' 或 'cuda:0' 使用 GPU
    DOCLING_DEVICE: str = "cpu"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()

