# Infrastructure Setup - Raspberry Pi 5

## Hardware Requirements

### Raspberry Pi 5 Setup
- **Model**: Raspberry Pi 5 (8GB RAM recommended, 4GB minimum)
- **Storage**: 256GB+ NVMe SSD or USB 3.0 SATA SSD (for Docker volumes & uploads)
- **SD Card**: 32GB+ microSD Class 10 (for OS boot)
- **Power**: Official 27W USB-C power supply
- **Cooling**: Active cooling case with fan (Pi 5 runs hot under load)
- **Network**: Ethernet cable (preferred) or WiFi

### External SSD Recommendation
Best options in India:
- Samsung T7 Portable SSD (500GB) - ₹5,500
- Crucial X6 Portable SSD (500GB) - ₹4,800
- Or internal SATA SSD in USB 3.0 enclosure

---

## Phase 1: Operating System Installation

### Step 1.1: Download and Flash Raspberry Pi OS

**On your Mac/development machine**:

```bash
# Download Raspberry Pi Imager
# macOS: 
brew install --cask raspberry-pi-imager

# Or download from: https://www.raspberrypi.com/software/
```

**Using Raspberry Pi Imager (Recommended)**:
1. Open Raspberry Pi Imager
2. Choose OS: **Raspberry Pi OS Lite (64-bit)** - Debian 12 Bookworm
3. Choose Storage: Your microSD card
4. Click ⚙️ (Settings) and configure:
   - **Hostname**: `attreq-pi`
   - **Enable SSH**: Yes (password authentication for now)
   - **Username**: `pi`
   - **Password**: [choose secure password]
   - **WiFi**: Configure if not using Ethernet
   - **Locale**: Asia/Kolkata, en_IN
5. Write to SD card (takes 5-10 minutes)

### Step 1.2: First Boot and SSH Access

```bash
# Insert SD card into Pi, connect Ethernet cable, power on

# Find Pi's IP address from your router
# Or scan network (replace with your network range):
nmap -sn 192.168.1.0/24 | grep -A 2 "raspberry"

# SSH into Pi (replace with actual IP)
ssh pi@192.168.1.100
# Enter password when prompted

# First thing: Update system
sudo apt update && sudo apt upgrade -y
# This takes 10-15 minutes

# Install essential tools
sudo apt install -y \
  vim \
  git \
  curl \
  wget \
  htop \
  net-tools \
  ufw \
  fail2ban \
  unattended-upgrades \
  rsync

# Set timezone
sudo timedatectl set-timezone Asia/Kolkata

# Verify
date
# Should show IST time
```

### Step 1.3: Configure External SSD Storage

```bash
# Connect your external SSD to Pi via USB 3.0 port

# List available drives
lsblk

# Expected output:
# NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
# sda           8:0    0 465.8G  0 disk          <- Your external SSD
# └─sda1        8:1    0 465.8G  0 part
# mmcblk0     179:0    0  29.7G  0 disk          <- SD card
# ├─mmcblk0p1 179:1    0   512M  0 part /boot/firmware
# └─mmcblk0p2 179:2    0  29.2G  0 part /

# Format SSD if brand new (⚠️ WARNING: This erases all data on /dev/sda)
# Skip if SSD already formatted
sudo mkfs.ext4 /dev/sda1 -L ATTREQ-Storage

# Create mount point
sudo mkdir -p /mnt/styleai

# Get UUID for persistent mounting
sudo blkid /dev/sda1
# Copy the UUID from output, example: UUID="1234abcd-5678-efgh..."

# Add to fstab for auto-mount on boot
sudo vim /etc/fstab

# Add this line at the end (replace UUID with your actual UUID):
UUID=1234abcd-5678-efgh-ijkl-mnopqrstuvwx /mnt/styleai ext4 defaults,nofail 0 2

# Save and exit (:wq in vim)

# Mount now
sudo mount -a

# Verify mounted
df -h /mnt/styleai
# Should show your SSD size and mounted at /mnt/styleai

# Set ownership to pi user
sudo chown -R pi:pi /mnt/styleai

# Create application directory structure
mkdir -p /mnt/styleai/{docker,postgres,weaviate,redis,backups,logs}
mkdir -p /mnt/styleai/uploads/{originals,processed,thumbnails}
mkdir -p /mnt/styleai/logs/{nginx,backend}

# Verify structure
tree -L 2 /mnt/styleai
```

