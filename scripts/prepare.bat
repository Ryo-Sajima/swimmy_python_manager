@echo off
setlocal

:: Python 3.13がインストールされているか確認
where python3.13 | findstr "python3.13.exe"
if %errorlevel% neq 0 (
    echo Python 3.13 がインストールされていません。
    echo Python 3.13 をインストールしてください。
    echo.
    pause >nul
    exit /b
)

:: pip をアップグレード
python -m pip install -U pip

:: wheel と setuptools をインストール
pip install wheel setuptools

:: requirements.txt に記載されているライブラリをインストール
pip install -r ..\requirements.txt

echo 任意のキーを押して終了します...
pause >nul