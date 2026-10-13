@echo off
cd /d "%~dp0"
if not exist config.json (
  copy config.example.json config.json >nul
  echo [!] 已生成 config.json —— 请先用记事本打开，把 host 改成你手机的 IP:13276，保存后重新运行。
  pause
  exit /b
)
where node >nul 2>nul || ( echo [x] 没找到 Node.js，请先安装 Node.js 20+ ^( https://nodejs.org ^) & pause & exit /b )
node proxy.js
pause
