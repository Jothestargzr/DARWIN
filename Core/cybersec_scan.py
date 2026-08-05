"""
GLM-5 CyberSec Scanner — AI-Powered Mac Security Audit
Collects local system telemetry (processes, network, launch agents, login items, etc.)
and sends the findings to GLM for intelligent threat analysis and remediation advice.
"""

import subprocess
import os
import sys
import json
import datetime

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from glm5_client import GLM5Client

console = Console()

# ─────────────────────────────────────────────────
# LOCAL DATA COLLECTORS (all offline, no network)
# ─────────────────────────────────────────────────

def _run(cmd: str, timeout: int = 15) -> str:
    """Run a shell command and return stdout, silently handling errors."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except Exception:
        return ""


def collect_running_processes() -> str:
    """Top 40 processes by CPU, plus any running as root."""
    top_cpu = _run("ps aux --sort=-%cpu 2>/dev/null | head -45 || ps aux | sort -nrk 3 | head -45")
    return top_cpu


def collect_network_connections() -> str:
    """Active network connections and listening ports."""
    conns = _run("netstat -an 2>/dev/null | head -80")
    lsof_listen = _run("lsof -i -P -n 2>/dev/null | grep LISTEN | head -40")
    return f"--- netstat ---\n{conns}\n\n--- Listening Ports (lsof) ---\n{lsof_listen}"


def collect_launch_agents() -> str:
    """List all LaunchAgents and LaunchDaemons (common malware persistence)."""
    locations = [
        "~/Library/LaunchAgents",
        "/Library/LaunchAgents",
        "/Library/LaunchDaemons",
        "/System/Library/LaunchAgents",
        "/System/Library/LaunchDaemons",
    ]
    results = []
    for loc in locations:
        expanded = os.path.expanduser(loc)
        if os.path.isdir(expanded):
            files = os.listdir(expanded)
            results.append(f"\n[{loc}] ({len(files)} items)")
            for f in sorted(files):
                results.append(f"  {f}")
    return "\n".join(results)


def collect_login_items() -> str:
    """Login items and startup programs (no System Events access needed)."""
    # Use sfltool for background task management entries (no permission prompt)
    sfctl = _run("sfltool dumpbtm 2>/dev/null | head -80")
    # List login items via launchctl (no permission prompt)
    launchctl_gui = _run("launchctl list 2>/dev/null | head -40")
    # Check for apps registered to open at login via Launch Services
    lsregister = _run("/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -dump 2>/dev/null | grep -i 'login\|launch.*agent' | head -20")
    return (
        f"--- Background Items (sfltool) ---\n{sfctl or '(not available)'}\n\n"
        f"--- launchctl list ---\n{launchctl_gui or '(empty)'}\n\n"
        f"--- Launch Services login-related ---\n{lsregister or '(none found)'}"
    )


def collect_crontabs() -> str:
    """User and system crontabs."""
    user_cron = _run("crontab -l 2>/dev/null")
    system_cron = _run("cat /etc/crontab 2>/dev/null")
    return f"--- User Crontab ---\n{user_cron or '(empty)'}\n\n--- /etc/crontab ---\n{system_cron or '(empty/not found)'}"


def collect_dns_config() -> str:
    """DNS resolver configuration (DNS hijacking detection)."""
    resolv = _run("scutil --dns 2>/dev/null | head -40")
    hosts_mod = _run("stat -f '%Sm' /etc/hosts 2>/dev/null")
    hosts_custom = _run("grep -v '^#' /etc/hosts 2>/dev/null | grep -v '^$' | grep -v 'localhost'")
    return f"--- DNS Resolvers ---\n{resolv}\n\n/etc/hosts last modified: {hosts_mod}\nCustom host entries:\n{hosts_custom or '(none)'}"


def collect_browser_extensions() -> str:
    """List Chrome and Safari extension folders."""
    chrome_ext = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Extensions")
    results = []
    if os.path.isdir(chrome_ext):
        exts = os.listdir(chrome_ext)
        results.append(f"Chrome Extensions ({len(exts)} installed): {', '.join(exts[:20])}")
    safari_ext = _run("pluginkit -mAD -p com.apple.Safari.extension 2>/dev/null | head -20")
    if safari_ext:
        results.append(f"Safari Extensions:\n{safari_ext}")
    return "\n".join(results) if results else "(no browser extensions found)"


def collect_firewall_status() -> str:
    """macOS firewall and SIP status."""
    fw = _run("/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null")
    sip = _run("csrutil status 2>/dev/null")
    gatekeeper = _run("spctl --status 2>/dev/null")
    filevault = _run("fdesetup status 2>/dev/null")
    return f"Firewall: {fw}\nSIP: {sip}\nGatekeeper: {gatekeeper}\nFileVault: {filevault}"


def collect_recent_installs() -> str:
    """Recently modified apps and brew packages."""
    recent_apps = _run("ls -lt /Applications 2>/dev/null | head -15")
    brew_list = _run("brew list --versions 2>/dev/null | head -25")
    return f"--- Recently Modified /Applications ---\n{recent_apps}\n\n--- Homebrew Packages ---\n{brew_list or '(brew not installed or empty)'}"


def collect_user_accounts() -> str:
    """List local user accounts and admin users."""
    users = _run("dscl . list /Users | grep -v '^_' | grep -v 'daemon\\|nobody\\|root'")
    admins = _run("dscl . -read /Groups/admin GroupMembership 2>/dev/null")
    last_logins = _run("last -5 2>/dev/null")
    return f"--- Local Users ---\n{users}\n\n--- Admin Group ---\n{admins}\n\n--- Recent Logins ---\n{last_logins}"


def collect_system_info() -> str:
    """Basic system information."""
    info = _run("sw_vers 2>/dev/null")
    uptime = _run("uptime")
    disk = _run("df -h / 2>/dev/null")
    return f"{info}\nUptime: {uptime}\n\n--- Disk Usage ---\n{disk}"


# ─────────────────────────────────────────────────
# MAIN SCANNER
# ─────────────────────────────────────────────────

COLLECTORS = [
    ("System Info",            collect_system_info),
    ("Running Processes",      collect_running_processes),
    ("Network Connections",    collect_network_connections),
    ("Firewall & SIP Status",  collect_firewall_status),
    ("Launch Agents/Daemons",  collect_launch_agents),
    ("Login & Startup Items",  collect_login_items),
    ("Crontabs",               collect_crontabs),
    ("DNS Configuration",      collect_dns_config),
    ("Browser Extensions",     collect_browser_extensions),
    ("Recent Installs & Apps", collect_recent_installs),
    ("User Accounts & Logins", collect_user_accounts),
]


def run_scan() -> dict:
    """Run all collectors and return results."""
    results = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning...", total=len(COLLECTORS))
        for name, collector in COLLECTORS:
            progress.update(task, description=f"Scanning: {name}...")
            try:
                results[name] = collector()
            except Exception as e:
                results[name] = f"(error: {e})"
            progress.advance(task)
    return results


def build_prompt(scan_results: dict) -> str:
    """Build the cybersecurity analysis prompt for GLM."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = []
    for name, data in scan_results.items():
        # Truncate very long sections to stay within token limits
        truncated = data[:3000] if len(data) > 3000 else data
        sections.append(f"### {name}\n```\n{truncated}\n```")

    scan_body = "\n\n".join(sections)

    prompt = f"""You are an expert macOS cybersecurity analyst. I have run a comprehensive system scan on a Mac computer at {timestamp}. Analyze the following telemetry data for security issues.

## YOUR TASK
1. **Threat Assessment**: Identify any suspicious processes, network connections, launch agents, DNS anomalies, or persistence mechanisms that could indicate malware, spyware, adware, or unauthorized access.
2. **Risk Rating**: Rate overall system risk as 🟢 LOW, 🟡 MEDIUM, 🟠 HIGH, or 🔴 CRITICAL.
3. **Specific Findings**: List each finding with:
   - What was found
   - Why it's suspicious (or safe)
   - Recommended action
4. **Hardening Recommendations**: Suggest concrete steps to improve security posture.
5. **Summary**: A clear executive summary.

Be specific. Reference actual process names, file paths, and port numbers from the data. Don't be generic.

---

## SCAN DATA

{scan_body}
"""
    return prompt


