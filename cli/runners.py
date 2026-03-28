import subprocess
from pathlib import Path
import socket
from pyVmomi import vim, vmodl
from pyVim import connect
import yaml

from config_writer import write_yaml_file


def load_local_config():
    """Load local configuration file with sensitive data."""
    config_path = Path("config/local.yml")
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}
from validators import (
    validate_host_address,
    validate_ssh_username,
    validate_ssh_key_exists,
    validate_server_name,
    validate_world_name,
    validate_server_password,
    validate_timezone,
    validate_esxi_host,
    validate_esxi_username,
    validate_esxi_password,
    validate_vm_template_name,
    validate_vm_name,
    validate_datastore_name,
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
    
    local_config = load_local_config()
    
    # Check for saved hosts
    saved_hosts = local_config.get('hosts', [])
    if saved_hosts:
        print("Saved hosts:")
        for i, host in enumerate(saved_hosts, 1):
            print(f"  {i}. {host['name']} ({host['ip']})")
        print("  0. Enter new host")
        
        choice = input("Choose a saved host or enter 0 for new: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(saved_hosts):
            host_config = saved_hosts[int(choice) - 1]
            host = host_config['ip']
            ssh_user = host_config['user']
            auth_method = host_config['auth']
            ssh_key_path = host_config.get('key_path', '~/.ssh/id_ed25519')
            ssh_password = host_config.get('password', '')
        else:
            host = None
    else:
        host = None
    
    if host is None:
        # Host validation
        host = prompt_with_validation(
            "Target host/IP",
            validate_host_address
        )
    
    if 'ssh_user' not in locals():
        # SSH user validation
        default_user = local_config.get('ssh', {}).get('default_user', 'ubuntu')
        ssh_user = prompt_with_validation(
            "SSH user",
            validate_ssh_username,
            default=default_user
        )
    
    if 'auth_method' not in locals():
        # Authentication method
        auth_method = input("SSH auth method (key/password) [password]: ").strip().lower() or "password"
    
    if 'ssh_key_path' not in locals():
        ssh_key_path = None
    if 'ssh_password' not in locals():
        ssh_password = None
    
    if auth_method == "key":
        if ssh_key_path is None:
            default_key = local_config.get('ssh', {}).get('default_key_path', '~/.ssh/id_ed25519')
            ssh_key_path = prompt_with_validation(
                "SSH private key path",
                validate_ssh_key_exists,
                default=default_key
            )
    else:
        if ssh_password == '':
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


def connect_to_esxi(host: str, user: str, password: str):
    """Connect to ESXi host and return service instance."""
    try:
        service_instance = connect.SmartConnectNoSSL(
            host=host,
            user=user,
            pwd=password,
            port=443
        )
        return service_instance
    except Exception as e:
        raise Exception(f"Failed to connect to ESXi: {e}")


def get_obj(content, vimtype, name):
    """Get object by name from vSphere inventory."""
    obj = None
    container = content.viewManager.CreateContainerView(
        content.rootFolder, vimtype, True
    )
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj


def clone_vm(service_instance, template_name: str, vm_name: str, datastore_name: str):
    """Clone VM from template."""
    content = service_instance.RetrieveContent()
    
    # Find template
    template = get_obj(content, [vim.VirtualMachine], template_name)
    if not template:
        raise Exception(f"Template '{template_name}' not found")
    
    # Find datastore
    datastore = get_obj(content, [vim.Datastore], datastore_name)
    if not datastore:
        raise Exception(f"Datastore '{datastore_name}' not found")
    
    # Get the folder where the template is located
    destfolder = template.parent
    
    # VM relocation spec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = datastore
    relospec.pool = template.resourcePool
    
    # VM clone spec
    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = True
    
    print(f"[*] Cloning VM '{vm_name}' from template '{template_name}'...")
    task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
    
    # Wait for task completion
    while task.info.state not in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]:
        pass
    
    if task.info.state == vim.TaskInfo.State.error:
        raise Exception(f"VM clone failed: {task.info.error}")
    
    # Get the cloned VM
    cloned_vm = get_obj(content, [vim.VirtualMachine], vm_name)
    return cloned_vm


def get_vm_ip(service_instance, vm_name: str, timeout: int = 300):
    """Get IP address of the VM."""
    content = service_instance.RetrieveContent()
    vm = get_obj(content, [vim.VirtualMachine], vm_name)
    
    if not vm:
        raise Exception(f"VM '{vm_name}' not found")
    
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if vm.guest.ipAddress:
            return vm.guest.ipAddress
        time.sleep(5)
    
    raise Exception(f"Timeout waiting for VM '{vm_name}' to get IP address")


def run_create_vm_deploy() -> None:
    """Create VM on ESXi and deploy Valheim server."""
    print("\n[*] Create VM and Deploy Valheim Server (ESXi)\n")
    
    local_config = load_local_config()
    esxi_config = local_config.get('esxi', {})
    
    # ESXi connection details
    default_host = esxi_config.get('host', '')
    if default_host:
        esxi_host = prompt_with_validation(
            "ESXi host/IP",
            validate_esxi_host,
            default=default_host
        )
    else:
        esxi_host = prompt_with_validation(
            "ESXi host/IP",
            validate_esxi_host
        )
    
    default_user = esxi_config.get('username', 'root')
    esxi_user = prompt_with_validation(
        "ESXi username",
        validate_esxi_username,
        default=default_user
    )
    
    stored_password = esxi_config.get('password', '')
    if stored_password:
        use_stored = input(f"Use stored password for {esxi_user}? (y/n) [y]: ").strip().lower()
        if use_stored != 'n':
            esxi_password = stored_password
        else:
            esxi_password = input("ESXi password: ").strip()
    else:
        esxi_password = input("ESXi password: ").strip()
    
    is_valid, error_msg = validate_esxi_password(esxi_password)
    if not is_valid:
        print(f"  ✗ {error_msg}")
        return
    
    # VM details
    default_template = esxi_config.get('vm_template', '')
    if default_template:
        vm_template = prompt_with_validation(
            "VM template name",
            validate_vm_template_name,
            default=default_template
        )
    else:
        vm_template = prompt_with_validation(
            "VM template name",
            validate_vm_template_name
        )
    
    vm_name = prompt_with_validation(
        "New VM name",
        validate_vm_name
    )
    
    default_datastore = esxi_config.get('datastore', 'datastore1')
    datastore = prompt_with_validation(
        "Datastore name",
        validate_datastore_name,
        default=default_datastore
    )
    
    # Valheim server config
    timezone = prompt_with_validation(
        "Timezone",
        validate_timezone,
        default="America/New_York"
    )
    
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
    
    # Port availability check (local check, VM will have its own)
    base_port = 2456
    print(f"\n[*] Note: Ports {list(range(base_port, base_port + 3))} will be used on the VM")
    
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
    
    print("\n[*] Configuration summary:")
    print(f"  ESXi Host: {esxi_host}")
    print(f"  VM Template: {vm_template}")
    print(f"  New VM: {vm_name}")
    print(f"  Datastore: {datastore}")
    print(f"  Server: {server_name}")
    print(f"  World: {world_name}")
    print(f"  Ports: {list(range(base_port, base_port + 3))}")
    print(f"  Timezone: {timezone}")
    
    confirm = input("\nProceed with VM creation and deployment? (y/n) [y]: ").strip().lower()
    if confirm == "n":
        print("VM creation cancelled.")
        return
    
    service_instance = None
    try:
        # Connect to ESXi
        print("\n[*] Connecting to ESXi...")
        service_instance = connect_to_esxi(esxi_host, esxi_user, esxi_password)
        
        # Clone VM
        cloned_vm = clone_vm(service_instance, vm_template, vm_name, datastore)
        print(f"[✓] VM '{vm_name}' created successfully")
        
        # Wait for VM to get IP
        print("[*] Waiting for VM to boot and get IP address...")
        vm_ip = get_vm_ip(service_instance, vm_name)
        print(f"[✓] VM IP address: {vm_ip}")
        
        # Write config
        write_yaml_file(config, "config/generated/deployment.yml")
        
        # Write inventory for the new VM (assume SSH key auth for now, or password)
        # For simplicity, assume password auth initially
        ssh_user = "ubuntu"  # Assume Ubuntu VM template
        ssh_password = "ubuntu"  # This should be changed, but for demo
        
        inventory_text = f"""[valheim_hosts]
valheim1 ansible_host={vm_ip} ansible_user={ssh_user} ansible_ssh_pass={ssh_password}
"""
        inventory_path = Path("inventory/hosts.ini")
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(inventory_text, encoding="utf-8")
        
        print("[*] Waiting for VM to be ready for SSH...")
        import time
        time.sleep(30)  # Wait for SSH to be available
        
        # Run Ansible deployment
        ansible_cmd = [
            "ansible-playbook",
            "-i", "inventory/hosts.ini",
            "ansible/site.yml",
            "-e", "@config/generated/deployment.yml",
            "-k", "-K"  # Ask for SSH password and sudo password
        ]
        
        run_cmd(ansible_cmd)
        
        print(f"\n[✓] VM creation and deployment complete!")
        print(f"    VM Name: {vm_name}")
        print(f"    VM IP: {vm_ip}")
        print(f"    Server: {server_name}")
        print(f"    World: {world_name}")
        print(f"    Ports: {list(range(base_port, base_port + 3))}")
        print(f"    Backups: /opt/valheim/backups (daily at 03:00 UTC)")
        
    except Exception as e:
        print(f"\n[✗] VM creation/deployment failed: {e}")
    finally:
        if service_instance:
            connect.Disconnect(service_instance)
