# Multi-Agent Email Generation System

A production-ready system that generates professional emails using multiple AI agents working together. Each agent has a specific role - from understanding your request to retrieving relevant information, drafting the email, checking for safety issues, and getting your approval before sending.

Built with LangGraph for orchestration, LangChain for agent capabilities, and Gradio for the web interface.

## What This System Does

Instead of a single AI generating emails, this system uses **6 specialized agents** that work together:

1. **Intent Classifier** - Understands what you want
2. **Retriever** - Finds relevant information from your knowledge base
3. **External Search** - Searches the web for latest information when needed
4. **Drafter** - Writes the actual email
5. **Safety Reviewer** - Checks for compliance and potential issues
6. **Send Agent** - Finalizes everything

The system also includes **dynamic routing** - it decides which agents to use based on your request. For example, if you ask for "latest news", it will automatically use the web search agent.

## How It Works

The system uses a graph-based workflow where each agent passes control to the next based on the current state. Here's the flow:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  Intent Classifier   │
                │  (Agent 1)           │
                │  "Is this an email   │
                │   generation request?"│
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   Router 1            │
                │  (Decision Point)     │
                └──────────┬───────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
    ┌───────────────┐           ┌──────────────┐
    │   Retriever   │           │     END      │
    │  (Agent 2)    │           │  (if not     │
    │  Searches     │           │  email req)   │
    │  knowledge    │           └──────────────┘
    │  base (RAG)   │
    └───────┬───────┘
            │
            ▼
    ┌──────────────────────┐
    │   Router 2           │
    │  (Decision Point)   │
    │  "Need web search?" │
    └──────────┬───────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌──────────────┐   ┌──────────────┐
│ External     │   │   Drafter    │
│ Search       │   │  (Agent 4)   │
│ (Agent 3)    │   │  Creates     │
│ Web search   │   │  email draft │
│ for latest   │   │              │
│ info         │   │              │
└──────┬───────┘   └──────┬───────┘
       │                  │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │ Safety Reviewer   │
       │ (Agent 5)        │
       │ Checks for        │
       │ compliance/risks  │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │   Router 3        │
       │  (Decision Point) │
       │  "Safe to send?"  │
       └────────┬───────────┘
                │
                ▼
       ┌──────────────────┐
       │ Human Approval   │
       │ (Interrupt)      │
       │ [PAUSES HERE]    │
       │ You review/edit  │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐
       │   Send Agent     │
       │  (Agent 6)       │
       │  Finalizes &     │
       │  logs email      │
       └──────────────────┘
                │
                ▼
       ┌──────────────────┐
       │  Persistence     │
       │  (SQLite file)   │
       │  + Langfuse      │
       │  (if configured) │
       └──────────────────┘
```

### Key Components

**6 Specialized Agents:**
1. **Intent Classifier** - Determines if the request is for email generation
2. **Retriever** - Searches your organizational knowledge base using RAG (vector search)
3. **External Search** - Searches the web via DuckDuckGo when current information is needed
4. **Drafter** - Generates the actual email content
5. **Safety Reviewer** - Checks for compliance, safety issues, and professionalism
6. **Send Agent** - Finalizes and logs the completed email

**3 Router Functions:**
- **Router 1** - After intent classification, decides if we should proceed or end
- **Router 2** - After retrieval, decides if external web search is needed (based on keywords like "latest", "recent", "current")
- **Router 3** - After safety review, decides if we need human approval or can proceed

**Dynamic Routing:**
The system makes intelligent decisions at each router. For example:
- If you say "latest trends", Router 2 will route to External Search
- If safety review finds high risk, Router 3 will require human approval
- If everything looks good, it can skip directly to sending

**Persistence Layer:**
- SQLite file stores session state automatically
- Langfuse (optional) provides full observability and tracing

## Getting Started

### What You Need

- Python 3.11 or 3.12 (3.13 works but some dependencies might need extra setup)
- An OpenAI API key (get one at https://platform.openai.com/api-keys)
- Optional: Langfuse account if you want to see detailed traces (free at https://cloud.langfuse.com)

### Installation Steps

1. **Get the code**
   ```bash
   git clone https://github.com/joseph-dejean/agentic_project.git
   cd agentic_project
   ```

2. **Set up Python environment**
   ```bash
   # Create virtual environment
   python -m venv .venv
   
   # Activate it
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```

3. **Install everything**
   ```bash
   pip install -r requirements.txt
   ```
   
   This might take a few minutes. If ChromaDB fails to install (common on some systems), don't worry - the system will work without it, just without vector search.

4. **Configure your API keys**
   
   Copy the example file and add your keys:
   ```bash
   # Windows
   copy env.example .env
   
   # Linux/Mac  
   cp env.example .env
   ```
   
   Then open `.env` in a text editor and add your OpenAI key:
   ```env
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
   
   Langfuse is optional - if you want it, add those keys too. The system works fine without it.

