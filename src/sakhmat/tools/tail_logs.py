import sys
import time
from pathlib import Path
from types import SimpleNamespace

from rich.console import Console
from rich.panel import Panel


from ..utils.path import find_project_root, pyproject_log_section


def main():
    """Show tail log display"""

    root: Path = find_project_root("pyproject.toml")

    log_config: SimpleNamespace = pyproject_log_section()
    # PARAM: log dir relative path from root
    log_path: Path = root / "logs" / log_config.file_name

    if not log_path.exists():
        print(f"No log file found at {log_path}")
        sys.exit(1)

    tail_log(str(log_path))


def tail_log(log_path: str):
    console = Console()
    path = Path(log_path)
    if not path.exists():
        console.print(f"[bold red]Error:[/bold red] Log file {log_path} not found.")
        return

    console.print(
        Panel(f"Tailing [bold cyan]{log_path}[/bold cyan]...", title="Loguru Monitor")
    )

    with open(path, "r") as f:
        # Go to the end of the file
        f.seek(0, 2)

        try:
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)  # Sleep briefly to save CPU
                    continue

                # Simple coloring based on Loguru levels
                if "DEBUG" in line:
                    console.print(line.strip(), style="bold yellow")
                elif "INFO" in line:
                    console.print(line.strip(), style="bold white")
                elif "WARNING" in line:
                    console.print(line.strip(), style="bold magenta")
                elif "ERROR" in line:
                    console.print(line.strip(), style="bold red")
                elif "SUCCESS" in line:
                    console.print(line.strip(), style="bold green")
                else:
                    console.print(line.strip())
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped tailing.[/yellow]")


if __name__ == "__main__":
    main()
