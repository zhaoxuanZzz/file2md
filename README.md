# File2MD 文档转换服务

基于 FastAPI 和 Docling 的文档转换服务，支持将多种文档格式（PDF, DOCX, PPTX, XLSX, HTML）转换为 Markdown 格式，并支持从 URL 直接转换。

## 项目概述

File2MD 是一个高性能的文档转换服务，使用 IBM 的 Docling 库作为核心转换引擎，提供 RESTful API 接口，支持文件上传和 URL 下载两种方式将文档转换为 Markdown 格式。

## 技术栈

- **Python**: 3.13
- **Web框架**: FastAPI
- **核心转换工具**: Docling (IBM 的文档处理库)
- **异步支持**: asyncio, aiohttp (用于URL下载)
- **依赖管理**: pip/poetry

## 环境配置

### Conda 虚拟环境使用说明

#### 环境信息
- **环境名称**: file2md
- **Python版本**: 3.13.9
- **环境路径**: `C:\Users\50424\.conda\envs\file2md`

#### 激活环境

在Windows PowerShell或命令提示符中运行：

```bash
conda activate file2md
```

#### 安装项目依赖

激活环境后，安装项目依赖：

```bash
pip install -r requirements.txt
```

#### 验证安装

检查Python版本：
```bash
python --version
```

应该显示：`Python 3.13.9`

#### 退出环境

```bash
conda deactivate
```

#### 删除环境（如果需要）

```bash
conda env remove -n file2md
```

## 项目结构

```
file2md/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用入口
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API路由
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理
│   │   └── converter.py     # 文档转换核心逻辑
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic数据模型
│   └── utils/
│       ├── __init__.py
│       └── download.py      # URL下载工具
├── tests/
│   ├── __init__.py
│   └── test_converter.py
├── requirements.txt
├── .env.example
├── .gitignore
├── run.py                   # 启动脚本
└── README.md
```

## 核心功能设计

### 1. API端点设计
- `POST /api/v1/convert/file` - 上传文件转换
- `POST /api/v1/convert/url` - 从URL转换
- `GET /health` - 健康检查
- `GET /api/v1/supported-formats` - 获取支持的格式列表

### 2. 转换流程
1. **文件上传/URL下载**
   - 接收文件或URL
   - 验证文件格式和大小
   - 如果是URL，先下载到临时目录

2. **文档转换**
   - 使用Docling加载文档
   - 转换为Markdown格式
   - 处理转换错误

3. **结果返回**
   - 返回Markdown文本
   - 或返回错误信息

### 3. 支持的文件格式
- PDF (.pdf)
- Word文档 (.docx)
- PowerPoint (.pptx)
- Excel (.xlsx)
- HTML (.html, .htm)

### 4. 配置项
- 最大文件大小限制（默认100MB）
- 临时文件存储路径
- 请求超时时间
- URL下载超时时间（默认30秒）
- 支持的文件扩展名列表
- Docling设备配置（CPU/CUDA）

## 安装和运行

### 1. 创建并激活虚拟环境

```bash
conda activate file2md
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

### 4. 运行服务

使用启动脚本：
```bash
python run.py
```

或使用 uvicorn 直接运行：
```bash
uvicorn app.main:app --reload
```

服务将在 `http://localhost:8000` 启动。

### 5. 访问API文档

启动服务后，可以访问以下地址查看API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API 使用示例

### 文件上传转换

```bash
curl -X POST "http://localhost:8000/api/v1/convert/file" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### URL转换

```bash
curl -X POST "http://localhost:8000/api/v1/convert/url" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/document.pdf"}'
```

### 健康检查

```bash
curl -X GET "http://localhost:8000/health"
```

### 获取支持的格式

```bash
curl -X GET "http://localhost:8000/api/v1/supported-formats"
```

## 配置说明

主要配置项在 `app/core/config.py` 中定义，可以通过环境变量或 `.env` 文件进行配置：

- `APP_NAME`: 应用名称（默认: File2MD）
- `APP_VERSION`: 应用版本（默认: 1.0.0）
- `DEBUG`: 调试模式（默认: False）
- `HOST`: 服务器地址（默认: 0.0.0.0）
- `PORT`: 服务器端口（默认: 8000）
- `MAX_FILE_SIZE`: 最大文件大小，单位字节（默认: 104857600，即100MB）
- `UPLOAD_DIR`: 上传文件目录（默认: ./tmp/uploads）
- `TEMP_DIR`: 临时文件目录（默认: ./tmp/temp）
- `DOWNLOAD_TIMEOUT`: URL下载超时时间，单位秒（默认: 30）
- `MAX_DOWNLOAD_SIZE`: 最大下载大小，单位字节（默认: 104857600，即100MB）
- `SUPPORTED_EXTENSIONS`: 支持的文件扩展名，逗号分隔（默认: .pdf,.docx,.pptx,.xlsx,.html,.htm）
- `LOG_LEVEL`: 日志级别（默认: INFO）
- `LOG_FILE`: 日志文件路径（默认: ./logs/app.log）
- `DOCLING_DEVICE`: Docling设备类型，'cpu' 或 'cuda'（默认: cpu）

## 实现要点

### Docling使用
- 使用 `docling.document_converter.DocumentConverter` 进行转换
- 配置转换选项（保留格式、图片处理等）
- 错误处理和日志记录

### 异步处理
- 使用FastAPI的异步特性
- URL下载使用aiohttp异步下载
- 文件I/O使用异步操作

### 错误处理
- 文件格式验证
- 文件大小限制
- 转换失败处理
- URL下载失败处理
- 超时处理

### 安全性
- 文件类型验证
- 文件大小限制
- URL白名单（可选）
- 临时文件自动清理

## 主要依赖包

- fastapi - Web框架
- uvicorn[standard] - ASGI服务器
- docling - 文档转换核心库
- python-multipart - 文件上传支持
- aiohttp - 异步HTTP客户端（URL下载）
- pydantic - 数据验证
- python-dotenv - 环境变量管理

完整依赖列表请查看 `requirements.txt`。

## 开发计划

1. ✅ 项目结构初始化
2. ⬜ 核心转换功能实现
3. ⬜ API端点实现
4. ⬜ URL下载功能
5. ⬜ 错误处理和日志
6. ⬜ 测试用例编写
7. ⬜ 文档完善

## 许可证

[待添加]

## 贡献

欢迎提交 Issue 和 Pull Request！
