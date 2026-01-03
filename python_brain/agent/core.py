import re
import json
import logging
import os
from inference.model_loader import ModelManager
from mlx_lm import generate

class Agent:
    def __init__(self, model_manager: ModelManager, tools: dict):
        self.model_manager = model_manager
        self.tools = tools
        self.max_steps = 15
        
    def run(self, user_query: str):
        """Run the ReAct loop"""
        model, tokenizer = self.model_manager.load_router()
        
        system_prompt = self._build_system_prompt()
        history = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_query}]
        
        last_response = ""
        
        for step in range(self.max_steps):
            # 1. Generate Thought/Action
            formatted_prompt = tokenizer.apply_chat_template(history, tokenize=False, add_generation_prompt=True)
            response = generate(model, tokenizer, prompt=formatted_prompt, max_tokens=200, verbose=False)
            last_response = response
            
            # Log for debugging
            logging.info(f"Step {step} Model Output: {response}")
            
            # 2. Parse Action
            action = self._parse_action(response)
            
            if not action:
                # No action, just a response. We are done.
                return response
                
            # 3. Execute Action
            tool_name, tool_args = action
            logging.info(f"Executing {tool_name} with {tool_args}")
            
            if tool_name in self.tools:
                try:
                    result = self.tools[tool_name](*tool_args)
                    observation = f"Observation: {str(result)}"
                except Exception as e:
                    observation = f"Observation: Error executing tool: {e}"
            else:
                observation = f"Observation: Tool '{tool_name}' not found."
                
            # 4. Update History
            history.append({"role": "assistant", "content": response})
            history.append({"role": "user", "content": observation})
            
        return f"{last_response}\n(Agent stopped after {self.max_steps} steps)"

    def _build_system_prompt(self):
        tool_descs = "\n".join([f"- {name}: {func.__doc__}" for name, func in self.tools.items()])
        user = os.environ.get("USER", "unknown")
        home = os.path.expanduser("~")
        
        return f"""You are Localhost, an autonomous developer agent running on macOS.
Current User: {user}
Home Directory: {home}

You have access to the following tools:
{tool_descs}

83: 2. Action: <tool_name>("<arg1>", "<arg2>")
84: 
85: Example:
86: Thought: User wants to find a 'config' file. I'll search for *config* in home.
87: Action: find_files: "*config*", "{home}"
88: 
89: If you have valid results or enough information to answer, simply provide the final answer without an Action.
90: """

    def _parse_action(self, text):
        """Extract tool call from text"""
        # 1. Try "Action: tool: args"
        match = re.search(r"Action:\s*(\w+):\s*(.*)", text, re.IGNORECASE)
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            args = [a.strip().strip('"').strip("'") for a in args_str.split(",")]
            return tool_name, args
            
        # 2. Try "Action: tool(args)" (Function call style)
        match = re.search(r"Action:\s*(\w+)\((.*)\)", text, re.IGNORECASE)
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            # Naive CSV parse
            args = [a.strip().strip('"').strip("'") for a in args_str.split(",")]
            return tool_name, args
            
        return None
