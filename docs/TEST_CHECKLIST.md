# Pre-Test Checklist

## Local Machine
- [ ] Python 3.10+ installed (`python3 --version`)
- [ ] Ansible 2.15+ installed (`ansible --version`)
- [ ] Project cloned and venv activated
- [ ] Dependencies installed (`pip list | grep PyYAML`)
- [ ] Collections installed (`ansible-galaxy collection list | grep community.docker`)

## Target Host (Ubuntu 24.04)
- [ ] SSH key-based auth working
- [ ] SSH user has sudo privileges
- [ ] Hostname/IP confirmed
- [ ] Network connectivity verified from local machine
- [ ] Firewall allows SSH (port 22) inbound

## Deployment Parameters
- [ ] Target host/IP: _______________
- [ ] SSH user: _______________
- [ ] SSH key path: _______________
- [ ] Server name decided: _______________
- [ ] World name decided: _______________
- [ ] Server password (5+ chars) prepared: _______________

## Post-Test Verification
- [ ] Ansible playbook completed with `failed=0`
- [ ] `docker ps` shows `valheim-server` running
- [ ] Valheim container logs show no errors
- [ ] UDP ports 2456-2458 listening on target
- [ ] Can reach target external IP on port 2456

## Issues Found
- Issue 1: _______________________________
- Issue 2: _______________________________
- Issue 3: _______________________________

## Notes
_____________________________________________________________
_____________________________________________________________
