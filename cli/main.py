from .prompts import main_menu
from .runners import run_existing_host_deploy, run_backup_server, run_restore_server, run_smoke_test, run_create_vm_deploy


def main() -> None:
    choice = main_menu()

    if choice == "1":
        run_existing_host_deploy()
    elif choice == "2":
        run_backup_server()
    elif choice == "3":
        run_restore_server()
    elif choice == "4":
        run_smoke_test()
    elif choice == "5":
        run_create_vm_deploy()
    elif choice == "6":
        print("Goodbye.")
    else:
        print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