**Estimated time**: 1 hour

---

## Phase 2: Security Hardening

### Step 2.1: Firewall Setup (UFW)

```bash
# Configure firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (port 22)
sudo ufw allow 22/tcp comment 'SSH access'

# Allow HTTP/HTTPS (for Nginx)
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Enable firewall
sudo ufw enable

# Verify status
sudo ufw status verbose

# Expected output:
# Status: active
# To                         Action      From
# --                         ------      ----
# 22/tcp                     ALLOW IN    Anywhere
# 80/tcp                     ALLOW IN    Anywhere
# 443/tcp                    ALLOW IN    Anywhere
```

### Step 2.2: SSH Hardening with Key-Based Auth

**On your Mac (development machine)**:

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "styleai-raspberry-pi" -f ~/.ssh/styleai_pi_ed25519

# Copy public key to Pi
ssh-copy-id -i ~/.ssh/styleai_pi_ed25519.pub pi@192.168.1.100
# Enter password when prompted

# Test key-based login (should not ask for password)
ssh -i ~/.ssh/styleai_pi_ed25519 pi@192.168.1.100

# Add to SSH config for convenience
vim ~/.ssh/config

# Add these lines:
Host styleai-pi
  HostName 192.168.1.100
  User pi
  IdentityFile ~/.ssh/styleai_pi_ed25519

# Now you can connect with just:
ssh styleai-pi
```

**On Raspberry Pi (disable password auth)**:

```bash
# Edit SSH config
sudo vim /etc/ssh/sshd_config

# Find and modify these lines (remove # if commented):
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
UsePAM yes

# Save and exit

# Restart SSH service
sudo systemctl restart ssh

# ⚠️ IMPORTANT: Test new connection in another terminal before closing this one!
# If it fails, you still have this session to fix it
```

### Step 2.3: Fail2Ban (Brute Force Protection)

```bash
# Install fail2ban (should already be installed)
sudo apt install -y fail2ban

# Create local jail config
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local

# Edit configuration
sudo vim /etc/fail2ban/jail.local

# Find [sshd] section and modify:
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600

# Save and exit

# Enable and start fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Check status
sudo fail2ban-client status sshd
```

**Estimated time**: 30 minutes

---

## Phase 3: Docker Installation

### Step 3.1: Install Docker Engine

```bash
# Download Docker installation script
curl -fsSL https://get.docker.com -o get-docker.sh

# Review script (optional but recommended)
cat get-docker.sh

# Run installation
sudo sh get-docker.sh

# Add pi user to docker group (no need for sudo)
sudo usermod -aG docker pi

# Apply group changes (logout and login again)
exit

# SSH back in
ssh styleai-pi

# Verify Docker installation
docker --version
# Expected: Docker version 24.0.x or higher

# Test Docker
docker run hello-world
# Should download and run successfully
```

### Step 3.2: Install Docker Compose

```bash
# Docker Compose V2 comes with Docker now
docker compose version
# Expected: Docker Compose version v2.23.x or higher

# If not available, install manually:
sudo apt install -y docker-compose-plugin

# Verify
docker compose version
```

### Step 3.3: Move Docker Data to External SSD

```bash
# Stop Docker
sudo systemctl stop docker

# Create Docker daemon config
sudo mkdir -p /etc/docker
sudo vim /etc/docker/daemon.json

# Add this content:
{
  "data-root": "/mnt/styleai/docker",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}

# Save and exit

# Create directory
sudo mkdir -p /mnt/styleai/docker

# Copy existing Docker data (if any)
sudo rsync -aP /var/lib/docker/ /mnt/styleai/docker/

