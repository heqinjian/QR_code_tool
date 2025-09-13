@echo off
setlocal enabledelayedexpansion

REM 设置Python版本和下载URL
set PYTHON_VERSION=3.11.9
set PYTHON_INSTALLER=python-%PYTHON_VERSION%-amd64.exe
set PYTHON_URL=https://www.python.org/ftp/python/%PYTHON_VERSION%/%PYTHON_INSTALLER%

REM 检查Python是否已安装
echo 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo 已检测到Python环境。
    goto :install_dependencies
)

REM 未安装Python，开始自动安装过程
echo 未检测到Python环境，正在开始自动安装...

echo 正在下载Python %PYTHON_VERSION%安装程序，请稍候...
REM 使用PowerShell下载Python安装程序
powershell -Command "Invoke-WebRequest -Uri %PYTHON_URL% -OutFile %PYTHON_INSTALLER%"

if not exist %PYTHON_INSTALLER% (
    echo 错误：Python安装程序下载失败。请检查网络连接并重试。
    pause
    exit /b 1
)

echo Python安装程序下载成功，正在安装Python，请稍候...
REM 静默安装Python（/quiet表示静默安装，/passive表示显示进度但无需用户交互）
REM /install表示安装模式，/norestart表示不自动重启
REM Include_doc=0表示不安装文档，Include_pip=1表示安装pip
%PYTHON_INSTALLER% /passive InstallAllUsers=1 PrependPath=1 Include_pip=1

if %errorlevel% neq 0 (
    echo 错误：Python安装失败。请手动安装Python后再次运行此脚本。
    pause
    exit /b 1
)

REM 删除安装程序
del %PYTHON_INSTALLER%

echo Python安装成功！

REM 刷新PATH环境变量，使新安装的Python可用
echo 正在配置环境变量...
call "%windir%\System32\refreshenv.cmd" >nul 2>&1
REM 如果refreshenv不可用，尝试直接设置路径
setshell=cmd.exe
start "" /b "%shell%" /c "exit"

:install_dependencies
REM 安装依赖包
echo 正在安装所需的依赖包，请稍候...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo 警告：部分依赖包安装可能失败。正在尝试使用国内镜像源重新安装...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    
    if %errorlevel% neq 0 (
        echo 错误：依赖包安装失败。请检查网络连接或手动安装依赖包。
        echo 手动安装命令：pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM 运行程序
echo 依赖包安装成功，正在启动二维码识别程序...
python 1.py

REM 程序结束后等待用户按键
echo 程序已结束。
pause