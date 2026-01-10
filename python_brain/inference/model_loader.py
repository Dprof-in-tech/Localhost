import os
import sys
from mlx_lm import load

class ModelManager:
    def __init__(self, cache_dir="~/.localhost/models/qwen3-4b-2507-4bit"):
        self.model_path = os.path.expanduser(cache_dir)
        self.models = {}
        
    def load_router(self, model_id="mlx-community/Qwen3-4B-Instruct-2507-4bit"):
        """Load Qwen3-4B-Instruct (4-bit quantized, version 2507)"""
        if "router" not in self.models:
            print("Loading model...", file=sys.stderr)
            
            # Use local path if it exists, otherwise fallback to explicit load
            path_to_load = self.model_path if os.path.exists(self.model_path) else model_id
            
            try:
                model, tokenizer = load(
                    path_to_load,
                    tokenizer_config={"trust_remote_code": True}
                )
                self.models["router"] = (model, tokenizer)
            except Exception as e:
                print(f"Error loading model: {e}", file=sys.stderr)
                # Fallback or re-raise depending on policy
                raise e
            
        return self.models["router"]
