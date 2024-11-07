@echo off

rem pyinstallerでPythonファイルをexe化
pyinstaller --onefile --icon=icon.ico --noconsole --clean main.py

rem main.exe をカレントディレクトリに移動
move dist\main.exe main.exe

rem デスクトップパスを取得（OneDrive上のデスクトップも考慮）
set desktopPath=%UserProfile%\Desktop

rem ショートカットのパスと対象の exe パス
set shortcutPath="%desktopPath%\Swimmy Python Manager.lnk"
set targetPath="%cd%\main.exe"

rem ショートカット作成
powershell -command "$wshShell = New-Object -ComObject WScript.Shell; $shortcut = $wshShell.CreateShortcut('%shortcutPath%'); $shortcut.TargetPath = '%targetPath%'; $shortcut.WorkingDirectory = '%cd%'; $shortcut.Save();"

pause
