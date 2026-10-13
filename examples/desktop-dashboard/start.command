#!/bin/bash
cd "$(dirname "$0")" || exit 1
if [ ! -f config.json ]; then
  cp config.example.json config.json
  echo "[!] 已生成 config.json —— 请先把 host 改成你手机的 IP:13276，再重新运行。"
  read -r -p "按回车退出..." _; exit 1
fi
command -v node >/dev/null 2>&1 || { echo "[x] 没找到 Node.js，请先安装 Node.js 20+（ https://nodejs.org ）"; read -r -p "按回车退出..." _; exit 1; }
node proxy.js
