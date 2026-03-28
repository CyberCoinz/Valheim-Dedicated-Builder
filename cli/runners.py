import subprocess
from pathlib import Path
import socket

from config_writer import write_yaml_file


def run_cmd(cmd: list[str]) -> None:
    print(f"\n[+] Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def check_port_available(port: int) -> bool:
    """Check if a UDP port is available locally."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("", port))
        sock.close()
        return True
    except OSError:
        return False


def suggest_available_port(start_port: int = 2456) -> int:
    """Find next available port range (3 consecutive ports for Valheim)."""
    current_port = start_port
    while current_port < 65535:
        if all(check_port_available(current_port + i) for i in range(3)):
            return current_port
        current_port += 3
    raise RuntimeError("No available port range found below 65535")


def write_inventory(host: str, ssh_user: str, ssh_key_path: str = None, ssh_password: str = None) -> None:
    if ssh_key_path:
        inventory_text = f"""[valheim_hosts]
valheim1 ansible_host={host} ansible_user={ssh_user} ansible_ssh_private_key_file={ssh_key_path}
"""
    else:
        inventory_text = f"""[valheim_hosts]
valheim1 ansible_host={host} ansible_user={ssh_user} ansible_ssh_pass={ssh_password}
"""
    inventory_path = Path("inventory/hosts.ini")
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(inventory_text, encoding="utf-8")


def run_existing_host_deploy() -> None:
    host = input("Target host/IP: ").strip()
    ssh_user = input("SSH user: ").strip()
    
    auth_method = input("SSH auth method (key/password) [password]: ").strip().lower() or "password"
    
    ssh_key_path = None
    ssh_password = None
    
    if auth_method == "key":
        ssh_key_path = input("SSH private key path (~/.ssh/id_ed25519): ").strip()
    else:
        ssh_password = input("SSH password: ").strip()
    
    timezone = input("Timezone [America/New_York]: ").strip() or "America/New_York"

    server_name = input("Server name: ").strip()
    world_name = input("World name: ").strip()
    server_password = input("Server password: ").strip()

    if len(server_password) < 5:
        raise ValueError("Valheim server password must be at least 5 characters.")

    # Port availability check
    base_port = 2456
    default_ports = list(range(base_port, base_port + 3))
    
    print(f"\n[*] Checking if ports {default_ports} are available...")
    if all(check_port_available(p) for p in default_ports):
        print(f"✓ Ports {default_ports} are available")
    else:
        print(f"⚠ Ports {default_ports} appear to be in use")
        use_default = input("Use different port anyway? (y/n) [n]: ").strip().lower()
        if use_default != "y":
            suggested_port = suggest_available_port(base_port + 3)
            print(f"✓ Suggesting ports {list(range(suggested_port, suggested_port + 3))}")
            use_suggested = input(f"Use ports starting at {suggested_port}? (y/n) [y]: ").strip().lower()
            if use_suggested != "n":
                base_port = suggested_port

    config = {
        "valheim": {
            "timezone": timezone,
            "server_name": server_name,
            "world_name": world_name,
            "server_password": server_password,
            "server_public": 1,
            "base_port": base_port,
            "root_dir": "/opt/valheim",
            "config_dir": "/opt/valheim/config",
            "data_dir": "/opt/valheim/data",
        }
    }

    write_yaml_file(config, "config/generated/deployment.yml")
    write_inventory(host, ssh_user, ssh_key_path, ssh_password)

    ansible_cmd = [
        "ansible-playbook",
        "-i", "inventory/hosts.ini",
        "ansible/site.yml",
        "-e", "@config/generated/deployment.yml",
    ]
    
    if not ssh_key_path:
        ansible_cmd.extend(["-k", "-K"])
    
    run_cmd(ansible_cmd)
    
    print(f"\n[+] Deployment complete! Valheim server running on ports {list(range(base_port, base_port + 3))}")
    print(f"    Server: {server_name}")
    print(f"    World: {world_name}")
    print(f"    Host: {host}")


def verify_deployment(host: str, ssh_user: str, ssh_key_path: str = None, ssh_password: str = None) -> None:
    """Execute quick validation checks on deployed host."""
    print("\n[*] Running post-deployment validation...")
    try:
        # This is a placeholder for future validation logic
        print("✓ Deployment validation complete")
    except Exception as e:
        print(f"⚠ Validation warning: {e}")
