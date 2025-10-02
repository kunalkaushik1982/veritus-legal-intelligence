# 🚀 Veritus Deployment Guide

This guide helps you deploy the Veritus frontend to Vercel while keeping the backend running locally.

## 📋 Prerequisites

- [x] Code pushed to GitHub
- [ ] ngrok installed and configured
- [ ] Vercel CLI installed
- [ ] Backend running locally

## 🔧 Step 1: Install ngrok

### Option A: Manual Download (Recommended)
1. Go to [ngrok.com](https://ngrok.com/)
2. Sign up for free account
3. Download Windows version
4. Extract `ngrok.exe` to project folder
5. Get auth token from dashboard

### Option B: Package Manager
```powershell
# Using Chocolatey (run as Administrator)
choco install ngrok

# Using winget
winget install ngrok
```

## 🌐 Step 2: Expose Backend with ngrok

```powershell
# Authenticate ngrok (replace with your token)
ngrok config add-authtoken YOUR_AUTH_TOKEN

# Start tunnel for backend (port 8000)
ngrok http 8000
```

**Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)

## ☁️ Step 3: Deploy to Vercel

### Option A: Automated Script (Recommended)
```powershell
# Run the deployment script
.\deploy-to-vercel.ps1
```

### Option B: Manual Deployment
```powershell
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy from frontend directory
cd frontend
vercel --prod --env NEXT_PUBLIC_API_URL=https://your-ngrok-url.ngrok.io --env NEXT_PUBLIC_WS_URL=wss://your-ngrok-url.ngrok.io
```

## 🧪 Step 4: Test Multi-User Collaboration

1. **Keep ngrok running** in one terminal
2. **Keep backend running** (`docker-compose up`)
3. **Share Vercel URL** with test users
4. **Test features**:
   - Real-time text editing
   - User presence tracking
   - Live cursors and typing indicators
   - Comments system

## 🔗 URLs After Deployment

- **Frontend (Vercel)**: `https://veritus-legal-intelligence.vercel.app`
- **Backend (ngrok)**: `https://your-unique-id.ngrok.io`
- **Local Backend**: `http://localhost:8000`

## 🛠️ Troubleshooting

### CORS Issues
- Ensure ngrok URL is added to backend CORS settings
- Check that WebSocket URL uses `wss://` for HTTPS ngrok URLs

### Environment Variables
- Verify `NEXT_PUBLIC_API_URL` points to ngrok URL
- Verify `NEXT_PUBLIC_WS_URL` uses correct WebSocket protocol

### ngrok Issues
- Free ngrok URLs change on restart
- Update Vercel environment variables if ngrok URL changes
- Consider ngrok paid plan for stable URLs

## 📊 Monitoring

- **Vercel Dashboard**: Monitor deployments and logs
- **ngrok Dashboard**: Monitor tunnel traffic
- **Browser DevTools**: Check WebSocket connections

## 🔄 Updating Deployment

When you make code changes:

```powershell
# Push changes to GitHub
git add .
git commit -m "Your changes"
git push origin main

# Redeploy to Vercel
cd frontend
vercel --prod
```

## 🎯 Production Considerations

For production deployment, consider:
- **Custom domain** instead of Vercel subdomain
- **Dedicated server** instead of ngrok tunnel
- **SSL certificates** for secure WebSocket connections
- **Load balancing** for multiple backend instances
- **Database hosting** (PostgreSQL, Redis)

---

**Need help?** Check the logs in Vercel dashboard or ngrok web interface at `http://localhost:4040`
