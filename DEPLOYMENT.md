# Mycelial Finance - Deployment Guide

**PHASE 4.2: Docker Compose Deployment**

This guide covers deploying Mycelial Finance using Docker Compose for production environments.

---

## Prerequisites

### Required Software:
- **Docker** (v20.10+): [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (v2.0+): Included with Docker Desktop

### Required Credentials:
- **Kraken API Keys**: [Generate at Kraken](https://www.kraken.com/u/security/api)
- **GitHub Personal Access Token** (optional, for Code moat): [Generate at GitHub](https://github.com/settings/tokens)

---

## Quick Start

### 1. Clone and Configure

```bash
# Navigate to project directory
cd mycelial_finance

# Copy environment template
cp .env.example .env

# Edit .env and add your credentials
nano .env  # or use your preferred editor
```

### 2. Set Environment Variables

Edit `.env` file:

```bash
# Kraken API
KRAKEN_API_KEY=your_actual_key_here
KRAKEN_API_SECRET=your_actual_secret_here

# GitHub API (optional, for real GitHub data)
GITHUB_TOKEN=your_github_token_here

# Redis (already configured for Docker)
REDIS_HOST=redis
REDIS_PORT=6379

# Application
APP_ENV=prod
```

### 3. Build and Launch

```bash
# Build images and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 4. Access Services

- **Trading Bot Logs**: `docker-compose logs -f trading-bot`
- **Dashboard**: http://localhost:8501
- **Redis**: localhost:6379

### 5. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

---

## Architecture

### Services:

1. **redis**: Message broker and cache
   - Port: 6379
   - Data persistence enabled
   - 2GB memory limit with LRU eviction

2. **trading-bot**: Main Mycelial Finance application
   - Runs model.py with all agents
   - CPU limit: 2 cores / Memory: 4GB
   - Persistent data in `./data` and `./logs`
   - SQLite database: `./mycelial_ledger.db`

3. **dashboard**: Streamlit web interface
   - Port: 8501
   - Real-time monitoring
   - CPU limit: 1 core / Memory: 2GB

4. **redis-commander** (optional): Redis web UI
   - Port: 8081
   - Only runs with `--profile debug` flag

---

## Production Deployment

### Security Best Practices:

1. **Never commit `.env` file** to version control
   ```bash
   # Verify .env is in .gitignore
   git check-ignore .env
   ```

2. **Use Docker secrets** for production credentials
   ```yaml
   # docker-compose.prod.yml
   secrets:
     kraken_api_key:
       external: true
     kraken_api_secret:
       external: true
   ```

3. **Run as non-root user** (already configured in Dockerfile)

4. **Enable firewall** and restrict ports:
   ```bash
   # Only expose dashboard publicly
   ufw allow 8501/tcp
   ufw deny 6379/tcp  # Redis internal only
   ```

### Resource Configuration:

Edit `docker-compose.yml` to adjust resource limits:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'        # Increase for more agents
      memory: 8G       # Increase for larger datasets
    reservations:
      cpus: '2'
      memory: 4G
```

### Data Persistence:

```bash
# Backup SQLite database
docker-compose exec trading-bot sqlite3 /app/mycelial_ledger.db .dump > backup.sql

# Backup Redis data
docker-compose exec redis redis-cli BGSAVE

# Restore from backup
cat backup.sql | docker-compose exec -T trading-bot sqlite3 /app/mycelial_ledger.db
```

---

## Monitoring

### View Logs:

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f trading-bot

# Last 100 lines
docker-compose logs --tail=100 trading-bot

# Follow errors only
docker-compose logs -f trading-bot | grep ERROR
```

### Health Checks:

```bash
# Check Redis health
docker-compose exec redis redis-cli ping

# Check trading bot status
docker-compose exec trading-bot python -c "from src.core.model import MycelialModel; print('OK')"

# View active agents
docker-compose exec redis redis-cli KEYS "agent:*"
```

### Performance Metrics:

```bash
# Container resource usage
docker stats

# Redis memory usage
docker-compose exec redis redis-cli INFO memory

# SQLite database size
docker-compose exec trading-bot ls -lh /app/mycelial_ledger.db
```

---

## Troubleshooting

### Issue: Redis connection failed

```bash
# Check Redis is running
docker-compose ps redis

# Check Redis logs
docker-compose logs redis

# Restart Redis
docker-compose restart redis
```

### Issue: Trading bot crashes on startup

```bash
# Check environment variables
docker-compose config

# Verify credentials
docker-compose exec trading-bot env | grep KRAKEN

# Check application logs
docker-compose logs --tail=50 trading-bot
```

### Issue: Dashboard not accessible

```bash
# Check dashboard is running
docker-compose ps dashboard

# Check port binding
netstat -an | grep 8501

# Restart dashboard
docker-compose restart dashboard
```

### Issue: Out of memory

```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
# Then recreate containers:
docker-compose up -d --force-recreate
```

---

## Advanced Configuration

### Debug Mode (with Redis Commander):

```bash
# Start with debug profile
docker-compose --profile debug up -d

# Access Redis Commander
open http://localhost:8081
```

### Development Mode (live code reload):

```yaml
# docker-compose.override.yml
services:
  trading-bot:
    volumes:
      - .:/app  # Mount entire project directory
    environment:
      - APP_ENV=dev
```

### Multi-Instance Deployment:

```bash
# Run multiple isolated instances
docker-compose -p mycelial-prod up -d
docker-compose -p mycelial-test up -d

# Each instance uses separate:
# - Network namespace
# - Volumes
# - Ports (must be remapped)
```

---

## Upgrade Process

### Zero-Downtime Upgrade:

```bash
# 1. Pull latest code
git pull origin main

# 2. Build new images (doesn't stop running containers)
docker-compose build

# 3. Recreate containers one by one
docker-compose up -d --no-deps --build trading-bot
docker-compose up -d --no-deps --build dashboard

# 4. Verify health
docker-compose ps
```

### Database Migration:

```bash
# 1. Backup database
docker-compose exec trading-bot sqlite3 /app/mycelial_ledger.db .dump > pre-upgrade-backup.sql

# 2. Stop services
docker-compose down

# 3. Apply migrations (if any)
python scripts/migrate_database.py

# 4. Start services
docker-compose up -d

# 5. Verify
docker-compose logs -f
```

---

## Uninstallation

### Remove All Services and Data:

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: DELETES ALL DATA)
docker-compose down -v

# Remove images
docker rmi mycelial_finance-trading-bot mycelial_finance-dashboard

# Clean up Docker system
docker system prune -a
```

---

## Environment-Specific Configurations

### Production (`docker-compose.prod.yml`):
```yaml
services:
  trading-bot:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Development (`docker-compose.dev.yml`):
```yaml
services:
  trading-bot:
    restart: "no"
    volumes:
      - .:/app
    environment:
      - APP_ENV=dev
```

### Usage:
```bash
# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

---

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review IMPLEMENTATION_PROGRESS.md for system status
- Consult config/agent_config.yaml for parameter tuning

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**PHASE:** 4.2 - Docker Compose Deployment