# Start Docker
sudo systemctl start docker

# Verify new data location
docker info | grep "Docker Root Dir"
# Should show: /mnt/styleai/docker

# Test with a container
docker run --rm alpine echo "Docker works on SSD!"
```

**Estimated time**: 30 minutes

---

## Phase 4: Project Repository Setup

### Step 4.1: Create Project Structure

```bash
# Create projects directory
mkdir -p ~/projects
cd ~/projects

# Clone your repository (or create new one)
# If you haven't created GitHub repo yet:
mkdir styleai
cd styleai

# Initialize git
git init
git branch -M main

# Create directory structure
mkdir -p backend frontend nginx scripts

# Create basic .gitignore
cat > .gitignore << 'EOF'
# Environment
.env
.env.local

# Dependencies
node_modules/
venv/
__pycache__/

# Build outputs
.next/
dist/
build/

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp

# Docker
docker-compose.override.yml
EOF
```

### Step 4.2: Environment Variables Setup

```bash
# Create environment template
cat > .env.example << 'EOF'
# === Application ===
APP_NAME=StyleAI
APP_ENV=production
APP_DEBUG=false

# === Database ===
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=styleai
POSTGRES_USER=styleai_user
POSTGRES_PASSWORD=CHANGE_ME

# === Weaviate ===
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
WEAVIATE_SCHEME=http

# === Redis ===
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_ME

# === JWT Authentication ===
JWT_SECRET_KEY=CHANGE_ME
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# === File Storage ===
UPLOAD_DIR=/mnt/styleai/uploads
MAX_UPLOAD_SIZE_MB=10

# === External APIs ===
ROBOFLOW_API_KEY=CHANGE_ME
ROBOFLOW_MODEL_ID=clothing-detection-ev04d/4
ROBOFLOW_PROJECT=main-project-qsu9x

OPENWEATHER_API_KEY=CHANGE_ME

# === Google OAuth (Optional) ===
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=

# === Frontend ===
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# === Nginx ===
DOMAIN=styleai.local
LETSENCRYPT_EMAIL=your-email@example.com
EOF

# Copy to actual .env file
cp .env.example .env

# Generate secure secrets
echo "Generating secure secrets..."

# Generate PostgreSQL password
POSTGRES_PASSWORD=$(openssl rand -base64 32)
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"

# Generate Redis password
REDIS_PASSWORD=$(openssl rand -base64 32)
echo "REDIS_PASSWORD: $REDIS_PASSWORD"

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 32)
echo "JWT_SECRET: $JWT_SECRET"

# Now edit .env and replace CHANGE_ME with generated values
vim .env
# Replace placeholders with generated values above
```

**Estimated time**: 20 minutes

---

## Phase 5: Docker Compose Configuration

### Step 5.1: Create docker-compose.yml

```bash
cd ~/projects/styleai

