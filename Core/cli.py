"""
GLM-5 Interactive Terminal CLI Application
Features real-time token streaming, live markdown formatting, model switching, and reasoning effort controls.
"""

import sys
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.prompt import Prompt
from glm5_client import GLM5Client

console = Console()


def print_banner():
    banner_text = """
[bold cyan]GLM-5 Series Interactive Terminal CLI[/bold cyan]
[dim]Powered by Zhipu AI / Z.ai | Models: GLM-5.2, GLM-5.1, GLM-5[/dim]

[bold yellow]Available Commands:[/bold yellow]
  [green]/model <name>[/green]   - Switch active model (e.g. glm-5.2, glm-5.1, glm-5)
  [green]/effort <level>[/green] - Change reasoning effort ('max' or 'high')
  [green]/clear[/green]          - Clear chat history
  [green]/exit[/green]           - Exit the application
"""
    console.print(Panel(banner_text, title="🚀 GLM-5 Terminal", border_style="cyan"))


def main():
    print_banner()

    client = GLM5Client()
    current_model = client.default_model
    current_effort = os.getenv("GLM_REASONING_EFFORT", "max")
    messages = [
        {"role": "system", "content": "You are GLM-5, an elite AI coding and reasoning assistant."}
    ]

    if not client.is_configured():
        console.print(
            "[bold red]⚠️  No API key configured![/bold red]\n"
            "Please set your [bold yellow]ZHIPU_API_KEY[/bold yellow] in [green].env[/green] or environment variables.\n"
            "Example: [bold white]export ZHIPU_API_KEY='your_api_key'[/bold white]\n"
        )

    while True:
        try:
            status_line = f"[dim]Model: [cyan]{current_model}[/cyan] | Effort: [magenta]{current_effort}[/magenta][/dim]"
            console.print(status_line)
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()

            if not user_input:
                continue

            if user_input.lower() in ["/exit", "exit", "quit", ":q"]:
                console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]")
                break

            if user_input.lower() == "/clear":
                messages = [{"role": "system", "content": "You are GLM-5, an elite AI coding and reasoning assistant."}]
                console.clear()
                print_banner()
                console.print("[bold yellow]Chat history cleared.[/bold yellow]\n")
                continue

            if user_input.lower().startswith("/model"):
                parts = user_input.split()
                if len(parts) > 1:
                    current_model = parts[1]
                    console.print(f"[bold yellow]Switched model to:[/bold yellow] [cyan]{current_model}[/cyan]\n")
                else:
                    console.print(f"[dim]Current model: {current_model}. Usage: /model glm-5.2[/dim]\n")
                continue

            if user_input.lower().startswith("/effort"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1].lower() in ["max", "high"]:
                    current_effort = parts[1].lower()
                    console.print(f"[bold yellow]Switched reasoning effort to:[/bold yellow] [magenta]{current_effort}[/magenta]\n")
                else:
                    console.print("[dim]Usage: /effort max OR /effort high[/dim]\n")
                continue

            if not client.is_configured():
                console.print("[red]Cannot send request: ZHIPU_API_KEY is not configured.[/red]\n")
                continue

            messages.append({"role": "user", "content": user_input})

            console.print(f"\n[bold cyan]GLM-5 ({current_model}):[/bold cyan]")
            full_response = ""

            with Live(Markdown("Thinking..."), console=console, refresh_per_second=10) as live:
                try:
                    for chunk in client.chat_stream(
                        messages=messages,
                        model=current_model,
                        reasoning_effort=current_effort
                    ):
                        full_response += chunk
                        live.update(Markdown(full_response))
                except Exception as e:
                    live.update(f"[bold red]Error during stream generation: {e}[/bold red]")

            messages.append({"role": "assistant", "content": full_response})
            console.print()

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold cyan]Session terminated. Goodbye! 👋[/bold cyan]")
            break


if __name__ == "__main__":
    main()
