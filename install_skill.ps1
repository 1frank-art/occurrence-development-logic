# 安装/更新 occurrence-development-logic skill（PowerShell）
# 用法1（推荐：先 cd 到你的项目根目录再运行，装进当前目录的 .dsh\skills）：
#   cd "D:\你的项目目录"; powershell -ExecutionPolicy Bypass -File "...\install_skill.ps1"
# 用法2（显式指定项目根）：powershell -ExecutionPolicy Bypass -File install_skill.ps1 -ProjectRoot "D:\你的项目目录"
param([string]$ProjectRoot = (Get-Location).Path)
$ErrorActionPreference = "Stop"
$dst = Join-Path $ProjectRoot ".dsh\skills\occurrence-development-logic"
New-Item -ItemType Directory -Path $dst -Force | Out-Null
Copy-Item (Join-Path $PSScriptRoot "SKILL.md") (Join-Path $dst "SKILL.md") -Force
Write-Host "已安装 skill 到：$dst" -ForegroundColor Green
Write-Host "验证：新开会话后输入 /occurrence-development-logic 或说「请加载 occurrence-development-logic skill」" -ForegroundColor Cyan
Write-Host "确认生效特征：回答先判交互类别、事实回答带 判断/来源/边界、首次会话输出出入对照表（仅一次）" -ForegroundColor Cyan
