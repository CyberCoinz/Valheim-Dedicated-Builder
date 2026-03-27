from prompts import main_menu
from runners import run_existing_host_deploy


def main() -> None:
    choice = main_menu()

    if choice == "1":
        run_existing_host_deploy()
    else:
        print("Only option 1 is implemented in Phase 1.")


if __name__ == "__main__":
    main()
