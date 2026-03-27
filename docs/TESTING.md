# Phase 1 Testing Guide

## Prerequisites

- **Target host**: Ubuntu 24.04 LTS
- **SSH access**: Key-based auth to target host
- **Python 3.10+**: On your local machine
- **Ansible 2.15+**: Installed locally
- **docker-compose-v2**: Will be installed by Ansible

## Local Setup

```bash
# Clone and setup
git clone https://github.com/CyberCoinz/Valheim-Dedicated-Builder.git
cd Valheim-Dedicated-Builder

# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r ansible/collections/requirements.yml

# Verify Ansible
ansible --version
ansible-galaxy collection list | grep community.docker
```

## Test Deployment

### 1. Prepare target host

Ensure your Ubuntu 24.04 host:
- Is reachable via SSH
- Has a user with sudo privileges (e.g., `ubuntu`)
- Can accept SSH key auth

Get the IP: `ip addr show` or check your router

### 2. Run the CLI

```bash
python cli/main.py
```

Select option **1: Deploy to existing Ubuntu host**

Provide:
- **Target host/IP**: e.g., `192.168.1.50` or `valheim.example.com`
- **SSH user**: e.g., `ubuntu`
- **SSH private key path**: e.g., `/home/user/.ssh/id_ed25519`
- **Timezone**: default `America/New_York` or your timezone
- **Server name**: e.g., `My Valheim Server`
- **World name**: e.g., `Dedicated`
- **Server password**: minimum 5 characters (keep it safe!)

### 3. Watch the deployment

Ansible will:
1. Update apt and install base packages
2. Install Docker and docker-compose-v2
3. Create `/opt/valheim` directories
4. Template environment and compose files
5. Start Valheim container

Total time: **5-10 minutes** (depends on host network/CPU)

### 4. Verify success

On target host:

```bash
# Check container running
docker ps | grep valheim

# Check logs
docker logs valheim-server

# Check ports listening
sudo ufw status
netstat -uln | grep 245[678]
```

From local machine:

```bash
# Ping container (optionally)
telnet <target_ip> 2456
```

Wait **5-10 minutes** after container start for world generation.

## Debugging

### Connection issues

```bash
# Test SSH connectivity
ssh -i /path/to/key ubuntu@<target_ip> "echo OK"

# Check SSH key permissions
ls -la ~/.ssh/id_ed25519
# Should be: -rw------- (600)
```

### Ansible run failed

```bash
# Re-run with verbose output
cd /tmp/valheim-builder
ansible-playbook -i inventory/hosts.ini ansible/site.yml \
  -e @config/generated/deployment.yml -vv
```

### Docker issues on target

```bash
# SSH to host
ssh -i /path/to/key ubuntu@<target_ip>

# Check Docker service
sudo systemctl status docker

# Check compose
docker-compose-v2 --version

# View compose logs
docker-compose-v2 -f /opt/valheim/docker-compose.yml logs
```

### Port access issues

Valheim needs these UDP ports:
- **2456**: Game traffic
- **2457**: Server info
- **2458**: Server notifications

Check firewall on target or router for UDP port blocking.

## Expected Output

```
[+] Running: ansible-playbook -i inventory/hosts.ini ansible/site.yml -e @config/generated/deployment.yml
...
TASK [valheim : Start Valheim with Docker Compose v2] ****
ok: [valheim1]

PLAY RECAP ****
valheim1 : ok=XX changed=XX unreachable=0 failed=0
```

If `failed=0`, deployment succeeded ✓

## Next Steps After Success

1. **Commit**: `git add -A && git commit -m "Phase 1 MVP tested and working on Ubuntu 24.04"`
2. **Add Commit 2**: Firewall rules and backup script
3. **Add Commit 3**: Input validation
