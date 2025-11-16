"""
Complete Multi-Agent Email Generation System Demo
Implements all project requirements with working demo
"""
import os
import uuid
from dotenv import load_dotenv
from graph import build_graph, ingest_knowledge, EmailState
from langgraph.types import Command
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()

def handle_interrupt(interrupt_data, app, thread_config):
    """Handle human-in-the-loop interrupt."""
    if not interrupt_data:
        return None
    
    interrupt_obj = interrupt_data[0] if isinstance(interrupt_data, list) else interrupt_data
    payload = interrupt_obj.value if hasattr(interrupt_obj, 'value') else interrupt_data
    
    console.print("\n" + "="*70, style="bold yellow")
    console.print("[bold yellow]🤖 HUMAN APPROVAL REQUIRED[/bold yellow]")
    console.print("="*70)
    
    if isinstance(payload, dict):
        # Display safety info
        if payload.get("risk_level"):
            risk_color = "red" if payload["risk_level"] == "high" else "yellow" if payload["risk_level"] == "medium" else "green"
            console.print(f"\n[bold {risk_color}]Risk Level:[/bold {risk_color}] {payload['risk_level'].upper()}")
        
        if payload.get("safety_notes"):
            console.print(Panel(payload["safety_notes"], title="[bold]Safety Review[/bold]", border_style="yellow"))
        
        # Display email
        console.print(Panel(payload.get("suggested_subject", ""), title="[bold]Subject[/bold]", border_style="cyan"))
        console.print(Panel(payload.get("suggested_body", ""), title="[bold]Email Body[/bold]", border_style="blue"))
        
        console.print(f"\n[dim]Instructions:[/dim] {payload.get('instructions', '')}")
    
    console.print("\n" + "-"*70)
    choice = input("\n[bold]Approve?[/bold] (y=approve, n=reject, e=edit): ").strip().lower()
    
    if choice == "e":
        console.print("\n[bold]Enter edited draft (finish with 'END' on new line):[/bold]")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        edited_body = "\n".join(lines)
        return Command(resume={"approve": True, "body": edited_body})
    elif choice == "y":
        return Command(resume=True)
    else:
        return Command(resume=False)

def display_state_summary(state):
    """Display a summary of the current state."""
    table = Table(title="Workflow State", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    if state.get("intent"):
        table.add_row("Intent Classifier", state["intent"])
    if state.get("retrieved_context"):
        table.add_row("Retrieval", f"✓ {len(state.get('citations', []))} docs")
    if state.get("external_info"):
        table.add_row("External Search", f"✓ {len(state['external_info'])} results")
    if state.get("draft"):
        table.add_row("Draft", f"✓ {len(state['draft'])} chars")
    if state.get("safety"):
        table.add_row("Safety Review", f"✓ {state['safety'].get('risk_level', 'unknown')} risk")
    if state.get("status"):
        table.add_row("Final Status", state["status"])
    
    console.print(table)

def main():
    """Main demo function."""
    console.print(Panel.fit(
        "[bold green]🚀 Multi-Agent Email Generation System[/bold green]\n"
        "[dim]Intent → Retrieval → External Search → Draft → Safety → Human Approval → Send[/dim]",
        border_style="green"
    ))
    
    # Initialize knowledge base
    console.print("\n[cyan]Initializing knowledge base...[/cyan]")
    ingest_knowledge()
    
    # Build graph
    console.print("[cyan]Building agent graph...[/cyan]")
    app = build_graph()
    console.print("[green]✓ Graph ready[/green]\n")
    
    # Get user input
    console.print("[bold]Enter your email request:[/bold]")
    user_request = input("> ").strip() or "Draft an executive email to the COO about Q4 priorities and how InsightX helps cost optimization."
    
    # Generate session ID
    session_id = str(uuid.uuid4())[:8]
    console.print(f"\n[dim]Session ID:[/dim] {session_id}\n")
    
    # Initialize Langfuse handler for tracing
    from graph import init_langfuse_handler
    langfuse_handler = init_langfuse_handler()
    
    # Initial state
    initial_state = EmailState(
        user_request=user_request,
        session_id=session_id
    )
    
    # Configure with Langfuse callback if available
    thread_config = {
        "configurable": {"thread_id": session_id},
        "callbacks": [langfuse_handler] if langfuse_handler else []
    }
    
    console.print("[bold cyan]Starting workflow...[/bold cyan]\n")
    console.print("-" * 70)
    
    # First invocation
    result = app.invoke(initial_state, config=thread_config)
    
    # Handle interrupt
    if "__interrupt__" in result:
        decision = handle_interrupt(result["__interrupt__"], app, thread_config)
        if decision:
            # Resume with same config (includes Langfuse callback)
            final_result = app.invoke(decision, config=thread_config)
            
            console.print("\n" + "="*70)
            console.print("[bold green]✅ Workflow Complete![/bold green]")
            console.print("="*70)
            
            display_state_summary(final_result)
            
            if final_result.get("result"):
                console.print(Panel(final_result["result"], title="[bold]Result[/bold]", border_style="green"))
            
            if final_result.get("citations"):
                console.print(f"\n[dim]Citations:[/dim] {', '.join(final_result['citations'])}")
        else:
            console.print("\n[bold red]❌ Workflow cancelled[/bold red]")
    else:
        console.print("\n[bold green]✅ Workflow Complete![/bold green]")
        display_state_summary(result)
    
    console.print(f"\n[dim]State persisted in state.sqlite, session: {session_id}[/dim]")
    if langfuse_handler:
        console.print("[bold green]📊 View traces in Langfuse dashboard:[/bold green] https://cloud.langfuse.com")
    else:
        console.print("[dim]Langfuse not configured - add keys to .env to see traces[/dim]")
    console.print()

if __name__ == "__main__":
    main()
