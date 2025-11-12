"""
启动脚本
兼容 Python 3.13 和 PyCharm 调试模式
"""
import asyncio
import sys

# 修复 PyCharm 调试模式下的 asyncio.run() 兼容性问题
if "_patch_asyncio" in str(asyncio.run):
    try:
        import asyncio.runners
        asyncio.run = asyncio.runners.run
    except (AttributeError, ImportError):
        pass

from uvicorn import Config, Server
from app.core.config import settings


async def main():
    """异步启动服务器"""
    config = Config(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
    server = Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止")

