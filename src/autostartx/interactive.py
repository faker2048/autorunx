"""Interactive selectors."""

from typing import List, Optional

from .models import ServiceInfo


def select_service(
    services: List[ServiceInfo], prompt: str = "Please select service"
) -> Optional[ServiceInfo]:
    """Interactive service selection."""
    if not services:
        print("No services available")
        return None

    if len(services) == 1:
        return services[0]

    print(f"\n{prompt}:")
    print("-" * 50)

    for i, service in enumerate(services, 1):
        status_color = _get_status_color(service.status.value)
        print(
            f"{i:2d}. {service.name:<20} "
            f"[{status_color}{service.status.value}{_get_reset_color()}] {service.id}"
        )

    print("-" * 50)

    while True:
        try:
            choice = input(f"Please enter number (1-{len(services)}, q to quit): ").strip()

            if choice.lower() == "q":
                return None

            index = int(choice) - 1
            if 0 <= index < len(services):
                return services[index]
            else:
                print(f"Please enter valid number (1-{len(services)})")

        except (ValueError, KeyboardInterrupt):
            print("\nOperation cancelled")
            return None


def confirm_action(action: str, target: str) -> bool:
    """Confirm action."""
    try:
        response = input(f"Are you sure you want to {action} '{target}'? (y/N): ").strip().lower()
        return response in ["y", "yes"]
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return False


def _get_status_color(status: str) -> str:
    """Get status color code."""
    colors = {
        "running": "\033[32m",  # Green
        "stopped": "\033[31m",  # Red
        "paused": "\033[33m",  # Yellow
        "failed": "\033[91m",  # Bright red
        "starting": "\033[36m",  # Cyan
    }
    return colors.get(status, "")


def _get_reset_color() -> str:
    """Get color reset code."""
    return "\033[0m"
