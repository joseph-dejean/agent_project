# 🚀 Multi-Agent Email Generation System

A complete multi-agent system for generating executive-style emails with context retrieval, safety review, and human-in-the-loop approval. Built with LangGraph, LangChain, and Gradio.

## ✨ Features

- **🤖 Multi-Agent Architecture**: 6 specialized agents (Intent Classifier, Retriever, External Search, Drafter, Safety Reviewer, Send)
- **🔄 Dynamic Routing**: Intelligent routing decisions based on workflow state
- **📚 RAG (Retrieval Augmented Generation)**: Vector database for organizational knowledge retrieval
- **🌐 External Tools**: DuckDuckGo web search integration for real-time information
- **👤 Human-in-the-Loop**: Interrupt/resume pattern for approval and editing
- **💾 Persistence**: SqliteSaver for session memory and state recovery
- **📊 Observability**: Langfuse integration for complete workflow tracing
- **🎨 Beautiful UI**: Gradio web interface for easy interaction

## 🏗️ Architecture

```
User Request → Intent Classifier → Router → Retrieval → [External Search] → Draft → Safety → Human Approval → Send
```

### System Flow

1. **Intent Classifier**: Determines if request is for email generation
2. **Router**: Dynamically routes to retrieval or external search
3. **Retriever**: Searches organizational knowledge base (vector DB)
4. **External Search**: Searches web for latest information (if needed)
5. **Drafter**: Creates professional email draft
6. **Safety Reviewer**: Checks for compliance and safety issues
7. **Human Approval**: Pauses for review/editing
8. **Send**: Finalizes and logs the email

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or 3.12 (Python 3.13 may have dependency issues)
- OpenAI API key
- (Optional) Langfuse account for observability

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd agentic_project
   ```

2. **Create virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/Mac
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Copy `env.example` to `.env` and fill in your keys:
   ```bash
   # Windows
   copy env.example .env
   
   # Linux/Mac
   cp env.example .env
   ```
   
   Then edit `.env` with your actual keys:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   
   # Optional: Langfuse for observability
   LANGFUSE_PUBLIC_KEY=pk_...
   LANGFUSE_SECRET_KEY=sk_...
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

### Running the Application

#### Option 1: Web UI (Recommended)

**Windows:**
```bash
# Double-click run_ui.bat
# Or run:
python ui.py
```

**Linux/Mac:**
```bash
python ui.py
```

Then open http://localhost:7860 in your browser.

#### Option 2: CLI Interface

**Windows:**
```bash
# Double-click run.bat
# Or run:
python demo.py
```

**Linux/Mac:**
```bash
python demo.py
```

## 📖 Usage Example

1. **Start the UI**: Run `python ui.py`
2. **Enter request**: "Draft an executive email to the COO about Q4 priorities and cost optimization"
3. **System processes**: All agents work through the workflow
4. **Review & Approve**: Edit the draft if needed, then approve
5. **Done**: Email is finalized and logged

## 🛠️ Project Structure

```
agentic_project/
├── graph.py              # Multi-agent graph definition
├── demo.py               # CLI interface
├── ui.py                 # Gradio web UI
├── requirements.txt      # Python dependencies
├── run.bat              # Windows CLI launcher
├── run_ui.bat           # Windows UI launcher
├── PROJECT_REPORT.md    # Detailed project documentation
└── README.md            # This file
```

## 🔧 Configuration

### Required
- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Optional
- `LANGFUSE_PUBLIC_KEY`: Langfuse public key for observability
- `LANGFUSE_SECRET_KEY`: Langfuse secret key
- `LANGFUSE_HOST`: Langfuse host URL (default: https://cloud.langfuse.com)

## 🐛 Troubleshooting

### ChromaDB Installation Issues
If ChromaDB fails to install (common on Python 3.13 or without Rust), the system will automatically fall back to simple context retrieval. The system remains fully functional.

### Port Already in Use
If port 7860 is in use, the UI will automatically find the next available port (7861, 7862, etc.) and display it.

### Import Errors
```bash
pip install -r requirements.txt --upgrade
```

### Langfuse Connection
If Langfuse keys are not configured, the system will work without observability. No errors will occur.

## 📊 Evaluation Criteria

This implementation meets all project requirements:

- ✅ **Multi-agent architecture**: 6 specialized agents
- ✅ **Dynamic routing**: 3 routing functions
- ✅ **Vector DB retrieval**: ChromaDB with citations
- ✅ **External search**: DuckDuckGo integration
- ✅ **Human-in-the-loop**: Interrupt/resume with editing
- ✅ **Persistence**: SqliteSaver with session recovery
- ✅ **Langfuse monitoring**: Complete tracing and spans
- ✅ **Extensibility**: Modular design, easy to extend

## 🧪 Testing

Run the demo to test the system:
```bash
python demo.py
```

Or use the web UI:
```bash
python ui.py
```

## 📝 License

This project is provided as-is for educational purposes.

## 🤝 Contributing

Feel free to submit issues or pull requests!

## 📧 Support

For questions or issues, please open an issue on GitHub.

---

**Built with**: LangGraph, LangChain, Gradio, OpenAI, Langfuse
