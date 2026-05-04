#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from auth_manager import AuthManager


COMMANDS = ("setup", "list", "delete")


def usage() -> None:
    print("Usage: python scripts/run.py <module> <command> [args...]")
    print()
    print("Modules:")
    print("  auth_manager  - Manage authentication credentials")
    print()
    print("auth_manager commands:")
    print("  setup         - Initialize the auth manager")
    print("  list          - List stored services")
    print("  delete <svc>  - Delete credentials for a service")


def run_auth_manager(command: str, args: list[str]) -> int:
    manager = AuthManager()

    if command == "setup":
        manager.setup()
        return 0

    if command == "list":
        manager.load()
        services = manager.list_services()
        if not services:
            print("No credentials stored.")
        else:
            print("Stored services:")
            for svc in services:
                print(f"  - {svc}")
        return 0

    if command == "delete":
        if not args:
            print("Error: delete requires a service name", file=sys.stderr)
            return 1
        manager.load()
        removed = manager.delete(args[0])
        if not removed:
            print(f"No credentials found for service: {args[0]}", file=sys.stderr)
            return 1
        return 0

    print(f"Unknown auth_manager command: {command}", file=sys.stderr)
    print(f"Available commands: {', '.join(COMMANDS)}", file=sys.stderr)
    return 1


def main() -> int:
    if len(sys.argv) < 3:
        usage()
        return 1

    module = sys.argv[1]
    command = sys.argv[2]
    args = sys.argv[3:]

    if module == "auth_manager":
        return run_auth_manager(command, args)

    print(f"Unknown module: {module}", file=sys.stderr)
    usage()
    return 1


if __name__ == "__main__":
    sys.exit(main())
