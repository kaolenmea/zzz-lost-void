<#
.SYNOPSIS
    打包免安装发布包：dist\ZZZLostVoid-v<版本>.zip

.DESCRIPTION
    包里自带 Python 和依赖，不需要用户安装任何东西。目录结构：
        ZZZLostVoid\
            ZZZLostVoid.exe   启动器（要求管理员权限）
            python\           自带的 Python 3.11 和依赖
            src\ assets\ config\ plugins\
            release.json      版本号，程序据此判断自己是发布包

    config\ 只复制 git 已跟踪的文件，本机的个人配置不会被打进去。

.PARAMETER Version
    版本号，默认读 pyproject.toml 的 version。

.PARAMETER SkipZip
    只生成目录，不压缩。
#>
param(
    [string]$Version = '',
    [switch]$SkipZip
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $root

function Invoke-Checked {
    param([scriptblock]$Command, [string]$Step)
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$Step 失败，退出码 $LASTEXITCODE" }
}

if (-not $Version) {
    $Version = (uv run --no-project python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])").Trim()
}
$appName = 'ZZZLostVoid'
$distDir = Join-Path $root 'dist'
$pkgDir = Join-Path $distDir $appName
$tmpDir = Join-Path $distDir '_build'
Write-Host "打包版本 v$Version -> $pkgDir"

if (Test-Path $pkgDir) { Remove-Item $pkgDir -Recurse -Force }
if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
New-Item -ItemType Directory -Force $pkgDir, $tmpDir | Out-Null

# 1. 复制 uv 管理的独立 Python（可以整个目录搬走）
Invoke-Checked { uv python install 3.11 } '安装 Python'
$pyBase = Get-ChildItem (uv python dir) -Directory -Filter 'cpython-3.11*' | Select-Object -First 1
if (-not $pyBase) { throw '找不到 uv 管理的 Python 3.11' }
Copy-Item $pyBase.FullName (Join-Path $pkgDir 'python') -Recurse
$pkgPython = Join-Path $pkgDir 'python\python.exe'

# 2. 按 uv.lock 安装运行依赖（不含 dev 组）
$requirements = Join-Path $tmpDir 'requirements.txt'
Invoke-Checked { uv export --frozen --no-dev --no-hashes --no-emit-project -o $requirements } '导出依赖'
Invoke-Checked {
    uv pip install --python $pkgPython -r $requirements --link-mode copy --break-system-packages --compile-bytecode
} '安装依赖'

# 删掉用不到的 Qt 模块（浏览器内核、3D、设计器、翻译），省几百 MB
$pyside = Join-Path $pkgDir 'python\Lib\site-packages\PySide6'
foreach ($pattern in 'Qt6WebEngine*', 'QtWebEngine*', 'Qt63D*', 'Qt3D*', 'Qt6Designer*', 'QtDesigner*') {
    Get-ChildItem $pyside -Recurse -Filter $pattern -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
foreach ($dir in 'resources', 'translations') {
    Remove-Item (Join-Path $pyside $dir) -Recurse -Force -ErrorAction SilentlyContinue
}

# 3. 复制程序、资源和配置
foreach ($dir in 'src', 'assets', 'plugins') {
    robocopy (Join-Path $root $dir) (Join-Path $pkgDir $dir) /E /XD __pycache__ /XF '*.pyc' /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "复制 $dir 失败，robocopy 退出码 $LASTEXITCODE" }
}
# 个人背景图不打进包
foreach ($file in 'version_poster.webp', 'static_background.webp', 'dynamic_background.webm') {
    Remove-Item (Join-Path $pkgDir "assets\ui\$file") -ErrorAction SilentlyContinue
}
# config 只复制已跟踪的文件，避免带上本机的个人配置
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
foreach ($file in (git -c core.quotepath=false ls-files config)) {
    $target = Join-Path $pkgDir $file
    New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
    Copy-Item (Join-Path $root $file) $target
}
Copy-Item (Join-Path $root 'LICENSE') $pkgDir
Copy-Item (Join-Path $root 'README.md') $pkgDir

$commit = (git rev-parse --short HEAD).Trim()
@{ version = $Version; commit = $commit; build_time = (Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK') } |
    ConvertTo-Json | Set-Content (Join-Path $pkgDir 'release.json') -Encoding UTF8

# 4. 打包启动器 exe（要求管理员权限）
Invoke-Checked {
    uv run --no-project --with pyinstaller pyinstaller `
        --onefile --noconsole --uac-admin `
        --icon (Join-Path $root 'assets\ui\logo.ico') `
        --name $appName `
        --distpath (Join-Path $tmpDir 'launcher') `
        --workpath (Join-Path $tmpDir 'work') `
        --specpath $tmpDir `
        (Join-Path $root 'packaging\launcher\launcher.py')
} '打包启动器'
Copy-Item (Join-Path $tmpDir "launcher\$appName.exe") $pkgDir

# 5. 自检：包里的 Python 能不能导入主程序
$env:PYTHONPATH = Join-Path $pkgDir 'src'
$env:QT_QPA_PLATFORM = 'offscreen'
Invoke-Checked { & $pkgPython -I -c "import sys; sys.path.insert(0, sys.argv[1]); import zzz_lv.gui.app as a; sys.exit(1 if a._init_error else 0)" (Join-Path $pkgDir 'src') } '导入自检'
Remove-Item Env:PYTHONPATH, Env:QT_QPA_PLATFORM

# 6. 压缩
if (-not $SkipZip) {
    $zipPath = Join-Path $distDir "$appName-v$Version.zip"
    if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
    # 用 .NET 生成 zip（支持大文件）；bsdtar 在 CI 机器上处理这个目录会崩溃
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory($pkgDir, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $true)
    Write-Host ("完成: {0} ({1:N0} MB)" -f $zipPath, ((Get-Item $zipPath).Length / 1MB))
} else {
    Write-Host "完成: $pkgDir"
}
Remove-Item $tmpDir -Recurse -Force
