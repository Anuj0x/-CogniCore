# Mini AutoGPT Cleanup Script
# Removes old, outdated files after modernization

Write-Host "🧹 Cleaning up old Mini AutoGPT files..." -ForegroundColor Cyan

# Files and directories to remove
$oldItems = @(
    "mini_autogpt-main"
)

# Check and remove old items
foreach ($item in $oldItems) {
    if (Test-Path $item) {
        Write-Host "Removing: $item" -ForegroundColor Yellow
        Remove-Item -Path $item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Removed: $item" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Already clean: $item not found" -ForegroundColor Gray
    }
}

Write-Host "" -ForegroundColor Cyan
Write-Host "🎉 Cleanup complete!" -ForegroundColor Green
Write-Host "" -ForegroundColor Cyan
Write-Host "📁 Modern file structure preserved:" -ForegroundColor White
Write-Host "├── main.py                 # Modern async entry point" -ForegroundColor White
Write-Host "├── core/                   # Core system components" -ForegroundColor White
Write-Host "├── think/                  # Modern reasoning & memory" -ForegroundColor White
Write-Host "├── action/                 # Action execution system" -ForegroundColor White
Write-Host "├── llm/                    # LLM provider abstraction" -ForegroundColor White
Write-Host "├── integrations/           # Telegram & other integrations" -ForegroundColor White
Write-Host "├── assets/                 # Static assets (logo)" -ForegroundColor White
Write-Host "├── requirements.txt        # Modern dependencies" -ForegroundColor White
Write-Host "├── README.md               # Comprehensive documentation" -ForegroundColor White
Write-Host "├── .env.template           # Modern configuration template" -ForegroundColor White
Write-Host "├── .gitignore              # Updated ignore patterns" -ForegroundColor White
Write-Host "├── setup.sh                # Automated setup script" -ForegroundColor White
Write-Host "└── run.sh                  # Easy run script" -ForegroundColor White
Write-Host "" -ForegroundColor Cyan
Write-Host "🚀 Ready to run setup.sh!" -ForegroundColor Magenta
