@echo off
setlocal

:: Python 3.13���C���X�g�[������Ă��邩�m�F
where python3.13 | findstr "python3.13.exe"
if %errorlevel% neq 0 (
    echo Python 3.13 ���C���X�g�[������Ă��܂���B
    echo Python 3.13 ���C���X�g�[�����Ă��������B
    echo.
    pause >nul
    exit /b
)

:: pip ���A�b�v�O���[�h
python -m pip install -U pip

:: wheel �� setuptools ���C���X�g�[��
pip install wheel setuptools

:: requirements.txt �ɋL�ڂ���Ă��郉�C�u�������C���X�g�[��
pip install -r ..\requirements.txt

echo �C�ӂ̃L�[�������ďI�����܂�...
pause >nul