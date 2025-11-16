"""
Multi-Agent Email Generation System
Implements: Intent Classifier → Router → Retrieval → Draft → Safety → Human Approval → Send
"""
import os
import warnings
from typing import TypedDict, Literal, Dict, Any, List, Annotated
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.documents import Document
try:
    from langchain_community.vectorstores import Chroma
    # Use new package to avoid deprecation warning
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    Chroma = None
    HuggingFaceEmbeddings = None
try:
    from langfuse.decorators import langfuse_context, observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    # Langfuse optional - create dummy decorators
    LANGFUSE_AVAILABLE = False
    class langfuse_context:
        class span:
            def __init__(self, name): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
    def observe(name=None):
        def decorator(func):
            return func
        return decorator

from rich.console import Console

load_dotenv()
console = Console()

# Initialize Langfuse CallbackHandler for automatic LLM tracing
try:
    from langfuse.langchain import CallbackHandler
    from langfuse import get_client
    LANGFUSE_CALLBACK_AVAILABLE = True
except ImportError:
    LANGFUSE_CALLBACK_AVAILABLE = False
    CallbackHandler = None
    get_client = None

def init_langfuse_handler():
    """Initialize Langfuse and return CallbackHandler if available."""
    if not LANGFUSE_CALLBACK_AVAILABLE:
        return None
    
    try:
        # Verify connection
        langfuse = get_client()
        if langfuse.auth_check():
            console.print("[green]✓ Langfuse connected[/green]")
            return CallbackHandler()
        else:
            console.print("[yellow]Warning:[/yellow] Langfuse authentication failed")
            return None
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Langfuse unavailable: {e}")
        return None

# Initialize components
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

# Initialize search tool (optional)
try:
    search_tool = DuckDuckGoSearchRun()
except Exception as e:
    console.print(f"[yellow]Warning:[/yellow] Search tool unavailable: {e}")
    search_tool = None

# Simple vector store (in-memory for demo)
if CHROMA_AVAILABLE and HuggingFaceEmbeddings:
    try:
        # Suppress deprecation warning
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        EMBEDDINGS_AVAILABLE = True
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Embeddings unavailable: {e}")
        embeddings = None
        EMBEDDINGS_AVAILABLE = False
else:
    embeddings = None
    EMBEDDINGS_AVAILABLE = False
vector_store = None  # Will be initialized in ingest_knowledge

# Email State
class EmailState(TypedDict, total=False):
    user_request: str
    intent: Literal["generate_email", "other"]
    retrieved_context: str
    citations: List[str]
    draft: str
    safety: Dict[str, Any]
    approved_draft: str
    external_info: List[str]
    status: Literal["drafted", "approved", "sent", "cancelled", "rejected"]
    result: str
    session_id: str

@observe()
def node_intent(state: EmailState) -> EmailState:
    """Intent Classifier Agent: Determines if request is for email generation."""
    with langfuse_context.span(name="intent_classifier"):
        request = state.get("user_request", "")
        
        prompt = f"""Classify this user request. Return ONLY "generate_email" or "other":
        
        Request: {request}
        
        Classification:"""
        
        response = llm.invoke(prompt).content.strip().lower()
        intent = "generate_email" if "generate_email" in response or "email" in response else "other"
        
        console.print(f"[cyan]Intent Classifier:[/cyan] {intent}")
        return {"intent": intent}

@observe()
def node_retrieval(state: EmailState) -> EmailState:
    """Retriever Agent: Retrieves relevant organizational knowledge."""
    with langfuse_context.span(name="retriever"):
        request = state.get("user_request", "")
        
        if vector_store:
            # RAG retrieval
            docs = vector_store.similarity_search(request, k=3)
            context = "\n\n".join([doc.page_content for doc in docs])
            citations = [doc.metadata.get("source", "unknown") for doc in docs]
        else:
            # Fallback: simple context
            context = "Organization: TechCorp. Focus: Innovation and customer satisfaction."
            citations = ["org_knowledge"]
        
        console.print(f"[cyan]Retriever:[/cyan] Retrieved {len(citations)} documents")
        return {"retrieved_context": context, "citations": citations}

