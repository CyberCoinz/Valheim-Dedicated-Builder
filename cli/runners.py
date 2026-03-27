import subprocess
from pathlib import Path

from config_writer import write_yaml_file


def run_cmd(cmd: list[str]) -> None:
    print(f"\n[+] Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def write_inventory(host: str, ssh_user: str, ssh_key_path: str) -> None:
    inventory_text = f"""[valheim_hosts]
valheim1 ansible_host={host} ansible_user={ssh_user} ansible_ssh_private_key_file={ssh_key_path}
"""
    inventory_path = Path("inventory/hosts.ini")
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(inventory_text, encoding="utf-8")


def run_existing_host_deploy() -> None:
    host = input("Target host/IP: ").strip()
    ssh_user = input("SSH user: ").strip()
    ssh_key_path = input("SSH private key path (~/.ssh/id_ed25519): ").strip()
    timezone = input("Timezone [America/New_York]: ").strip() or "America/New_York"

    server_name = input("Server name: ").strip()
    world_name = input("World name: ").strip()
    server_password = input("Server password: ").strip()

    if len(server_password) < 5:
        raise ValueError("Valheim server password must be at least 5 characters.")

    config = {
        "valheim": {
            "timezone": timezone,
            "server_name": server_name,
            "world_name": world_name,
            "server_password": server_password,
            "server_public": 1,
            "base_port": 2456,
            "root_dir": "/opt/valheim",
            "config_dir": "/opt/valheim/config",
            "data_dir": "/opt/valheim/data",
        }
    }

    write_yaml_file(config, "config/generated/deployment.yml")
    write_inventory(host, ssh_user, ssh_key_path)

    run_cmd([
        "ansible-playbook",
        "-i", "inventory/hosts.ini",
        "ansible/site.yml",
        "-e", "@config/generated/deployment.yml",
    ])
