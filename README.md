# Localhost: The Native AI Agent for macOS

Localhost is a powerful, local-first AI agent that lives on your Mac. It combines a native Swift UI with a Python-based LLM brain to provide a seamless, private, and intelligent assistant that knows your code and files.

**Zero data leaves your machine.** Everything runs locally on Apple Silicon (M1/M2/M3).

![Localhost Banner](https://via.placeholder.com/800x200?text=Localhost+AI+Agent)

## ✨ Features

- **🧠 Local LLM Brain**: Runs `Qwen-2.5-3B-Instruct` (4-bit quantized) using `mlx-lm` for high performance on Apple Silicon.
- **🔦 Neural Spotlight UI**: A beautiful, floating search bar triggered by `Cmd+Shift+.` that sits above your apps.
- **📚 RAG (Retrieval Augmented Generation)**: Index your local folders (`/index <path>`) to let the AI answer questions about your codebase.
- **🕵️‍♂️ Agentic Capabilities**: An autonomous "Agent" that can reason and use tools:
    - **Find Files**: "Find the triac controller file"
    - **Read Code**: "Explain what XPCBridge.swift does"
    - **List Directories**: "Show me files in the python_brain folder"
- **⚡️ Native Bridge**: Seamless IPC communication between Swift (UI) and Python (Logic) using standard I/O.

## 🛠️ Architecture

*   **Host App (Swift)**: Manages the UI, global hotkey, accessibility permissions, and the life-cycle of the Python subprocess.
*   **Brain (Python)**: Handles model inference, vector database (LanceDB), and agentic reasoning (ReAct loop).

## 🚀 Getting Started

### Prerequisites

*   macOS 12.0+ (Apple Silicon M1/M2/M3 recommended)
*   Xcode 14+
*   Python 3.10+

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/localhost.git
    cd localhost
    ```

2.  **Run the Setup Script:**
    This script creates the Python virtual environment, installs dependencies (MLX, Transformers, LanceDB), and downloads the model.
    ```bash
    chmod +x setup_env.sh
    ./setup_env.sh
    ```

3.  **Build in Xcode:**
    *   Open `LocalhostApp/LocalhostApp.xcodeproj`.
    *   Ensure the Signing Team is set in project settings.
    *   Build and Run (`Cmd+R`).

### Usage

1.  **Activate**: Press `Cmd+Shift+.` (Period) to toggle the floating bar.
2.  **Chat**: Type any question (e.g., "Write a Python script to parse JSON").
3.  **Index Code**: Type `/index /path/to/my/project` to verify your code.
4.  **Agent Search**: Type natural requests like "Find the readme in my documents" or "Read the config file".

## 🤖 Commands

| Command | Description |
| :--- | :--- |
| `/index <path>` | Indexes a directory for RAG (Retrieval Augmented Generation). |
| `/find <pattern> <path>` | Manually search for files (or just ask the Agent to do it!). |
| `/read <path>` | Read a specific file's content. |
| `/ls <path>` | List directory contents. |

## 🏗️ Project Structure

*   `LocalhostApp/`: Swift source code for the macOS application.
*   `python_brain/`: Python source code for the LLM, RAG, and Agent logic.
    *   `agent/`: The ReAct agent core.
    *   `bridge/`: Message handling between Swift and Python.
    *   `inference/`: Model loading and generation.
    *   `rag/`: Vector database and indexing logic.
    *   `tools/`: File system tools (`find`, `read`, `ls`).

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
