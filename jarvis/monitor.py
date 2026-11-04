"""
JARVIS HUD & Voice Monitor Dashboard
Renders a real-time sci-fi terminal interface showing live audio levels,
system diagnostics, open applications, and command execution logs.
Fully compatible with Windows CP1252/UTF-8 terminal encodings.
"""

import sys
import time

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.table import Table
from rich.text import Text

class JarvisHUD:
    def __init__(self):
        self.console = Console(highlight=False)
        self.log_history = []
        self.status = "ONLINE"
        self.last_command = "None"
        self.last_response = "System ready."
        self.audio_level = 0.0

    def add_log(self, action: str, result: str):
        timestamp = time.strftime("%H:%M:%S")
        self.log_history.append((timestamp, action, result))
        if len(self.log_history) > 6:
            self.log_history.pop(0)

    def render_vu_meter(self, level: float, width: int = 24) -> str:
        filled = int(level * width)
        filled = max(0, min(width, filled))
        bars = "=" * filled
        empty = "-" * (width - filled)
        return f"[{bars}{empty}] {int(level * 100)}%"

    def generate_layout(self, telemetry: dict) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=8),
        )
        layout["body"].split_row(
            Layout(name="voice_monitor", ratio=1),
            Layout(name="system_telemetry", ratio=1),
        )

        # Header
        title = Text("J.A.R.V.I.S.  //  DESKTOP VOICE CONTROLLER & MONITOR", style="bold cyan")
        layout["header"].update(Panel(title, border_style="bold blue", expand=True))

        # Voice Monitor
        status_colors = {
            "ONLINE": "bold green",
            "LISTENING": "bold yellow",
            "RECORDING": "bold red",
            "TRANSCRIBING": "bold cyan",
            "SPEAKING": "bold magenta",
        }
        status_style = status_colors.get(self.status, "bold white")
        
        vm_text = Text()
        vm_text.append("STATUS: ", style="bold white")
        vm_text.append(f"[*] {self.status}\n\n", style=status_style)
        
        vm_text.append("MIC AUDIO MONITOR:\n", style="bold white")
        vm_text.append(f"{self.render_vu_meter(self.audio_level)}\n\n", style="cyan")
        
        vm_text.append("LAST COMMAND SPOKEN:\n", style="bold white")
        vm_text.append(f"\"{self.last_command}\"\n\n", style="italic yellow")
        
        vm_text.append("RESPONSE:\n", style="bold white")
        vm_text.append(f"{self.last_response}\n", style="green")

        layout["voice_monitor"].update(
            Panel(vm_text, title="[bold cyan]VOICE MONITOR[/bold cyan]", border_style="cyan")
        )

        # System Telemetry
        cpu = telemetry.get("cpu_percent", 0.0)
        ram = telemetry.get("ram_percent", 0.0)
        ram_used = telemetry.get("ram_used_gb", 0.0)
        ram_total = telemetry.get("ram_total_gb", 0.0)
        battery = telemetry.get("battery", "N/A")
        open_wins = telemetry.get("open_windows_count", 0)

        sys_text = Text()
        sys_text.append(f"CPU LOAD:      {cpu:>5.1f}%  {self.render_vu_meter(cpu/100, 16)}\n", style="bold white")
        sys_text.append(f"RAM USAGE:     {ram:>5.1f}%  {self.render_vu_meter(ram/100, 16)}\n", style="bold white")
        sys_text.append(f"MEMORY:        {ram_used:.1f} GB / {ram_total:.1f} GB\n", style="dim white")
        sys_text.append(f"BATTERY:       {battery}\n", style="bold white")
        sys_text.append(f"ACTIVE APPS:   {open_wins} windows online\n\n", style="bold white")

        # Top 3 Windows
        sys_text.append("ACTIVE WINDOWS:\n", style="bold cyan")
        windows = telemetry.get("windows", [])[:3]
        for w in windows:
            title = w.get("title", "")[:35]
            sys_text.append(f" - {title}\n", style="dim white")

        layout["system_telemetry"].update(
            Panel(sys_text, title="[bold blue]SYSTEM TELEMETRY[/bold blue]", border_style="blue")
        )

        # Log Table
        table = Table(expand=True, box=None, border_style="dim white")
        table.add_column("Time", style="cyan", width=10)
        table.add_column("Command Executed", style="yellow", width=35)
        table.add_column("Outcome / Verification", style="green")

        for t, act, res in self.log_history:
            table.add_row(t, act, res)

        layout["footer"].update(
            Panel(table, title="[bold cyan]COMMAND EXECUTION LOG[/bold cyan]", border_style="dim blue")
        )

        return layout

if __name__ == "__main__":
    hud = JarvisHUD()
    telemetry = {
        "cpu_percent": 18.5,
        "ram_percent": 74.0,
        "ram_used_gb": 11.5,
        "ram_total_gb": 15.6,
        "battery": "72% (Charging)",
        "open_windows_count": 4,
        "windows": [{"title": "Chrome"}, {"title": "File Explorer"}]
    }
    hud.add_log("voice: 'volume up'", "Volume adjusted by 5 steps")
    hud.add_log("voice: 'open chrome'", "Launched chrome, window focused")
    hud.console.print(hud.generate_layout(telemetry))