### Running the System

You have two options:

**Option 1: Web Interface (Easiest)**

Just run:
```bash
python ui.py
```

Then open your browser to http://localhost:7860. You'll see a nice interface where you can:
- Enter your email request
- See the generated email
- Edit it if needed
- Approve or reject

**Option 2: Command Line**

If you prefer the terminal:
```bash
python demo.py
```

You'll get a nice formatted output showing each agent's work, and it will pause for your approval when needed.

**Windows Users**: You can also just double-click `run_ui.bat` or `run.bat` - they do the same thing.

## Testing the System

Here's how to test it works:

1. **Start the UI**: `python ui.py`
2. **Try a simple request**: "Write an email to my manager about completing the quarterly report"
3. **Watch it work**: You'll see each agent doing its job
4. **Review the draft**: The system will pause and ask for your approval
5. **Approve or edit**: You can approve as-is, edit it, or reject it

**Example requests to try:**
- "Draft an email to the team about the project deadline"
- "Write a professional email to a client thanking them for their business"
- "Create an email about the latest industry trends" (this will trigger web search)

The system automatically saves your session state, so if something goes wrong, you can recover it.

## Project Files

The main files you'll interact with:

- `graph.py` - Where all the agents are defined and connected
- `demo.py` - Command-line interface
- `ui.py` - Web interface (Gradio)
- `requirements.txt` - All Python packages needed
- `env.example` - Template for your `.env` file
- `PROJECT_REPORT.md` - Detailed technical documentation

## About SQLite (No Server Needed!)

You might notice there's no SQLite server setup - that's because **SQLite doesn't need a server**. It's a file-based database, so it just creates a `state.sqlite` file in your project folder automatically when you run the system.

This file stores:
- Session state (so you can recover if something crashes)
- Workflow history
- Task logs

You don't need to do anything - it just works. The file is automatically created on first run and ignored by git (so it won't be pushed to GitHub).

## Troubleshooting

**ChromaDB won't install?**
- That's okay! The system will use a simpler retrieval method. Everything still works, you just won't have vector search. This is common on Windows or Python 3.13.

**Port 7860 already in use?**
- The UI will automatically try port 7861, 7862, etc. Just check the terminal output for the actual URL.

**"Module not found" errors?**
- Make sure your virtual environment is activated
- Try: `pip install -r requirements.txt --upgrade`

**Langfuse not connecting?**
- That's fine - it's optional. The system works perfectly without it. If you want it, just make sure your keys in `.env` are correct.

**Database errors?**
- SQLite creates the database file automatically. If you get errors, try deleting `state.sqlite` and running again (you'll lose saved sessions, but it will recreate everything).

## What's Included

This system implements all the required features:

- ✅ **6 specialized agents** working together
- ✅ **Smart routing** that decides which agents to use
- ✅ **Knowledge retrieval** from your organizational data (with vector search if ChromaDB works)
- ✅ **Web search** integration for real-time information
- ✅ **Human approval** step where you can review and edit before sending
- ✅ **Session persistence** - your work is saved automatically
- ✅ **Full observability** with Langfuse (if configured)

## How to Test It

The easiest way to test:

1. Run `python ui.py`
2. Open http://localhost:7860
3. Enter: "Write an email to my team about the project update"
4. Watch the agents work
5. Review and approve the draft

You should see:
- Intent classification happening
- Knowledge being retrieved
- Email being drafted
- Safety review
- Your approval step

Everything is logged and traceable (if you set up Langfuse).

## Technical Details

For more technical information, architecture decisions, and implementation details, see `PROJECT_REPORT.md`.

---

Built with LangGraph, LangChain, Gradio, and OpenAI.