@observe()
def node_external_search(state: EmailState) -> EmailState:
    """External Tool Agent: Searches web for additional information."""
    with langfuse_context.span(name="external_search"):
        request = state.get("user_request", "")
        
        # Extract key terms for search
        if search_tool:
            search_query = f"{request} latest information"
            try:
                results = search_tool.invoke(search_query)
                external_info = [results] if results else []
            except Exception as e:
                console.print(f"[yellow]Search error:[/yellow] {e}")
                external_info = []
        else:
            external_info = []
        
        console.print(f"[cyan]External Search:[/cyan] Found {len(external_info)} results")
        return {"external_info": external_info}

@observe()
def node_draft(state: EmailState) -> EmailState:
    """Drafter Agent: Creates email draft using context."""
    with langfuse_context.span(name="drafter"):
        request = state.get("user_request", "")
        context = state.get("retrieved_context", "")
        external = state.get("external_info", [])
        
        external_text = "\n".join(external) if external else "No external information available."
        
        prompt = f"""Write a professional executive-style email based on this request:

Request: {request}

Organizational Context:
{context}

External Information:
{external_text}

Include a "Subject:" line. Make it professional and concise."""
        
        draft = llm.invoke(prompt).content
        
        # Extract subject if present
        if "Subject:" in draft:
            parts = draft.split("Subject:", 1)
            if len(parts) > 1:
                subject_line = parts[1].split("\n")[0].strip()
                body = "\n".join(parts[1].split("\n")[1:]).strip()
                draft = f"Subject: {subject_line}\n\n{body}"
        
        console.print(f"[cyan]Drafter:[/cyan] Draft created ({len(draft)} chars)")
        return {"draft": draft, "status": "drafted"}

@observe()
def node_safety(state: EmailState) -> EmailState:
    """Safety Reviewer Agent: Checks draft for issues."""
    with langfuse_context.span(name="safety_reviewer"):
        draft = state.get("draft", "")
        
        prompt = f"""Review this email draft for safety, compliance, and professionalism.
        Return a JSON object with:
        - "safe": true/false
        - "notes": brief explanation
        - "risk_level": "low"/"medium"/"high"
        
        Draft:
        {draft}
        
        Review:"""
        
        response = llm.invoke(prompt).content
        
        # Simple parsing (in production, use structured output)
        safe = "true" in response.lower() or "safe" in response.lower()
        risk_level = "high" if "high" in response.lower() else "medium" if "medium" in response.lower() else "low"
        notes = response[:200] if len(response) > 200 else response
        
        safety_result = {
            "safe": safe,
            "risk_level": risk_level,
            "notes": notes
        }
        
        console.print(f"[cyan]Safety Reviewer:[/cyan] {risk_level} risk, safe={safe}")
        return {"safety": safety_result}

@observe()
def node_human(state: EmailState) -> Command:
    """Human-in-the-Loop: Approval node with interrupt."""
    with langfuse_context.span(name="human_approval"):
        draft = state.get("draft", "")
        safety = state.get("safety", {})
        
        payload = {
            "question": "Approve this email?",
            "suggested_subject": draft.split("\n")[0] if draft else "No subject",
            "suggested_body": draft,
            "safety_notes": safety.get("notes", ""),
            "risk_level": safety.get("risk_level", "unknown"),
            "instructions": "Return True/False or {'approve': bool, 'subject': str, 'body': str}."
        }
        
        decision = interrupt(payload)
        
        approve = False
        final_draft = draft
        
        if isinstance(decision, dict):
            approve = bool(decision.get("approve", False))
            if decision.get("body"):
                final_draft = decision.get("body", final_draft)
        else:
            approve = bool(decision)
        
        state["approved_draft"] = final_draft if approve else ""
        state["status"] = "approved" if approve else "rejected"
        
        return Command(goto="send" if approve else "draft")

