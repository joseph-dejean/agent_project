"""
Gradio UI for Multi-Agent Email Generation System
Beautiful web interface for the email generation workflow
"""
import os
import uuid
import gradio as gr
from dotenv import load_dotenv
from graph import build_graph, ingest_knowledge, EmailState, init_langfuse_handler
from langgraph.types import Command

load_dotenv()

# Global state
app = None
knowledge_initialized = False

def initialize_system():
    """Initialize the knowledge base and graph (only once)."""
    global app, knowledge_initialized
    
    if not knowledge_initialized:
        yield "🔄 Initializing knowledge base...", ""
        ingest_knowledge()
        yield "🔄 Building agent graph...", ""
        app = build_graph()
        knowledge_initialized = True
        yield "✅ System ready!", ""
    else:
        yield "✅ System already initialized!", ""

# Store session state for interrupt handling
session_store = {}

def run_workflow(user_request, progress=None):
    """Run the complete workflow."""
    global app, session_store
    
    if not app:
        return "❌ System not initialized. Please wait...", "", "", ""
    
    if not user_request.strip():
        return "❌ Please enter an email request", "", "", ""
    
    # Initialize Langfuse
    langfuse_handler = init_langfuse_handler()
    
    # Generate session ID
    session_id = str(uuid.uuid4())[:8]
    
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
    
    # Store session config for later resume
    session_store[session_id] = thread_config
    
    # Run workflow
    result = app.invoke(initial_state, config=thread_config)
    
    # Check for interrupt (human approval needed)
    if "__interrupt__" in result:
        # Extract interrupt data
        interrupt_data = result["__interrupt__"]
        interrupt_obj = interrupt_data[0] if isinstance(interrupt_data, list) else interrupt_data
        payload = interrupt_obj.value if hasattr(interrupt_obj, 'value') else interrupt_data
        
        if isinstance(payload, dict):
            subject = payload.get("suggested_subject", "No subject")
            body = payload.get("suggested_body", "")
            risk_level = payload.get("risk_level", "unknown")
            safety_notes = payload.get("safety_notes", "")
            
            # Return for human approval
            status = f"⏸️ **HUMAN APPROVAL REQUIRED**\n\n**Risk Level:** {risk_level.upper()}\n\n**Safety Review:**\n{safety_notes}\n\n**Session ID:** {session_id}"
            return status, subject, body, session_id  # Return session_id as string
    
    # Workflow completed without interrupt
    final_draft = result.get("approved_draft") or result.get("draft", "")
    status = f"✅ **Workflow Complete!**\n\n**Status:** {result.get('status', 'completed')}\n\n**Session ID:** {session_id}"
    
    if langfuse_handler:
        status += "\n\n📊 View traces: https://cloud.langfuse.com"
    
    return status, "", final_draft, ""  # Empty string means no approval needed

def handle_approval(decision, edited_subject, edited_body, session_id_state):
    """Handle human approval decision."""
    global app, session_store
    
    if not app or not session_id_state:
        return "❌ No approval pending. Please generate an email first.", ""
    
    session_id = session_id_state
    thread_config = session_store.get(session_id)
    
    if not thread_config:
        return "❌ Session expired. Please generate a new email.", ""
    
    if decision == "approve":
        # Approve as-is
        command = Command(resume=True)
    elif decision == "approve_edited":
        # Approve with edits
        full_draft = f"{edited_subject}\n\n{edited_body}" if edited_subject else edited_body
        command = Command(resume={"approve": True, "body": full_draft})
    else:
        # Reject
        return "❌ Email rejected by user", ""
    
    # Resume workflow
    result = app.invoke(command, config=thread_config)
    
    final_draft = result.get("approved_draft") or result.get("draft", "")
    status = f"✅ **Email Sent!**\n\n**Status:** {result.get('status', 'sent')}\n\n**Session ID:** {session_id}"
    
    langfuse_handler = init_langfuse_handler()
    if langfuse_handler:
        status += "\n\n📊 View traces: https://cloud.langfuse.com"
    
    # Clean up session
    if session_id in session_store:
        del session_store[session_id]
    
    return status, final_draft

# Create Gradio interface
with gr.Blocks(title="Multi-Agent Email Generator", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🚀 Multi-Agent Email Generation System
    
    **Complete workflow:** Intent → Retrieval → External Search → Draft → Safety → Human Approval → Send
    
    Enter your email request below and the system will generate a professional email using multiple AI agents.
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            user_input = gr.Textbox(
                label="Email Request",
                placeholder="e.g., Draft an executive email to the COO about Q4 priorities and cost optimization",
                lines=3
            )
            generate_btn = gr.Button("🚀 Generate Email", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            init_btn = gr.Button("⚙️ Initialize System", variant="secondary")
            init_status = gr.Textbox(label="System Status", interactive=False)
    
    with gr.Row():
        status_output = gr.Markdown(label="Workflow Status")
    
    with gr.Row():
        with gr.Column():
            subject_output = gr.Textbox(label="Email Subject", interactive=True, visible=True)
            body_output = gr.Textbox(label="Email Body", lines=10, interactive=True, visible=True)
        
        with gr.Column():
            session_id_hidden = gr.State(value="")
            approval_decision = gr.Radio(
                choices=["approve", "approve_edited", "reject"],
                label="Approval Decision",
                value="approve_edited"
            )
            approve_btn = gr.Button("✅ Submit Decision", variant="primary", visible=False)
            final_output = gr.Markdown(label="Final Result", visible=True)
    
    # Event handlers
    init_btn.click(
        fn=initialize_system,
        outputs=[init_status, status_output]
    )
    
    def run_and_update(user_req):
        status, subj, body, session_id = run_workflow(user_req)
        # Show approve button if session_id is not empty (approval needed)
        show_approve = bool(session_id)
        return status, subj, body, session_id, gr.update(visible=show_approve)
    
    generate_btn.click(
        fn=run_and_update,
        inputs=[user_input],
        outputs=[status_output, subject_output, body_output, session_id_hidden, approve_btn]
    )
    
    approve_btn.click(
        fn=handle_approval,
        inputs=[approval_decision, subject_output, body_output, session_id_hidden],
        outputs=[status_output, final_output]
    )
    
    # Auto-initialize on load
    demo.load(
        fn=initialize_system,
        outputs=[init_status, status_output]
    )

if __name__ == "__main__":
    import socket
    
    def find_free_port(start_port=7860, max_attempts=10):
        """Find a free port starting from start_port."""
        for i in range(max_attempts):
            port = start_port + i
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                continue
        return None  # No free port found
    
    # Try to find a free port
    port = find_free_port(7860)
    if port is None:
        print("❌ Could not find an available port. Please close other applications.")
        exit(1)
    
    if port != 7860:
        print(f"⚠️  Port 7860 is in use. Using port {port} instead.")
        print(f"🌐 Open http://localhost:{port} in your browser")
    
    demo.launch(server_name="0.0.0.0", server_port=port, share=False)

