@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo Cleaning old build files...
if exist build\windows rmdir /s /q build\windows
if exist dist\windows rmdir /s /q dist\windows

echo Creating necessary directories...
mkdir build\windows
mkdir dist\windows

echo Checking if app_icon.png exists...
if not exist assets\app_icon.png (
  echo Error: assets\app_icon.png does not exist!
  echo Press any key to exit...
  pause > nul
  exit /b 1
)

echo Creating Windows icon file...
if not exist assets\app_icon.ico (
  echo Using automatic conversion tool to create ICO icon...
  python src\tools\convert_icon_windows.py
  
  if not exist assets\app_icon.ico (
    echo Warning: Automatic conversion failed, manual conversion from PNG to ICO format is required
    echo Tip: You can use online tools to convert assets\app_icon.png to app_icon.ico
    echo      Then place the ico file in the assets folder
    echo Will continue packaging with default icon
  ) else (
    echo ICO icon created successfully!
  )
) else (
  echo ICO icon already exists, using it directly...
)

echo Starting Windows version packaging...
pyinstaller spotify_export.spec --distpath=dist\windows --workpath=build\windows

if %ERRORLEVEL% equ 0 (
  echo Windows version packaging completed!
  echo Program located at: dist\windows\SpotifyExportTool\SpotifyExportTool.exe
  
  echo Ensuring assets directory exists...
  if not exist dist\windows\SpotifyExportTool\assets mkdir dist\windows\SpotifyExportTool\assets
  
  echo Copying all resource files to assets directory...
  copy assets\*.* dist\windows\SpotifyExportTool\assets\
  
  echo Ensuring locale directory exists...
  if not exist dist\windows\SpotifyExportTool\locale mkdir dist\windows\SpotifyExportTool\locale
  
  echo Copying all language files to locale directory...
  copy locale\*.json dist\windows\SpotifyExportTool\locale\
  
  echo Creating installation package...
  echo Note: This script will not automatically create an installer
  echo You can use Inno Setup or other tools to create a Windows installer
  echo Or directly compress the dist\windows\SpotifyExportTool folder as a ZIP file for distribution

  echo Creating ZIP archive...
  cd dist\windows
  powershell -Command "Compress-Archive -Path 'SpotifyExportTool' -DestinationPath 'SpotifyExportTool.zip' -Force"
  cd ..\..
  
  if exist dist\windows\SpotifyExportTool.zip (
    echo ZIP archive creation completed: dist\windows\SpotifyExportTool.zip
  ) else (
    echo Failed to create ZIP archive!
  )
) else (
  echo Windows version packaging failed!
  echo See above error messages for details.
  echo Press any key to exit...
  pause > nul
  exit /b 1
)

echo Build process completed!
echo Press any key to exit...
pause > nul 