def main():
    console.print(Panel(
        "[bold cyan]🛡️  GLM-5 CyberSec Scanner[/bold cyan]\n"
        "[dim]AI-Powered Mac Security Audit · Powered by GLM[/dim]\n\n"
        "[yellow]This tool collects local system data (processes, network,\n"
        "launch agents, DNS, etc.) and sends it to GLM for analysis.[/yellow]",
        title="🔒 CyberSec",
        border_style="red",
    ))

    # Initialize GLM client
    client = GLM5Client()
    if not client.is_configured():
        console.print(
            "\n[bold red]⚠️  No API key configured![/bold red]\n"
            "Set your API key in [green].env[/green] to enable GLM analysis.\n"
            "The scan will still run and save results locally.\n"
        )

    # Phase 1: Collect data
    console.print("\n[bold white]Phase 1:[/bold white] [cyan]Collecting system telemetry...[/cyan]\n")
    scan_results = run_scan()

    # Show summary table
    table = Table(title="Scan Collection Summary", border_style="cyan")
    table.add_column("Category", style="bold")
    table.add_column("Data Size", justify="right")
    table.add_column("Status", justify="center")
    for name, data in scan_results.items():
        size = f"{len(data):,} chars"
        status = "[green]✓[/green]" if data and "(error" not in data else "[red]✗[/red]"
        table.add_row(name, size, status)
    console.print(table)

    # Save raw scan to file
    scan_file = os.path.join(os.path.dirname(__file__), "cybersec_scan_results.txt")
    with open(scan_file, "w") as f:
        f.write(f"GLM-5 CyberSec Scan — {datetime.datetime.now()}\n")
        f.write("=" * 60 + "\n\n")
        for name, data in scan_results.items():
            f.write(f"### {name}\n{data}\n\n{'─' * 40}\n\n")
    console.print(f"\n[dim]Raw scan saved to:[/dim] [green]{scan_file}[/green]")

    # Phase 2: GLM Analysis
    if not client.is_configured():
        console.print("\n[yellow]Skipping GLM analysis (no API key). Review the raw scan file above.[/yellow]")
        return

    console.print("\n[bold white]Phase 2:[/bold white] [cyan]Sending to GLM for AI threat analysis...[/cyan]\n")

    prompt = build_prompt(scan_results)
    messages = [
        {"role": "system", "content": (
            "You are CyberSec-GLM, an elite macOS cybersecurity threat analyst. "
            "You analyze system telemetry to detect malware, spyware, adware, rootkits, "
            "persistence mechanisms, unauthorized network connections, DNS hijacking, "
            "and misconfigurations. You provide actionable, specific remediation advice. "
            "Format your response in clean Markdown."
        )},
        {"role": "user", "content": prompt}
    ]

    # Try GLM-5.2 first, fall back to free models if unavailable
    model_candidates = [
        "z-ai/glm-5.2",
        client.default_model,
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "poolside/laguna-s-2.1:free",
    ]

    full_response = ""
    console.print("[bold red]🛡️  CyberSec-GLM Analysis:[/bold red]\n")

    for model_id in model_candidates:
        console.print(f"[dim]Trying model: {model_id}...[/dim]")
        full_response = ""
        with Live(Markdown("⏳ Analyzing scan data..."), console=console, refresh_per_second=8) as live:
            try:
                for chunk in client.chat_stream(
                    messages=messages,
                    model=model_id,
                    reasoning_effort="max",
                    max_tokens=4096,
                ):
                    full_response += chunk
                    live.update(Markdown(full_response))
                if full_response:
                    break  # Success, stop trying models
            except Exception as e:
                console.print(f"[dim red]Model {model_id} failed: {e}[/dim red]")
                continue

    if not full_response:
        console.print("\n[bold red]All models failed. Check your API key or try again later.[/bold red]")
        return

    # Save analysis report
    report_file = os.path.join(os.path.dirname(__file__), "cybersec_report.md")
    with open(report_file, "w") as f:
        f.write(f"# GLM-5 CyberSec Report\n")
        f.write(f"**Generated:** {datetime.datetime.now()}\n\n")
        f.write(full_response)
    console.print(f"\n\n[dim]Full report saved to:[/dim] [bold green]{report_file}[/bold green]")
    console.print("[bold cyan]Scan complete. 🛡️[/bold cyan]\n")


if __name__ == "__main__":
    main()
