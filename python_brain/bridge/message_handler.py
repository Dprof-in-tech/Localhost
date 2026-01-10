from inference.model_loader import ModelManager
from tools.filesystem import FileSystemTool
from rag.indexer import Indexer
from agent.core import Agent

# Global singletons
model_manager = ModelManager()
fs_tool = FileSystemTool()
indexer = Indexer()

def clear_context():
    """Clear the current project context and RAG index."""
    try:
        fs_tool.set_project_root(None)
        indexer.clear_index()
        return "Context Cleared. Memory reset."
    except Exception as e:
        return f"Error clearing context: {e}"

# Define available tools
tools = {
    "find_files": fs_tool.find_files,
    "read_file": fs_tool.read_file,
    "read_multiple_files": fs_tool.read_multiple_files,
    "write_file": fs_tool.write_file,
    "replace_in_file": fs_tool.replace_file_content,
    "clear_context": clear_context
    # "index_directory": indexer.index_directory # DISABLED: Too heavy for autonomous use
}

def get_agent_context():
    if fs_tool.sandbox.project_root:
        return str(fs_tool.sandbox.project_root)
    return None

agent = Agent(model_manager, tools, context_provider=get_agent_context)

def handle_message(message):
    msg_type = message.get("type")
    payload = message.get("payload", {})
    
    if msg_type == "query":
        text = payload.get("text", "")
        
        # 1. Legacy Commands (keep for speed)
        if text.startswith("/"):
            if text == "/reset":
                 return {"status": "success", "response": clear_context()}
            if text.startswith("/ls "):
                return {"status": "success", "response": str(fs_tool.list_directory(text[4:].strip()))}
            if text.startswith("/read "):
                return {"status": "success", "response": str(fs_tool.read_file(text[6:].strip()))}
            if text.startswith("/find "):
                parts = text[6:].split(" ", 1)
                return {"status": "success", "response": str(fs_tool.find_files(parts[0], parts[1] if len(parts)>1 else "~"))}
            if text.startswith("/index "):
                return {"status": "success", "response": str(indexer.index_directory(text[7:].strip()))}
            if text.startswith("/project "):
                try:
                    path = text[9:].strip()
                    new_root = fs_tool.set_project_root(path)
                    return {"status": "success", "response": f"🔒 Sandbox Active. Project root set to: {new_root}"}
                except Exception as e:
                    return {"status": "error", "message": f"Error setting project root: {e}"}
            if text == "/approve":
                 return {"status": "success", "response": fs_tool.approve_pending_edits()}

        # 2. Agentic Loop (NLP)
        try:
            response_text = agent.run(text)
            return {"status": "success", "response": response_text}
        
        except Exception as e:
            return {"status": "error", "message": f"Agent error: {str(e)}"}
            
    if msg_type == "get_context":
        if fs_tool.sandbox.project_root:
            return {"status": "success", "response": f"📂 {fs_tool.sandbox.project_root.name}"}
        else:
            return {"status": "success", "response": "Localhost Ready"}

    return {"status": "error", "message": "Unknown message type"}