# Create main docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # PostgreSQL Database with pgvector
  postgres:
    image: pgvector/pgvector:pg15
    container_name: styleai_postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    volumes:
      - /mnt/styleai/postgres:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"
    networks:
      - styleai_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 1G

  # Weaviate Vector Database
  weaviate:
    image: cr.weaviate.io/semitechnologies/weaviate:1.23.0
    container_name: styleai_weaviate
    restart: unless-stopped
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'text2vec-transformers'
      ENABLE_MODULES: 'text2vec-transformers'
      TRANSFORMERS_INFERENCE_API: 'http://t2v-transformers:8080'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - /mnt/styleai/weaviate:/var/lib/weaviate
    ports:
      - "127.0.0.1:8080:8080"
    networks:
      - styleai_network
    depends_on:
      - t2v-transformers
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:8080/v1/.well-known/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 2G

  # Text2Vec Transformers for Weaviate
  t2v-transformers:
    image: cr.weaviate.io/semitechnologies/transformers-inference:sentence-transformers-all-MiniLM-L6-v2
    container_name: styleai_transformers
    restart: unless-stopped
    environment:
      ENABLE_CUDA: '0'
    networks:
      - styleai_network
    deploy:
      resources:
        limits:
          memory: 1G

  # Redis Cache
  redis:
    image: redis:7.2-alpine
    container_name: styleai_redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - /mnt/styleai/redis:/data
    ports:
      - "127.0.0.1:6379:6379"
    networks:
      - styleai_network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend (will be created in next phase)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: styleai_backend
    restart: unless-stopped
    env_file: .env
    volumes:
      - /mnt/styleai/uploads:/app/uploads
      - /mnt/styleai/logs/backend:/app/logs
    ports:
      - "127.0.0.1:8000:8000"
    networks:
      - styleai_network
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      weaviate:
        condition: service_healthy
    deploy:
      resources:
        limits:
          memory: 2G

  # Next.js Frontend (will be created in next phase)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: styleai_frontend
    restart: unless-stopped
    env_file: .env
    ports:
      - "127.0.0.1:3000:3000"
    networks:
      - styleai_network
    depends_on:
      - backend
    deploy:
      resources:
        limits:
          memory: 1G

  # Nginx Reverse Proxy
  nginx:
    image: nginx:1.25-alpine
    container_name: styleai_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - /mnt/styleai/logs/nginx:/var/log/nginx
    networks:
      - styleai_network
    depends_on:
      - frontend
      - backend

networks:
  styleai_network:
    driver: bridge

EOF

echo "✅ Docker Compose file created"
```

### Step 5.2: Test Infrastructure Services

```bash
# Start only database services first
docker compose up -d postgres redis weaviate t2v-transformers

# Wait 30 seconds for services to initialize
sleep 30

# Check service status
docker compose ps

# Expected output (all should show "healthy" or "running"):
# styleai_postgres         Up (healthy)
# styleai_redis            Up (healthy)
# styleai_weaviate         Up (healthy)
# styleai_transformers     Up

# Test PostgreSQL
docker exec styleai_postgres psql -U styleai_user -d styleai -c "SELECT version();"
# Should show PostgreSQL version

# Test Redis
docker exec styleai_redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d '=' -f2) PING
# Should return: PONG

# Test Weaviate
curl http://localhost:8080/v1/.well-known/ready
# Should return: {"status":"ready"}

# View logs if any issues
docker compose logs -f
# Ctrl+C to exit
```

**Estimated time**: 45 minutes

---

## Phase 6: External API Setup

### Step 6.1: Roboflow API Key

```bash
# 1. Open browser and go to: https://roboflow.com/
# 2. Sign up with Google/GitHub (free account)
# 3. Go to Universe: https://universe.roboflow.com/
# 4. Search for "clothing detection"
# 5. Open this model: https://universe.roboflow.com/main-project-qsu9x/clothing-detection-ev04d
# 6. Click "Use this Model"
# 7. Copy the API key from the code snippet shown
# 8. Add to .env file:

vim .env
# Find ROBOFLOW_API_KEY and paste your key
# Example: ROBOFLOW_API_KEY=abc123xyz789...
```

### Step 6.2: OpenWeatherMap API Key

```bash
# 1. Go to: https://openweathermap.org/api
# 2. Click "Sign Up" and create free account
# 3. Verify email
# 4. Go to API Keys section: https://home.openweathermap.org/api_keys
# 5. Copy the default API key (or generate new one)
# 6. Add to .env:

vim .env
# Find OPENWEATHER_API_KEY and paste your key
```

### Step 6.3: Google OAuth Credentials (Optional)

```bash
# 1. Go to: https://console.cloud.google.com/
# 2. Create new project: "StyleAI"
# 3. Enable Google+ API
# 4. Go to Credentials → Create OAuth 2.0 Client ID
# 5. Application type: Web application
# 6. Authorized redirect URIs:
#    - http://localhost:8000/api/auth/google/callback (dev)
#    - https://yourdomain.com/api/auth/google/callback (prod)
# 7. Copy Client ID and Client Secret
# 8. Add to .env:

vim .env
# Add:
# GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
# GOOGLE_CLIENT_SECRET=your-client-secret
```

**Estimated time**: 30 minutes

---

## Phase 7: Network Configuration

### Step 7.1: Assign Static IP (Recommended)

```bash
# Find your current IP and gateway
ip addr show eth0
ip route | grep default

# Edit dhcpcd configuration
sudo vim /etc/dhcpcd.conf

# Add at the end (adjust IP to your network):
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Save and exit

# Restart networking
sudo systemctl restart dhcpcd

# Verify new IP
ip addr show eth0
```

### Step 7.2: Router Port Forwarding

**Access your router admin panel** (usually 192.168.1.1):

1. Find "Port Forwarding" or "Virtual Server" section
2. Add new rule:
   - **Name**: StyleAI-HTTP
   - **External Port**: 80
   - **Internal IP**: 192.168.1.100 (Pi's IP)
   - **Internal Port**: 80
   - **Protocol**: TCP

3. Add second rule:
   - **Name**: StyleAI-HTTPS
   - **External Port**: 443
   - **Internal IP**: 192.168.1.100
   - **Internal Port**: 443
   - **Protocol**: TCP

4. Save settings

5. Test from external network (use mobile data):
```bash
# Get your public IP
curl ifconfig.me

# Test HTTP access
curl http://your-public-ip
```

**Estimated time**: 15 minutes

---

## Phase 8: Backup Automation

### Step 8.1: Create Backup Script

```bash
# Create backup script
cat > ~/backup-styleai.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/mnt/styleai/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

echo "=== StyleAI Backup Started: $DATE ==="

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker exec styleai_postgres pg_dump -U styleai_user styleai > "$BACKUP_DIR/postgres_$DATE.sql"

# Compress backup
gzip "$BACKUP_DIR/postgres_$DATE.sql"

# Backup uploads directory
echo "Backing up uploads..."
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" /mnt/styleai/uploads/

# Remove old backups
echo "Cleaning old backups (older than $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "uploads_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Backup stats
echo "=== Backup Complete ==="
ls -lh "$BACKUP_DIR" | tail -5
du -sh "$BACKUP_DIR"

EOF

# Make executable
chmod +x ~/backup-styleai.sh

# Test backup
./backup-styleai.sh

# Schedule daily backups at 2 AM
crontab -e

# Add this line:
0 2 * * * /home/pi/backup-styleai.sh >> /home/pi/backup.log 2>&1
```

### Step 8.2: System Monitoring Script

```bash
# Create monitoring script
cat > ~/monitor-styleai.sh << 'EOF'
#!/bin/bash

echo "========================================"
echo "StyleAI System Status - $(date)"
echo "========================================"

echo -e "
🌡️  CPU Temperature:"
vcgencmd measure_temp

echo -e "
💾 Memory Usage:"
free -h

echo -e "
💿 Disk Usage:"
df -h /mnt/styleai | tail -1

echo -e "
🐳 Docker Containers:"
docker ps --format "table {{.Names}}	{{.Status}}	{{.CPUPerc}}	{{.MemUsage}}"

echo -e "
📊 Docker Stats (5 sec snapshot):"
docker stats --no-stream --format "table {{.Name}}	{{.CPUPerc}}	{{.MemUsage}}	{{.NetIO}}"

echo -e "
🔥 Top Processes:"
ps aux --sort=-%cpu | head -6

EOF

chmod +x ~/monitor-styleai.sh

# Run it
./monitor-styleai.sh
```

**Estimated time**: 20 minutes

---

## Phase 9: Testing Infrastructure

### Step 9.1: Complete Health Check

```bash
cd ~/projects/styleai

# Start all services
docker compose up -d

# Wait for services to be healthy (check every 10 seconds)
for i in {1..12}; do
  echo "Waiting for services to be healthy... ($i/12)"
  docker compose ps
  sleep 10
done

# Run comprehensive health check
echo "=== Health Check ==="

# PostgreSQL
echo "1. PostgreSQL:"
docker exec styleai_postgres pg_isready -U styleai_user && echo "✅ Healthy" || echo "❌ Failed"

