# Valheim Dedicated Builder

**Automated deployment of Valheim dedicated servers to Ubuntu hosts via Python CLI + Ansible + Docker.**

Deploy a fully configured Valheim server in **5-10 minutes** with a single command. Supports existing Ubuntu hosts with automatic firewall setup, daily backups, and multi-instance port management.

---

## 🎯 What This Does

Valheim Builder is an orchestration tool that:

1. **Gathers deployment parameters** via interactive CLI prompts
2. **Detects port conflicts** and suggests available port ranges automatically
3. **Provisions the target host** using Ansible (installs Docker, UFW, etc.)
4. **Deploys Valheim** in a Docker container with customizable settings
5. **Configures firewall** to allow SSH + game ports (UDP 2456-2458)
6. **Sets up automated backups** with daily snapshots and retention policies
7. **Generates restore scripts** for manual world recovery

---

## ✨ Phase 1.5 Features

### Core Deployment
- ✅ Deploy to existing Ubuntu 24.04 host
- ✅ SSH password or key-based authentication
- ✅ Customizable server name, world name, password
- ✅ Timezone support
- ✅ Docker Compose orchestration

### Networking & Security
- ✅ **Firewall automation** (UFW) - whitelist SSH + Valheim ports
- ✅ **Port conflict detection** - avoids already-in-use ports
- ✅ **Dynamic port assignment** - suggests next available 3-port range (2456-2458, 2459-2461, etc.)
- ✅ **Multi-instance support** - run multiple Valheim servers on same host

### Data Management
- ✅ **Automated daily backups** at 03:00 UTC
- ✅ **Backup retention** - auto-cleanup after 7 days
- ✅ **Restore scripts** - manual recovery from any backup
- ✅ **Config persistence** - world data + server settings backed up

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Ansible 2.15+
- SSH access to target Ubuntu 24.04 host
- Target host with sudo-capable user

### Setup (Local Machine)

```bash
# Clone repo
git clone https://github.com/CyberCoinz/Valheim-Dedicated-Builder.git
cd Valheim-Dedicated-Builder

# Create Python environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Ansible collections
ansible-galaxy collection install -r ansible/collections/requirements.yml
```

### Deploy

```bash
python cli/main.py
```

Select **Option 1** from the menu and follow the prompts:
- Target host/IP
- SSH username
- Authentication method (key or password)
- Server name & world name
- Server password (5+ characters)
- Timezone

The CLI will:
1. Check for port conflicts
2. Generate deployment config
3. Run Ansible playbook
4. Complete in 5-10 minutes

---

## 📋 Current Menu Options

```
Valheim Builder
----------------
1. Deploy to existing Ubuntu host
2. Exit
```

**Option 1: Deploy to existing Ubuntu host**
- Interactive setup with port conflict detection
- Automatic firewall configuration (UFW)
- Daily backup scheduling
- Post-deployment summary

---

## 🏗️ Project Structure

```
Valheim-Dedicated-Builder/
├── cli/                          # Python CLI orchestrator
│   ├── main.py                  # Entry point
│   ├── prompts.py               # Menu & user input
│   ├── config_writer.py         # YAML config generation
│   └── runners.py               # Deployment logic & port detection
│
├── ansible/                      # Infrastructure automation
│   ├── site.yml                 # Main playbook
│   ├── ansible.cfg
│   ├── collections/
│   │   └── requirements.yml     # community.docker collection
│   │
│   └── roles/
│       ├── common/              # Base packages, timezone
│       ├── firewall/            # UFW configuration
│       ├── docker/              # Docker installation
│       ├── valheim/             # Valheim deployment
│       └── backup/              # Backup & restore setup
│
├── config/
│   └── generated/               # Generated deployment configs
│
├── inventory/                   # Ansible inventory
│   └── hosts.ini               # Auto-populated by CLI
│
├── docs/                        # Documentation
│   ├── TESTING.md              # Deployment testing guide
│   └── TEST_CHECKLIST.md       # Pre-deployment checklist
│
└── scripts/                     # Utility scripts (future)
```

