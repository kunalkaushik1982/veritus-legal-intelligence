# 🐳 Veritus - Complete Container Setup

This document describes the comprehensive container setup for the Veritus application, including all services, management scripts, and deployment options.

## 📋 Overview

The Veritus application is containerized using Docker Compose with the following services:

- **Frontend**: Next.js React application (Port 3000)
- **Backend**: FastAPI Python application (Port 8000)
- **Database**: PostgreSQL 15 (Port 5432)
- **Cache**: Redis 7 Alpine (Port 6379)
- **Proxy**: Nginx (Port 80/443) - Optional
- **Admin Tools**: pgAdmin, Redis Commander - Optional

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

**Windows PowerShell:**
```powershell
.\start-all-containers.ps1
```

**Linux/macOS:**
```bash
chmod +x start-all-containers.sh
./start-all-containers.sh
```

### Option 2: Manual Setup

```bash
# Start core services
docker-compose -f docker-compose.full.yml up -d postgres redis

# Wait for database
sleep 10

# Start backend
docker-compose -f docker-compose.full.yml up -d backend

# Wait for backend
sleep 15

# Start frontend
docker-compose -f docker-compose.full.yml up -d frontend
```

## 🛠️ Container Management

Use the management script for easy container operations:

```powershell
# Start all containers
.\manage-containers.ps1 -Action start -Service all

# Start specific service
.\manage-containers.ps1 -Action start -Service frontend

# Stop all containers
.\manage-containers.ps1 -Action stop -Service all

# Restart backend
.\manage-containers.ps1 -Action restart -Service backend

# View status
.\manage-containers.ps1 -Action status

# View logs
.\manage-containers.ps1 -Action logs -Service backend

# Open shell
.\manage-containers.ps1 -Action shell -Service backend

# Clean everything
.\manage-containers.ps1 -Action clean

# Build containers
.\manage-containers.ps1 -Action build -Service all

# Backup data
.\manage-containers.ps1 -Action backup

# Restore data
.\manage-containers.ps1 -Action restore
```

## 🌐 Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main application |
| Backend API | http://localhost:8000 | API endpoints |
| Database | localhost:5432 | PostgreSQL |
| Redis | localhost:6379 | Cache |
| pgAdmin | http://localhost:5050 | Database admin |
| Redis Commander | http://localhost:8081 | Redis admin |
| Nginx | http://localhost:80 | Reverse proxy |

## 📁 File Structure

```
veritus/
├── docker-compose.full.yml      # Complete container setup
├── start-all-containers.ps1     # Windows startup script
├── start-all-containers.sh      # Linux/macOS startup script
├── manage-containers.ps1        # Container management script
├── nginx/
│   └── nginx.conf              # Nginx configuration
├── logs/                       # Application logs
└── backups/                    # Database backups
```

## 🔧 Configuration

### Environment Variables

The containers use the following environment variables:

**Backend:**
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `CORS_ORIGINS`: Allowed CORS origins
- `DEBUG`: Debug mode (True/False)

**Frontend:**
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_APP_URL`: Frontend application URL

### Ports

| Service | Internal Port | External Port | Protocol |
|---------|---------------|---------------|----------|
| Frontend | 3000 | 3000 | HTTP |
| Backend | 8000 | 8000 | HTTP |
| PostgreSQL | 5432 | 5432 | TCP |
| Redis | 6379 | 6379 | TCP |
| Nginx | 80 | 80 | HTTP |
| Nginx | 443 | 443 | HTTPS |
| pgAdmin | 80 | 5050 | HTTP |
| Redis Commander | 8081 | 8081 | HTTP |

## 🎯 Profiles

The setup supports different profiles for different use cases:

### Development Profile
```bash
docker-compose -f docker-compose.full.yml up -d
```

### Production Profile (with Nginx)
```bash
docker-compose -f docker-compose.full.yml --profile production up -d
```

### Admin Profile (with admin tools)
```bash
docker-compose -f docker-compose.full.yml --profile admin up -d
```

### Full Profile (everything)
```bash
docker-compose -f docker-compose.full.yml --profile production --profile admin up -d
```

## 🔒 Security Features

- **Rate Limiting**: API and web requests are rate limited
- **CORS**: Proper CORS configuration
- **Security Headers**: X-Frame-Options, X-Content-Type-Options, etc.
- **SSL Support**: HTTPS configuration with SSL certificates
- **Network Isolation**: Custom Docker network

## 📊 Monitoring

### Health Checks

All services include health checks:

```bash
# Check health status
docker-compose -f docker-compose.full.yml ps

# View health check logs
docker-compose -f docker-compose.full.yml logs | grep health
```

### Logs

```bash
# View all logs
docker-compose -f docker-compose.full.yml logs -f

# View specific service logs
docker-compose -f docker-compose.full.yml logs -f backend

# View last 100 lines
docker-compose -f docker-compose.full.yml logs --tail=100
```

## 💾 Data Persistence

### Volumes

- `postgres_data`: Database data
- `redis_data`: Cache data
- `pgadmin_data`: pgAdmin configuration

### Backups

```bash
# Create backup
.\manage-containers.ps1 -Action backup

# Restore backup
.\manage-containers.ps1 -Action restore
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -an | findstr ":3000"
   
   # Stop conflicting services
   net stop <service-name>
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   icacls . /grant Everyone:F /T
   ```

3. **Container Won't Start**
   ```bash
   # Check logs
   docker-compose -f docker-compose.full.yml logs <service>
   
   # Rebuild container
   docker-compose -f docker-compose.full.yml build --no-cache <service>
   ```

4. **Database Connection Issues**
   ```bash
   # Check database status
   docker-compose -f docker-compose.full.yml exec postgres pg_isready -U veritus_user
   
   # Reset database
   docker-compose -f docker-compose.full.yml down -v
   docker-compose -f docker-compose.full.yml up -d postgres
   ```

### Reset Everything

```bash
# Stop and remove everything
docker-compose -f docker-compose.full.yml down --volumes --remove-orphans

# Remove all images
docker rmi $(docker images -q)

# Clean system
docker system prune -af

# Start fresh
.\start-all-containers.ps1
```

## 🔄 Updates

### Update Containers

```bash
# Pull latest images
docker-compose -f docker-compose.full.yml pull

# Rebuild and restart
docker-compose -f docker-compose.full.yml up -d --build
```

### Update Application Code

```bash
# Code changes are automatically reflected due to volume mounting
# No need to rebuild containers for code changes
```

## 📈 Performance

### Optimization Tips

1. **Resource Limits**: Set appropriate memory and CPU limits
2. **Caching**: Use Redis for session and data caching
3. **Database**: Optimize PostgreSQL configuration
4. **Nginx**: Enable gzip compression and static file caching

### Scaling

```bash
# Scale frontend instances
docker-compose -f docker-compose.full.yml up -d --scale frontend=3

# Scale backend instances
docker-compose -f docker-compose.full.yml up -d --scale backend=2
```

## 🆘 Support

For issues and support:

1. Check the logs: `docker-compose -f docker-compose.full.yml logs`
2. Verify container status: `docker-compose -f docker-compose.full.yml ps`
3. Check health checks: `docker inspect <container-name>`
4. Review this documentation

## 📝 Notes

- All containers are configured for development with hot reloading
- Volume mounting enables real-time code changes
- Health checks ensure services are ready before dependencies start
- Network isolation provides security and organization
- Backup and restore functionality protects your data
