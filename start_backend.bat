@echo off
chcp 65001 >nul
echo ========================================
echo   代码转论文智能体 - 后端启动
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] 检查虚拟环境...
if not exist "backend\.venv\Scripts\python.exe" (
    echo 错误: 虚拟环境不存在，请先创建虚拟环境
    pause
    exit /b 1
)
echo 虚拟环境已就绪
echo.

echo [2/3] 检查配置文件...
if not exist ".env" (
    echo 警告: .env 文件不存在，正在从 .env.example 复制...
    if exist "backend\.env.example" (
        copy "backend\.env.example" ".env"
        echo 请编辑 .env 文件配置数据库和 API 密钥
    ) else (
        echo 错误: .env.example 也不存在
        pause
        exit /b 1
    )
)
echo 配置文件已就绪
echo.

echo [3/3] 启动后端服务...
echo.
echo 服务地址: http://localhost:7348
echo API文档: http://localhost:7348/docs
echo 按 Ctrl+C 停止服务
echo.
echo ========================================
echo.

cd /d "%~dp0backend"
.venv\Scripts\python.exe main.py

pause

