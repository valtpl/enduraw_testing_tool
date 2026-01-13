# Build Script pour Enduraw Testing Tool
# Génère l'exécutable Windows avec PyInstaller

Write-Host "=== Build Enduraw Testing Tool ===" -ForegroundColor Cyan

# Vérifier que PyInstaller est installé
try {
    python -m PyInstaller --version | Out-Null
} catch {
    Write-Host "PyInstaller n'est pas installé. Installation..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Nettoyer les anciens builds
Write-Host "Nettoyage des anciens builds..." -ForegroundColor Yellow
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item *.spec -ErrorAction SilentlyContinue

# Builder l'application
Write-Host "Build de l'application..." -ForegroundColor Green
$iconPath = if (Test-Path "icon.ico") { "--icon=icon.ico" } else { "" }

pyinstaller --onefile `
    --windowed `
    --name "Enduraw_Testing_Tool" `
    --add-data "src;src" `
    $iconPath `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild terminé avec succès !" -ForegroundColor Green
    Write-Host "Exécutable disponible dans: dist\Enduraw_Testing_Tool.exe" -ForegroundColor Cyan
} else {
    Write-Host "`nErreur lors du build !" -ForegroundColor Red
    exit 1
}
