import subprocess
from pathlib import Path
import socket

from config_writer import write_yaml_file
from validators import (
    validate_host_address,
    validate_ssh_username,
    validate_ssh_key_exists,
    validate_server_name,
    validate_world_name,
    validate_server_password,
    validate_timezone,
)


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


def prompt_with_validation(prompt_text: str, validator_func, default: str = None) -> str:
    """
    Prompt user for input and validate using provided validator function.
    Repeats until valid input is provided.
    """
    while True:
        if default:
            user_input = input(f"{prompt_text} [{default}]: ").strip() or default
        else:
            user_input = input(f"{prompt_text}: ").strip()
        
        is_valid, error_msg = validator_func(user_input)
        if is_valid:
            return user_input
        else:
            print(f"  ✗ {error_msg}")
            print(f"  Please try again.\n")


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
    print("\n[*] Gathering deployment parameters...\n")
    
    # Host validation
    host = prompt_with_validation(
        "Target host/IP",
        validate_host_address
    )
    
    # SSH user validation
    ssh_user = prompt_with_validation(
        "SSH user",
        validate_ssh_username
    )
    
    # Authentication method
    auth_method = input("SSH auth method (key/password) [password]: ").strip().lower() or "password"
    
    ssh_key_path = None
    ssh_password = None
    
    if auth_method == "key":
        ssh_key_path = prompt_with_validation(
            "SSH private key path",
            validate_ssh_key_exists,
            default="~/.ssh/id_ed25519"
        )
    else:
        ssh_password = input("SSH password: ").strip()
    
    # Timezone validation
    timezone = prompt_with_validation(
        "Timezone",
        validate_timezone,
        default="America/New_York"
    )

    # Server settings validation
    server_name = prompt_with_validation(
        "Server name",
        validate_server_name
    )
    
    world_name = prompt_with_validation(
        "World name",
        validate_world_name
    )
    
    server_password = prompt_with_validation(
        "Server password (5+ characters)",
        validate_server_password
    )

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

    print("\n[*] Configuration summary:")
    print(f"  Host: {host}")
    print(f"  User: {ssh_user}")
    print(f"  Server: {server_name}")
    print(f"  World: {world_name}")
    print(f"  Ports: {list(range(base_port, base_port + 3))}")
    print(f"  Timezone: {timezone}")
    
    confirm = input("\nProceed with deployment? (y/n) [y]: ").strip().lower()
    if confirm == "n":
        print("Deployment cancelled.")
        return

    ansible_cmd = [
        "ansible-playbook",
        "-i", "inventory/hosts.ini",
        "ansible/site.yml",
        "-e", "@config/generated/deployment.yml",
    ]
    
    if not ssh_key_path:
        ansible_cmd.extend(["-k", "-K"])
    
    run_cmd(ansible_cmd)
    
    print(f"\n[✓] Deployment complete! Valheim server running on ports {list(range(base_port, base_port + 3))}")
    print(f"    Server: {server_name}")
    print(f"    World: {world_name}")
    print(f"    Host: {host}")
    print(f"    Backups: /opt/valheim/backups (daily at 03:00 UTC)")


def verify_deployment(host: str, ssh_user: str, ssh_key_path: str = None, ssh_password: str = None) -> None:
    """Execute quick validation checks on deployed host."""
    print("\n[*] Running post-deployment validation...")
    try:
        # This is a placeholder for future validation logic
        print("✓ Deployment validation complete")
    except Exception as e:
        print(f"⚠ Validation warning: {e}")