# Redis
echo "2. Redis:"
docker exec styleai_redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d '=' -f2) PING && echo "✅ Healthy" || echo "❌ Failed"

# Weaviate
echo "3. Weaviate:"
curl -s http://localhost:8080/v1/.well-known/ready | grep -q "ready" && echo "✅ Healthy" || echo "❌ Failed"

# Check disk space
echo "4. Disk Space:"
df -h /mnt/styleai | tail -1

# Check memory
echo "5. Memory:"
free -h

# View logs for errors
echo "6. Recent Errors:"
docker compose logs --tail=50 | grep -i error || echo "No errors found"
```

### Step 9.2: Create Infrastructure Test

```bash
# Create test script
cat > ~/test-infrastructure.sh << 'EOF'
#!/bin/bash

echo "🧪 Testing StyleAI Infrastructure"

# Test PostgreSQL write/read
echo "Testing PostgreSQL..."
docker exec styleai_postgres psql -U styleai_user -d styleai -c "CREATE TABLE IF NOT EXISTS test (id SERIAL PRIMARY KEY, data TEXT);"
docker exec styleai_postgres psql -U styleai_user -d styleai -c "INSERT INTO test (data) VALUES ('Hello from test');"
docker exec styleai_postgres psql -U styleai_user -d styleai -c "SELECT * FROM test;" | grep -q "Hello from test" && echo "✅ PostgreSQL OK"

# Test Redis write/read
echo "Testing Redis..."
docker exec styleai_redis redis-cli -a $(grep REDIS_PASSWORD ~/.env | cut -d '=' -f2) SET test_key "test_value" > /dev/null
docker exec styleai_redis redis-cli -a $(grep REDIS_PASSWORD ~/.env | cut -d '=' -f2) GET test_key | grep -q "test_value" && echo "✅ Redis OK"

# Test Weaviate
echo "Testing Weaviate..."
curl -s http://localhost:8080/v1/meta | grep -q "version" && echo "✅ Weaviate OK"

# Test file uploads directory
echo "Testing uploads directory..."
touch /mnt/styleai/uploads/originals/test.txt && rm /mnt/styleai/uploads/originals/test.txt && echo "✅ Uploads directory OK"

echo "✅ All infrastructure tests passed!"

EOF

chmod +x ~/test-infrastructure.sh
./test-infrastructure.sh
```

**Estimated time**: 15 minutes

---

## Troubleshooting Common Issues

### Issue: Container keeps restarting

```bash
# Check logs
docker compose logs [service-name]

# Common fixes:
# 1. Memory issue - check available memory
free -h

# 2. Port conflict - check what's using the port
sudo netstat -tulpn | grep LISTEN

# 3. Volume permission - fix ownership
sudo chown -R pi:pi /mnt/styleai
```

### Issue: Out of memory

```bash
# Add 4GB swap file
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Issue: SSD not mounting on boot

```bash
# Check fstab entry
cat /etc/fstab | grep styleai

# Re-mount manually
sudo mount -a

# Check kernel messages
dmesg | grep -i usb
```

---

## Success Checklist

- [ ] Raspberry Pi OS installed and updated
- [ ] External SSD mounted at /mnt/styleai
- [ ] UFW firewall configured
- [ ] SSH key-based authentication working
- [ ] Fail2ban protecting SSH
- [ ] Docker and Docker Compose installed
- [ ] Docker data moved to external SSD
- [ ] Project repository created
- [ ] .env file configured with API keys
- [ ] docker-compose.yml created
- [ ] PostgreSQL container running and healthy
- [ ] Redis container running and healthy
- [ ] Weaviate container running and healthy
- [ ] Roboflow API key obtained
- [ ] OpenWeatherMap API key obtained
- [ ] Static IP assigned (optional)
- [ ] Automated backups scheduled
- [ ] All health checks passing

**Total Time**: 6-8 hours (including waiting for downloads/updates)

---

**Next Steps**: Proceed to `04-backend.md` to start building the FastAPI application.
