# PowerShell script to restart server and clear cache

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "RESTART SERVER AND CLEAR CACHE" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan

# Step 1: Clear Python bytecode cache
Write-Host ""
Write-Host "Step 1: Clearing Python bytecode cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Directory -Filter "__pycache__" -Recurse | Remove-Item -Recurse -Force
Get-ChildItem -Path . -File -Filter "*.pyc" -Recurse | Remove-Item -Force
Write-Host "✅ Cache cleared" -ForegroundColor Green

# Step 2: Instructions for server restart (requires SSH to Linux server)
Write-Host ""
Write-Host "Step 2: Server restart required on Linux server..." -ForegroundColor Yellow
Write-Host "⚠️  You need to SSH into your Linux server and run:" -ForegroundColor Yellow
Write-Host ""
Write-Host "    sudo systemctl restart gunicorn" -ForegroundColor White
Write-Host "    sudo systemctl restart nginx" -ForegroundColor White
Write-Host ""

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "CACHE CLEAR COMPLETE" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. SSH into your Linux server (iwnd349@ipanel2)" -ForegroundColor White
Write-Host "2. Run: sudo systemctl restart gunicorn" -ForegroundColor White
Write-Host "3. Run: sudo systemctl restart nginx" -ForegroundColor White
Write-Host "4. Clear your browser cache (Ctrl+Shift+Delete)" -ForegroundColor White
Write-Host "5. Try registering with a 055 or 057 number" -ForegroundColor White
Write-Host "6. If still not working, try in an incognito/private window" -ForegroundColor White
Write-Host ""
Write-Host "=======================================================================" -ForegroundColor Cyan
