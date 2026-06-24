# ============================================================================
#  build.ps1 - Construye el ejecutable del agente ELEKA Marketplace.
#
#  Crea un entorno virtual, instala dependencias + PyInstaller y empaqueta
#  agent.py como un unico .exe (--onefile) llamado ElekaMarketplaceAgent,
#  incluyendo los modulos reutilizados del repo (src/modules) como datos.
#
#  Uso (desde la carpeta agent/):
#     powershell -ExecutionPolicy Bypass -File .\build.ps1
#
#  Salida: agent\dist\ElekaMarketplaceAgent.exe
# ============================================================================

$ErrorActionPreference = "Stop"

# Rutas (este script vive en <repo>/agent).
$AgentDir = $PSScriptRoot
$RepoRoot = Split-Path -Parent $AgentDir
$SrcDir   = Join-Path $RepoRoot "src"
$VenvDir  = Join-Path $AgentDir ".venv"

Write-Host "ELEKA Marketplace - build del agente"
Write-Host "  Repo: $RepoRoot"
Write-Host "  Src : $SrcDir"

# 1) Resolver interprete de Python.
$PyExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PyExe = "py -3"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PyExe = "python"
} else {
    throw "No se encontro Python (py -3 / python). Instala Python 3.x."
}
Write-Host "  Python: $PyExe"

# 2) Crear venv si no existe.
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creando entorno virtual..."
    Invoke-Expression "$PyExe -m venv `"$VenvDir`""
}

$VenvPy = Join-Path $VenvDir "Scripts\python.exe"

# 3) Instalar dependencias + PyInstaller.
Write-Host "Instalando dependencias..."
& $VenvPy -m pip install --upgrade pip
& $VenvPy -m pip install -r (Join-Path $AgentDir "requirements.txt")
& $VenvPy -m pip install pyinstaller

# 4) Empaquetar.
#    --add-data usa ';' como separador en Windows (origen;destino_en_bundle).
#    Incluimos src/modules y src/config (settings.py es importado por algun modulo).
Write-Host "Empaquetando con PyInstaller..."
Push-Location $AgentDir
try {
    & $VenvPy -m PyInstaller `
        --onefile `
        --name ElekaMarketplaceAgent `
        --add-data "$SrcDir\modules;src\modules" `
        --add-data "$SrcDir\config;src\config" `
        --hidden-import selenium `
        --hidden-import webdriver_manager `
        --hidden-import pyotp `
        --hidden-import websockets `
        --hidden-import requests `
        --hidden-import PIL `
        (Join-Path $AgentDir "agent.py")
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Listo. Ejecutable en: $(Join-Path $AgentDir 'dist\ElekaMarketplaceAgent.exe')"
