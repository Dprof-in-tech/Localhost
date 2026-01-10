import lancedb
import os
import glob
from pathlib import Path
import pyarrow as pa
import logging
from rag.embedder import Embedder

class Indexer:
    def __init__(self, db_path="~/.localhost/vectordb"):
        self.db_path = os.path.expanduser(db_path)
        os.makedirs(self.db_path, exist_ok=True)
        self.db = lancedb.connect(self.db_path)
        self.embedder = Embedder()
        
    def index_directory(self, path: str):
        """Index a directory recursively"""
        root_path = Path(path).expanduser()
        if not root_path.exists():
            return {"error": f"Path not found: {path}"}
            
        # Recursive glob for text-ish files
        # Limit extensions for now to avoid binary noise
        extensions = ["*.py", "*.swift", "*.md", "*.txt", "*.js", "*.ts", "*.json"]
        files = []
        for ext in extensions:
            files.extend(root_path.rglob(ext))
            
        # Ignore patterns
        IGNORE_DIRS = {
            "node_modules", ".git", "venv", ".venv", "__pycache__", 
            "dist", "build", ".next", ".vscode", ".idea", "Pods"
        }
        
        filtered_files = []
        for file in files:
            # Check if any part of the path is in IGNORE_DIRS
            if any(part in IGNORE_DIRS for part in file.parts):
                continue
            filtered_files.append(file)
            
        files = filtered_files
            
        data = []
        logging.info(f"Indexing {len(files)} files in {path}...")
        
        for file in files:
            try:
                content = file.read_text(encoding='utf-8')
                if not content.strip():
                    continue
                    
                # Simple chunking (e.g. 500 characters overlap)
                # Better approach: Tree-sitter (Phase 3)
                chunks = self._chunk_text(content)
                
                for i, chunk in enumerate(chunks):
                    vector = self.embedder.embed_text(chunk)
                    data.append({
                        "path": str(file),
                        "chunk_id": i,
                        "text": chunk,
                        "vector": vector
                    })
            except Exception as e:
                logging.warning(f"Skipping {file}: {e}")
                continue
                
        if not data:
            return {"status": "empty", "message": "No text files found to index."}
            
        # Create or Overwrite table
        # Tbl name based on path hash or fixed 'codebase' for MVP
        tbl = self.db.create_table("codebase", data=data, mode="overwrite")
        return {"status": "success", "message": f"Indexed {len(data)} chunks from {len(files)} files."}

    def clear_index(self):
        """Drop the current index"""
        try:
            self.db.drop_table("codebase")
            return {"status": "success", "message": "Index cleared."}
        except:
            return {"status": "success", "message": "Index already empty."}

        
    def search(self, query: str, limit=5):
        """Semantic search"""
        try:
            tbl = self.db.open_table("codebase")
            query_vector = self.embedder.embed_text(query)
            
            results = tbl.search(query_vector).limit(limit).to_list()
            return results
        except Exception:
            return []
            
    def _chunk_text(self, text, chunk_size=1000, overlap=100):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start += chunk_size - overlap
        return chunks
