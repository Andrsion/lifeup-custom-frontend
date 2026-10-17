@echo off
cd /d "%~dp0"
where node >nul 2>nul || ( echo [x] 没找到 Node.js，请先安装 Node.js 20+ ^( https://nodejs.org ^) & pause & exit /b )
node ..\..\scripts\doctor.js .
echo.
echo 上面的结果里出现 ✖ 就是没通过，照着提示改；全是 ✓ 就可以继续双击 start.bat 了。
pause
