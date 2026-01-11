# Localhost: The Native AI Agent for macOS

Localhost is a powerful, local-first AI agent that lives on your Mac. It combines a native Swift UI with a Python-based LLM brain to provide a seamless, private, and intelligent assistant that knows your code and files.

**Zero data leaves your machine.** Everything runs locally on Apple Silicon (M1/M2/M3).

<img width="1024" height="434" alt="image" src="https://github.com/user-attachments/assets/46a4a4c7-6b21-4be9-808e-a7a67ebb6bd2" />


## ✨ Features

- **🧠 Local LLM Brain**: Runs `Qwen3-4B-Instruct` (4-bit quantized) using `mlx-lm` for high performance on Apple Silicon.
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

### 📦 Installation

#### 👩‍💻 For Users (No Coding Required)

**Download:** [Localhost_v0.1.zip](release/Localhost_v0.1.zip)

1.  **Unzip** the file.
2.  **Run the Installer**:
    Double-click `Install.command` to set up the AI Brain (Python environment & models).
    *Tip: If it asks for permission, Right-Click > Open.*
3.  **Install the App**:
    Drag `Localhost.app` into your **Applications** folder.

#### 👷‍♂️ For Developers (Build from Source)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/localhost.git
    cd localhost
    ```

2.  **Run the Setup Script:**
    This script creates the Python virtual environment and installs dependencies (MLX, Transformers, LanceDB), and downloads the model.
    ```bash
    # We use the same script as the release
    chmod +x release/Install.command
    ./release/Install.command
    ```

3.  **Build in Xcode:**
    *   Open `LocalhostApp/LocalhostApp.xcodeproj`.
    *   **CRITICAL**: Go to target settings -> Signing & Capabilities. Ensure `LocalhostApp/Resources/Localhost.entitlements` is selected in "Code Signing Entitlements" (or manually add `LocalhostApp/Resources/Localhost.entitlements` to Build Settings). This disables the Sandbox so the app can see your files.
    *   Build and Run (`Cmd+R`).

### 🔐 Setup & Permissions (Important)

Localhost interacts deeply with your system to be helpful. You **must** grant these permissions on first run:

1.  **Accessibility**:
    *   Required for the Global Hotkey (`Cmd+Shift+.`) and reading your active window context.
    *   *System Settings > Privacy & Security > Accessibility*.
2.  **Full Disk Access**:
    *   **CRITICAL**: Required for the Agent to search and index your projects (`/mdfind`). Without this, the Agent is blind to files outside its own folder.
    *   *System Settings > Privacy & Security > Full Disk Access*.

### 🚀 Usage

1.  **Activate**: Press `Cmd+Shift+.` (Period) to toggle the floating bar.
2.  **Chat**: Type any question (e.g., "Write a Python script to parse JSON").
3.  **Index Code**: Type `/index /path/to/my/project` to verify your code.
4.  **Agent Search**: Type natural requests like "Find the readme in my documents" or "Read the config file".

## 🤖 Commands

| Command | Description |
| :--- | :--- |
| `/project <path>` | Switch the active project context (sandbox root). |
| `/index .` | Index the current project for RAG (Search). |
| `/find <pattern> <path>` | Manually search for files (or just ask the Agent to do it!). |
| `/read <path>` | Read a specific file's content. |
| `/ls <path>` | List directory contents. |
| `/quit` | Quit the background app. |
| `/reset` | Clear conversation memory and index. |

## 🚀 New Feature: Draft Mode

Localhost now includes **Draft Mode**, a new feature that allows you to propose file edits without immediately applying them.

- **Draft Mode** enables safe, reversible editing of files.
- You can propose changes to a file, review them, and apply them with a single command.
- Supports both full file replacement and partial edits (search & replace).
- Safe for experimentation and code review.

### How to Use Draft Mode

1. Type `/draft <path>` to initiate a draft edit.
2. Enter your changes in the draft buffer.
3. Review the proposed changes.
4. Apply with `/approve` to finalize the edit.

## 🏗️ Project Structure

*   `LocalhostApp/`: Swift source code for the macOS application.
*   `python_brain/`: Python source code for the LLM, RAG, and Agent logic.
    *   `agent/`: The ReAct agent core.
    *   `bridge/`: Message handling between Swift and Python.
    *   `inference/`: Model loading and generation.
    *   `rag/`: Vector database and indexing logic.
    *   `tools/`: File system tools (`find`, `read`, `ls`).
*   `release/`: Installer scripts and packaged binaries.

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
