import os
from mlx_lm import load

class ModelManager:
    def __init__(self, cache_dir="~/.localhost/models"):
        self.cache_dir = os.path.expanduser(cache_dir)
        self.models = {}
        
    def load_router(self):
        """Load Qwen-2.5-3B-Instruct (4-bit quantized)"""
        # Ensure directory exists
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
            
        if "router" not in self.models:
            print("Loading model...", file=sys.stderr)
            # Check if local path exists, otherwise try to download (or expect user to have done it)
            # For this script, we'll try to load from huggingface if local fails or is empty,
            # but ideally we point to the local path defined in setup
            
            model_path = os.path.join(self.cache_dir, "qwen-2.5-3b-4bit")
            
            # If explicit path doesn't exist, fall back to HF hub cache or download
            path_to_load = model_path if os.path.exists(model_path) else "mlx-community/Qwen2.5-3B-Instruct-4bit"
            
            model, tokenizer = load(
                path_to_load,
                tokenizer_config={"trust_remote_code": True}
            )
            self.models["router"] = (model, tokenizer)
            
        return self.models["router"]
        
import sys