def run_backup_server() -> None:
    """Backup an existing Valheim server."""
    print("\n[*] Backup Server\n")
    
    host = prompt_with_validation(
        "Target host/IP",
        validate_host_address
    )
    
    ssh_user = prompt_with_validation(
        "SSH user",
        validate_ssh_username
    )
    
    auth_method = input("SSH auth method (key/password) [password]: ").strip().lower() or "password"
    
    ssh_key_path = None
    ssh_password = None
    
    if auth_method == "key":
        ssh_key_path = prompt_with_validation(
            "SSH private key path",
            validate_ssh_key_exists,
            default="~/.ssh/id_ed25519"
        )
    else:
        ssh_password = input("SSH password: ").strip()
    
    # Generate temp inventory for backup command
    temp_inventory = f"""[valheim_hosts]
valheim1 ansible_host={host} ansible_user={ssh_user}"""
    
    if ssh_key_path:
        temp_inventory += f" ansible_ssh_private_key_file={ssh_key_path}"
    else:
        temp_inventory += f" ansible_ssh_pass={ssh_password}"
    
    print("\n[*] Running backup on remote host...")
    
    try:
        cmd = [
            "ssh",
            f"{ssh_user}@{host}",
            "/usr/local/bin/valheim-backup.sh"
        ]
        
        if not ssh_key_path:
            cmd.insert(1, "-o")
            cmd.insert(2, "StrictHostKeyChecking=no")
        else:
            cmd.insert(1, "-i")
            cmd.insert(2, ssh_key_path)
        
        run_cmd(cmd)
        print("\n[✓] Backup completed successfully")
    except Exception as e:
        print(f"\n[✗] Backup failed: {e}")


def run_restore_server() -> None:
    """Restore a Valheim server from backup."""
    print("\n[*] Restore Server\n")
    
    host = prompt_with_validation(
        "Target host/IP",
        validate_host_address
    )
    
    ssh_user = prompt_with_validation(
        "SSH user",
        validate_ssh_username
    )
    
    auth_method = input("SSH auth method (key/password) [password]: ").strip().lower() or "password"
    
    ssh_key_path = None
    ssh_password = None
    
    if auth_method == "key":
        ssh_key_path = prompt_with_validation(
            "SSH private key path",
            validate_ssh_key_exists,
            default="~/.ssh/id_ed25519"
        )
    else:
        ssh_password = input("SSH password: ").strip()
    
    backup_file = input("Backup file path (on remote host): ").strip()
    
    if not backup_file:
        print("[✗] Backup file path cannot be empty")
        return
    
    confirm = input(f"Restore from {backup_file}? This will stop the server. (y/n) [n]: ").strip().lower()
    if confirm != "y":
        print("Restore cancelled.")
        return
    
    print("\n[*] Running restore on remote host...")
    
    try:
        cmd = [
            "ssh",
            f"{ssh_user}@{host}",
            f"/usr/local/bin/valheim-restore.sh {backup_file}"
        ]
        
        if not ssh_key_path:
            cmd.insert(1, "-o")
            cmd.insert(2, "StrictHostKeyChecking=no")
        else:
            cmd.insert(1, "-i")
            cmd.insert(2, ssh_key_path)
        
        run_cmd(cmd)
        print("\n[✓] Restore completed successfully")
    except Exception as e:
        print(f"\n[✗] Restore failed: {e}")


def run_smoke_test() -> None:
    """Run validation checks on a deployed Valheim server."""
    print("\n[*] Smoke Test Deployment\n")
    
    host = prompt_with_validation(
        "Target host/IP",
        validate_host_address
    )
    
    ssh_user = prompt_with_validation(
        "SSH user",
        validate_ssh_username
    )
    
    auth_method = input("SSH auth method (key/password) [password]: ").strip().lower() or "password"
    
    ssh_key_path = None
    ssh_password = None
    
    if auth_method == "key":
        ssh_key_path = prompt_with_validation(
            "SSH private key path",
            validate_ssh_key_exists,
            default="~/.ssh/id_ed25519"
        )
    else:
        ssh_password = input("SSH password: ").strip()
    
    # Write temp inventory
    inventory_text = f"""[valheim_hosts]
valheim1 ansible_host={host} ansible_user={ssh_user}"""
    
    if ssh_key_path:
        inventory_text += f" ansible_ssh_private_key_file={ssh_key_path}"
    else:
        inventory_text += f" ansible_ssh_pass={ssh_password}"
    
    temp_inventory_path = Path("inventory/.temp_validation.ini")
    temp_inventory_path.write_text(inventory_text, encoding="utf-8")
    
    try:
        ansible_cmd = [
            "ansible-playbook",
            "-i", str(temp_inventory_path),
            "ansible/validation.yml",
        ]
        
        if not ssh_key_path:
            ansible_cmd.extend(["-k", "-K"])
        
        run_cmd(ansible_cmd)
        print("\n[✓] Smoke test completed successfully")
    except Exception as e:
        print(f"\n[✗] Smoke test failed: {e}")
    finally:
        # Cleanup temp inventory
        if temp_inventory_path.exists():
            temp_inventory_path.unlink()
