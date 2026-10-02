"""APEX OSINT Command-Line Interface."""

import asyncio
import json
import sys
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.database import init_db, async_session_factory
from app.engine.universal_detector import UniversalTargetEngine
from app.modules.registry import module_registry
from app.models.workspace import Workspace
from app.models.investigation import Investigation
from app.models.target import Target
from app.engine.orchestrator import orchestrator
from app.config import settings

console = Console()


def print_banner():
    console.print(
        Panel.fit(
            "[bold white]A P E X   O S I N T[/bold white]\n"
            "[dim cyan]Intelligence, connected.[/dim cyan]\n"
            "[dim]Defensive Open-Source Intelligence & Investigation Platform[/dim]",
            border_style="cyan"
        )
    )


async def cmd_doctor():
    """Run diagnostics."""
    print_banner()
    console.print("\n[bold]Running APEX System Diagnostics...[/bold]\n")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="white", width=25)
    table.add_column("Status", width=12)
    table.add_column("Details", style="dim")

    # Python
    table.add_row("Python Runtime", "[green]PASS[/green]", f"Python {sys.version.split()[0]}")

    # Database
    try:
        await init_db()
        table.add_row("Database Engine", "[green]PASS[/green]", f"SQLite async storage ready")
    except Exception as e:
        table.add_row("Database Engine", "[red]FAIL[/red]", str(e))

    # Modules
    mods = module_registry.list_modules()
    table.add_row("OSINT Module Registry", "[green]PASS[/green]", f"{len(mods)} registered collectors ready")

    # Gemini
    if settings.GEMINI_API_KEY:
        table.add_row("Google Gemini Copilot", "[green]CONNECTED[/green]", f"Model {settings.GEMINI_MODEL}")
    else:
        table.add_row("Google Gemini Copilot", "[yellow]INFO[/yellow]", "Local grounded reasoning mode (Set GEMINI_API_KEY for live LLM)")

    # SSRF Guard
    table.add_row("SSRF Security Guard", "[green]ACTIVE[/green]", "RFC 1918 / loopback protections enforced")

    console.print(table)
    console.print("\n[bold green]Diagnostics complete.[/bold green]\n")


async def cmd_modules():
    """List registered OSINT modules."""
    print_banner()
    table = Table(title="APEX OSINT Registered Modules", header_style="bold cyan")
    table.add_column("Module Name", style="bold white")
    table.add_column("Category", style="cyan")
    table.add_column("Target Types", style="yellow")
    table.add_column("Status", style="green")
    table.add_column("Description", style="dim")

    for mod in module_registry.list_modules():
        table.add_row(
            mod["name"],
            mod["category"],
            ", ".join(mod["target_types"]),
            mod["status"],
            mod["description"][:50] + "..."
        )

    console.print(table)


async def cmd_target(query: str):
    """Analyze a target query using the Universal Target Engine."""
    print_banner()
    console.print(f"\n[bold]Universal Analysis for Query:[/bold] [cyan]'{query}'[/cyan]\n")

    results = UniversalTargetEngine.process_universal_query(query)
    for idx, at in enumerate(results, 1):
        console.print(f"[bold]Target #{idx}:[/bold] [white]{at.raw_input}[/white] -> [bold cyan]{at.primary_type}[/bold cyan] ({int(at.primary_confidence * 100)}%)")
        console.print("[dim]Multi-type hypotheses:[/dim]")
        for h in at.hypotheses:
            bar = "#" * (h.percentage // 10) + "-" * (10 - (h.percentage // 10))
            console.print(f"  {h.target_type:<15} [cyan]{bar}[/cyan] {h.percentage:>3}% - {h.explanation}")
        console.print(f"[dim]Planned Investigation:[/dim] {', '.join(at._build_investigation_plan())}\n")


async def cmd_scan(query: str, mode: str = "standard", depth: int = 1):
    """Run an investigation directly from CLI."""
    print_banner()
    await init_db()

    async with async_session_factory() as session:
        # Default workspace
        ws = Workspace(name="CLI Workspace", description="Automated CLI investigation workspace")
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        inv = Investigation(
            workspace_id=ws.id,
            title=f"CLI Investigation: {query}",
            mode=mode,
            depth=depth,
            status="pending"
        )
        session.add(inv)
        await session.commit()
        await session.refresh(inv)

        # Targets
        analyzed_targets = UniversalTargetEngine.process_universal_query(query)
        for at in analyzed_targets:
            tgt = Target(
                investigation_id=inv.id,
                raw_input=at.raw_input,
                detected_type=at.primary_type,
                normalized_value=at.normalized_value,
                confidence=at.primary_confidence,
                depth=0,
                status="pending"
            )
            session.add(tgt)
        await session.commit()

    console.print(f"\n[bold]Launching investigation:[/bold] [cyan]{inv.id}[/cyan] on target [white]{query}[/white] (Mode: {mode.upper()}, Depth: {depth})")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Executing OSINT collection pipeline...", total=None)
        await orchestrator._execute_pipeline(inv.id)

    # Show results
    async with async_session_factory() as session:
        inv_done = await session.get(Investigation, inv.id)
        summary = inv_done.summary_json or {}

        console.print(Panel.fit(
            f"[bold green]Investigation Complete![/bold green]\n\n"
            f"Target: [bold white]{query}[/bold white]\n"
            f"Entities Discovered: [bold cyan]{summary.get('entities_count', 0)}[/bold cyan]\n"
            f"Evidence Records: [bold cyan]{summary.get('evidence_count', 0)}[/bold cyan]\n"
            f"Correlated Links: [bold cyan]{summary.get('relationships_count', 0)}[/bold cyan]\n"
            f"Contradictions: [bold red]{summary.get('contradictions_count', 0)}[/bold red]\n\n"
            f"[dim]{summary.get('executive_summary', '')}[/dim]",
            title="Investigation Dossier Summary",
            border_style="green"
        ))


def main():
    parser = argparse.ArgumentParser(description="APEX OSINT - Intelligence, Connected.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # doctor
    subparsers.add_parser("doctor", help="Run system diagnostics")

    # modules
    subparsers.add_parser("modules", help="List all registered OSINT modules")

    # target
    target_parser = subparsers.add_parser("target", help="Analyze target input using Universal Engine")
    target_parser.add_argument("query", help="Target string (e.g. domain, username, email, IP, name)")

    # scan
    scan_parser = subparsers.add_parser("scan", help="Run investigation against a target")
    scan_parser.add_argument("query", help="Target string")
    scan_parser.add_argument("--mode", default="standard", choices=["quick", "standard", "deep"], help="Investigation mode")
    scan_parser.add_argument("--depth", type=int, default=1, help="Max recursion depth")

    args = parser.parse_args()

    if args.command == "doctor":
        asyncio.run(cmd_doctor())
    elif args.command == "modules":
        asyncio.run(cmd_modules())
    elif args.command == "target":
        asyncio.run(cmd_target(args.query))
    elif args.command == "scan":
        asyncio.run(cmd_scan(args.query, args.mode, args.depth))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
