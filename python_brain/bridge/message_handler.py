from inference.model_loader import ModelManager
from tools.filesystem import FileSystemTool
from rag.indexer import Indexer
from agent.core import Agent

# Global singletons
model_manager = ModelManager()
fs_tool = FileSystemTool()
indexer = Indexer()

# Define available tools
tools = {
    "find_files": fs_tool.find_files,
    "read_file": fs_tool.read_file,
    "index_directory": indexer.index_directory
}

agent = Agent(model_manager, tools)

def handle_message(message):
    msg_type = message.get("type")
    payload = message.get("payload", {})
    
    if msg_type == "query":
        text = payload.get("text", "")
        
        # 1. Legacy Commands (keep for speed)
        if text.startswith("/"):
            if text.startswith("/ls "):
                return {"status": "success", "response": str(fs_tool.list_directory(text[4:].strip()))}
            if text.startswith("/read "):
                return {"status": "success", "response": str(fs_tool.read_file(text[6:].strip()))}
            if text.startswith("/find "):
                parts = text[6:].split(" ", 1)
                return {"status": "success", "response": str(fs_tool.find_files(parts[0], parts[1] if len(parts)>1 else "~"))}
            if text.startswith("/index "):
                return {"status": "success", "response": str(indexer.index_directory(text[7:].strip()))}
        
        # 2. Agentic Loop (NLP)
        try:
            response_text = agent.run(text)
            return {"status": "success", "response": response_text}
        
        except Exception as e:
            return {"status": "error", "message": f"Agent error: {str(e)}"}
            
    return {"status": "error", "message": "Unknown message type"}