---

## 🔧 Generated Artifacts

After deployment, your host has:

```
/opt/valheim/
├── docker-compose.yml          # Generated from templates
├── valheim.env                 # Environment variables
├── config/                     # Server config directory
├── data/                       # World data
└── backups/                    # Backup directory (daily snapshots)

/usr/local/bin/
├── valheim-backup.sh           # Manual backup command
└── valheim-restore.sh          # Restore from backup
```

---

## 📚 Usage Examples

### Test Deployment
```bash
# Run through CLI interactively
python cli/main.py

# Provide:
# - Host: 192.168.1.50
# - User: ubuntu
# - Auth: password (or key path)
# - Password: QAZqazQAZ123$%^
```

### Check Server Status (On Target Host)
```bash
docker ps | grep valheim
docker logs valheim-server
```

### Manual Backup
```bash
ssh ubuntu@192.168.1.50
/usr/local/bin/valheim-backup.sh
```

### Restore from Backup
```bash
ssh ubuntu@192.168.1.50
/usr/local/bin/valheim-restore.sh /opt/valheim/backups/valheim_backup_20260328_030000.tar.gz
```

### Check Firewall
```bash
ssh ubuntu@192.168.1.50
sudo ufw status
```

---

## 🗺️ Roadmap

### Phase 1 (✅ Complete)
- Deploy to existing host
- Docker Compose orchestration
- SSH password auth

### Phase 1.5 (✅ Complete)
- Firewall automation (UFW)
- Port conflict detection
- Automated backups + restore

### Phase 2 (🔜 Next)
- Input validation (IP format, SSH key exists, etc.)
- Smoke test validation playbook
- Menu option: Backup/Restore operations

### Phase 3 (📋 Planned)
- Proxmox VM creation + provisioning
- Cloud provider support (AWS EC2)
- DNS/hostname registration

### Phase 4+ (📋 Future)
- Discord webhook integration
- Whitelist/ban management
- Scheduled world backups
- Web dashboard + stats
- Admin UI

---

## 🐛 Troubleshooting

### SSH Connection Refused
Ensure target host has SSH running:
```bash
ssh-keyscan -H <target_ip> >> ~/.ssh/known_hosts
```

### Ports Already in Use
The CLI will detect this and suggest the next available range automatically.

### Ansible Collection Missing
```bash
ansible-galaxy collection install community.docker
```

### Docker Not Starting
Check target host:
```bash
ssh ubuntu@<target_ip>
sudo systemctl status docker
sudo docker ps
```

See [TESTING.md](docs/TESTING.md) for full debugging guide and [TEST_CHECKLIST.md](docs/TEST_CHECKLIST.md) for pre-deployment verification.

---

## 📖 Documentation

- [TESTING.md](docs/TESTING.md) - Complete deployment & debugging guide
- [TEST_CHECKLIST.md](docs/TEST_CHECKLIST.md) - Pre-deployment verification checklist

---

## 🤝 Architecture

```
User (Local Machine)
    ↓
    ├─→ CLI Prompts [main.py / prompts.py]
    ├─→ Port Detection [runners.py] ← Socket check for available ports
    ├─→ Config Generation [config_writer.py] → deployment.yml
    └─→ Ansible Execution [site.yml]
            ↓
    Target Host (Ubuntu 24.04)
            ↓
        ├─ common role      → apt update, base packages, timezone
        ├─ firewall role    → UFW enable, allow SSH + Valheim ports
        ├─ docker role      → Install Docker + Compose v2
        ├─ valheim role     → Deploy Valheim container
        └─ backup role      → Setup daily backups + restore scripts
```

---

## 📄 License

MIT (Open Source)

---

## 🎮 About Valheim

Valheim is a Viking explorer survival game. Learn more at: https://www.valheimgame.com/

This project uses the popular public Docker image: `ghcr.io/lloesche/valheim-server`