@observe()
def node_send(state: EmailState) -> EmailState:
    """Send Agent: Finalizes and logs the email."""
    with langfuse_context.span(name="send_email"):
        draft = state.get("approved_draft") or state.get("draft", "")
        
        state["status"] = "sent"
        state["result"] = f"Email sent successfully. Content:\n{draft[:200]}..."
        
        console.print(f"[green]Email sent![/green]")
        return state

def route_from_intent(state: EmailState) -> str:
    """Router: Dynamically chooses next step based on intent."""
    intent = state.get("intent", "other")
    if intent == "generate_email":
        return "retrieval"
    return END

def route_after_retrieval(state: EmailState) -> str:
    """Router: Decide if external search is needed."""
    request = state.get("user_request", "").lower()
    # Simple heuristic: search if request mentions "latest", "recent", "current"
    if any(word in request for word in ["latest", "recent", "current", "news", "update"]):
        return "external_search"
    return "draft"

def route_after_safety(state: EmailState) -> str:
    """Router: Check if safety review passed."""
    safety = state.get("safety", {})
    if safety.get("safe", True):
        return "human"
    # If unsafe, go back to draft
    return "draft"

def build_graph():
    """Build the complete multi-agent graph."""
    sg = StateGraph(EmailState)
    
    # Add nodes
    sg.add_node("intent", node_intent)
    sg.add_node("retrieval", node_retrieval)
    sg.add_node("external_search", node_external_search)
    sg.add_node("draft", node_draft)
    sg.add_node("safety", node_safety)
    sg.add_node("human", node_human)
    sg.add_node("send", node_send)
    
    # Entry point
    sg.set_entry_point("intent")
    
    # Routing edges
    sg.add_conditional_edges("intent", route_from_intent, {"retrieval": "retrieval", END: END})
    sg.add_conditional_edges("retrieval", route_after_retrieval, {"external_search": "external_search", "draft": "draft"})
    sg.add_edge("external_search", "draft")
    sg.add_edge("draft", "safety")
    sg.add_conditional_edges("safety", route_after_safety, {"human": "human", "draft": "draft"})
    sg.add_edge("send", END)
    
    # Persistence - use SqliteSaver properly
    db_path = os.getenv("STATE_DB", "state.sqlite")
    try:
        # SqliteSaver needs to be used as context manager or with connection
        import sqlite3
        conn = sqlite3.connect(db_path, check_same_thread=False)
        memory = SqliteSaver(conn)
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] Using MemorySaver instead: {e}")
        from langgraph.checkpoint.memory import MemorySaver
        memory = MemorySaver()
    
    return sg.compile(checkpointer=memory)

def ingest_knowledge():
    """Initialize vector store with organizational knowledge."""
    global vector_store
    
    # Sample organizational knowledge
    org_docs = [
        Document(
            page_content="TechCorp is a leading technology company focused on innovation. Our mission is to deliver cutting-edge solutions that drive customer success.",
            metadata={"source": "org_overview.md"}
        ),
        Document(
            page_content="Our Q4 priorities include cost optimization, customer retention, and product innovation. InsightX is our flagship product for data analytics.",
            metadata={"source": "q4_priorities.md"}
        ),
        Document(
            page_content="Executive communication should be clear, concise, and action-oriented. Always include specific metrics and timelines when possible.",
            metadata={"source": "communication_guidelines.md"}
        ),
    ]
    
    if embeddings and Chroma:
        try:
            vector_store = Chroma.from_documents(
                documents=org_docs,
                embedding=embeddings,
                persist_directory="./chroma_db"
            )
            console.print("[green]✓ Vector store initialized[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not initialize vector store: {e}")
            vector_store = None
    else:
        console.print("[yellow]Warning:[/yellow] ChromaDB not available, using simple context retrieval")
        vector_store = None

