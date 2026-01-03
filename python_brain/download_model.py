from huggingface_hub import snapshot_download
import os

model_id = "mlx-community/Qwen2.5-3B-Instruct-4bit"
local_dir = os.path.expanduser("~/.localhost/models/qwen-2.5-3b-4bit")

print(f"🧠 Downloading {model_id} to {local_dir}...")
snapshot_download(
    repo_id=model_id,
    local_dir=local_dir,
    local_dir_use_symlinks=False
)
print("✅ Download complete!")
