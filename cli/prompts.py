def main_menu() -> str:
    print("\nValheim Builder")
    print("----------------")
    print("1. Deploy to existing Ubuntu host")
    print("2. Backup a server")
    print("3. Restore a server")
    print("4. Smoke test deployment")
    print("5. Exit")
    return input("Choose an option: ").strip()

