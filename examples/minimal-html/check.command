#!/bin/sh
cd "$(dirname "$0")" || exit 1
command -v node >/dev/null 2>&1 || { echo "没找到 Node.js，请先安装 Node.js 20+（https://nodejs.org）"; exit 1; }
node ../../scripts/doctor.js .
echo
echo "上面的结果里出现 ✖ 就是没通过，照着提示改；全是 ✓ 就可以继续双击 start.command 了。"
