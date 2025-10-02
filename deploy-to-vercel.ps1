# Veritus Vercel Deployment Script
# This script helps deploy the frontend to Vercel with proper environment variables

Write-Host "🚀 Veritus Vercel Deployment Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Check if Vercel CLI is installed
try {
    $vercelVersion = vercel --version
    Write-Host "✅ Vercel CLI found: $vercelVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Vercel CLI not found. Installing..." -ForegroundColor Red
    npm install -g vercel
}

# Get ngrok URL from user
Write-Host "`n🔗 Please provide your ngrok URL:" -ForegroundColor Yellow
Write-Host "   Example: https://abc123.ngrok.io" -ForegroundColor Gray
$ngrokUrl = Read-Host "Enter your ngrok URL"

if (-not $ngrokUrl) {
    Write-Host "❌ ngrok URL is required for deployment!" -ForegroundColor Red
    exit 1
}

# Validate URL format
if ($ngrokUrl -notmatch "^https?://.*\.ngrok\.io$") {
    Write-Host "⚠️  Warning: URL doesn't look like a typical ngrok URL" -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y" -and $continue -ne "Y") {
        exit 1
    }
}

# Create WebSocket URL
$wsUrl = $ngrokUrl -replace "^https://", "wss://" -replace "^http://", "ws://"

Write-Host "`n📝 Configuration:" -ForegroundColor Yellow
Write-Host "   API URL: $ngrokUrl" -ForegroundColor White
Write-Host "   WebSocket URL: $wsUrl" -ForegroundColor White

# Change to frontend directory
Set-Location frontend

# Deploy to Vercel
Write-Host "`n🚀 Deploying to Vercel..." -ForegroundColor Cyan
Write-Host "   Setting environment variables..." -ForegroundColor Gray

# Set environment variables and deploy
vercel --prod `
    --env NEXT_PUBLIC_API_URL=$ngrokUrl `
    --env NEXT_PUBLIC_WS_URL=$wsUrl `
    --env NEXT_PUBLIC_ENV=production

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Deployment successful!" -ForegroundColor Green
    Write-Host "`n🌐 Your app should be available at:" -ForegroundColor Cyan
    Write-Host "   https://veritus-legal-intelligence.vercel.app" -ForegroundColor White
    
    Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Keep your ngrok tunnel running: .\ngrok.exe http 8000" -ForegroundColor White
    Write-Host "   2. Share the Vercel URL with test users" -ForegroundColor White
    Write-Host "   3. Test real-time collaboration!" -ForegroundColor White
} else {
    Write-Host "`n❌ Deployment failed!" -ForegroundColor Red
    Write-Host "   Please check the error messages above." -ForegroundColor Gray
}

# Return to root directory
Set-Location ..

Write-Host "`n🎯 Deployment script completed!" -ForegroundColor Cyan
