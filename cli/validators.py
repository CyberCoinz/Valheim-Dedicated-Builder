import re
import os
from pathlib import Path


def validate_ip_address(ip: str) -> tuple[bool, str]:
    """
    Validate IPv4 address format.
    Returns: (is_valid, error_message)
    """
    ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    if re.match(ipv4_pattern, ip):
        return True, ""
    return False, f"Invalid IPv4 address: {ip}"


def validate_hostname(hostname: str) -> tuple[bool, str]:
    """
    Validate hostname format (FQDN or localhost).
    Returns: (is_valid, error_message)
    """
    hostname_pattern = r"^([a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?\.)*[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$"
    if re.match(hostname_pattern, hostname.lower()):
        return True, ""
    return False, f"Invalid hostname: {hostname}"


def validate_host_address(host: str) -> tuple[bool, str]:
    """
    Validate that host is either valid IP or valid hostname.
    Returns: (is_valid, error_message)
    """
    is_ip_valid, _ = validate_ip_address(host)
    if is_ip_valid:
        return True, ""
    
    is_hostname_valid, _ = validate_hostname(host)
    if is_hostname_valid:
        return True, ""
    
    return False, f"Host must be valid IPv4 address or hostname: {host}"


def validate_ssh_key_exists(key_path: str) -> tuple[bool, str]:
    """
    Validate that SSH private key file exists and has correct permissions.
    Returns: (is_valid, error_message)
    """
    expanded_path = os.path.expanduser(key_path)
    
    if not os.path.exists(expanded_path):
        return False, f"SSH key not found: {expanded_path}"
    
    if not os.path.isfile(expanded_path):
        return False, f"SSH key path is not a file: {expanded_path}"
    
    # Check permissions (should be readable only by owner)
    stat_info = os.stat(expanded_path)
    mode = stat_info.st_mode
    
    if mode & 0o077:
        return False, f"SSH key has insecure permissions (should be 600): {oct(mode)}"
    
    return True, ""


def validate_server_password(password: str) -> tuple[bool, str]:
    """
    Validate server password meets minimum requirements.
    Returns: (is_valid, error_message)
    """
    if len(password) < 5:
        return False, "Server password must be at least 5 characters"
    
    if len(password) > 100:
        return False, "Server password must be less than 100 characters"
    
    return True, ""


def validate_server_name(name: str) -> tuple[bool, str]:
    """
    Validate server name is not empty and reasonable length.
    Returns: (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Server name cannot be empty"
    
    if len(name) < 2:
        return False, "Server name must be at least 2 characters"
    
    if len(name) > 50:
        return False, "Server name must be less than 50 characters"
    
    return True, ""


def validate_world_name(name: str) -> tuple[bool, str]:
    """
    Validate world name is not empty and reasonable length.
    Returns: (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "World name cannot be empty"
    
    if len(name) < 2:
        return False, "World name must be at least 2 characters"
    
    if len(name) > 50:
        return False, "World name must be less than 50 characters"
    
    return True, ""


def validate_timezone(tz: str) -> tuple[bool, str]:
    """
    Validate timezone is valid (basic check against common zones).
    Returns: (is_valid, error_message)
    """
    tz_path = Path("/usr/share/zoneinfo") / tz
    
    if not tz_path.exists():
        return False, f"Invalid timezone: {tz}. Use format like 'America/New_York' or 'UTC'"
    
    return True, ""


def validate_ssh_username(username: str) -> tuple[bool, str]:
    """
    Validate SSH username format.
    Returns: (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "SSH username cannot be empty"
    
    # Unix username pattern: lowercase letter, digits, underscore, hyphen
    username_pattern = r"^[a-z0-9_-]+$"
    if not re.match(username_pattern, username.lower()):
        return False, f"Invalid SSH username format: {username}"
    
    return True, ""


def validate_port_number(port: int) -> tuple[bool, str]:
    """
    Validate port number is in valid range.
    Returns: (is_valid, error_message)
    """
    if not isinstance(port, int):
        try:
            port = int(port)
        except (ValueError, TypeError):
            return False, f"Port must be a number: {port}"
    
    if port < 1024 or port > 65535:
        return False, f"Port must be between 1024 and 65535: {port}"
    
    return True, ""
