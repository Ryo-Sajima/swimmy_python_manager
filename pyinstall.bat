@echo off

rem pyinstaller��Python�t�@�C����exe��
pyinstaller --onefile --icon=icon.ico --noconsole --clean main.py

rem main.exe ���J�����g�f�B���N�g���Ɉړ�
move dist\main.exe main.exe

rem �f�X�N�g�b�v�p�X���擾�iOneDrive��̃f�X�N�g�b�v���l���j
set desktopPath=%UserProfile%\Desktop

rem �V���[�g�J�b�g�̃p�X�ƑΏۂ� exe �p�X
set shortcutPath="%desktopPath%\Swimmy Python Manager.lnk"
set targetPath="%cd%\main.exe"

rem �V���[�g�J�b�g�쐬
powershell -command "$wshShell = New-Object -ComObject WScript.Shell; $shortcut = $wshShell.CreateShortcut('%shortcutPath%'); $shortcut.TargetPath = '%targetPath%'; $shortcut.WorkingDirectory = '%cd%'; $shortcut.Save();"

pause
