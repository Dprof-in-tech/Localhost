import re
import json
import logging
import os
from inference.model_loader import ModelManager
from mlx_lm import generate

class Agent:
    def __init__(self, model_manager: ModelManager, tools: dict, context_provider=None):
        self.model_manager = model_manager
        self.tools = tools
        self.context_provider = context_provider
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
            
            logging.info(f"Step {step}: Starting Generation...")
            response = generate(model, tokenizer, prompt=formatted_prompt, max_tokens=2048, verbose=False)
            logging.info(f"Step {step}: Generation Complete. Length: {len(response)}")
            
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
                    logging.info(f"Tool Execution Complete. Result length: {len(str(result))}")
                    observation = f"Observation: {str(result)}"
                except Exception as e:
                    logging.error(f"Tool Execution Failed: {e}")
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
        
        project_context = "Not Set (Ask user to set /project)"
        if self.context_provider:
             try:
                 ctx = self.context_provider()
                 if ctx: project_context = ctx
             except: pass
        
        return f"""You are Localhost, an autonomous developer agent running on macOS.
Current User: {user}
Home Directory: {home}
Current Project Root: {project_context}

You have access to the following tools:
{tool_descs}
You have access to the following tools:
{tool_descs}

STYLE GUIDELINES:
1. NO EMOJIS. Your output must be strictly professional and text-only.
2. CONCISE. Do not waste tokens.

FORMATTING STANDARDS (System Requirement):
1. **File Edits MUST use proper formatting**:
   - Markdown: Use proper spacing, headers, and newlines. NEVER write a whole file as a single line.
   - JSON: Use indentation (2 or 4 spaces) and newlines.
   - Python/Swift: Respect existing indentation and style.
2. **Prohibition**: Do NOT minify text files. Do NOT dump long strings without newlines.

STRATEGY GUIDELINES:
1. SEARCHING:
   - If user query is vague, extract specific keywords.
   - If 0 results, retry with spelling correction.

2. READING:
   - [DIR] -> list_directory. [FILE] -> read_file.
   - **CRITICAL**: If you do not know the EXACT path, use `find_files` first. Do NOT guess paths.
   - Example: Don't read "config.py". Run `find_files("config.py", "{home}")` then read the result.

3. WRITING / EDITING (Draft Mode):
   - **CRITICAL**: Before writing, perform "Silent Red Team" analysis.
   - **MANDATORY**: You MUST include the returned DIFF in your final response.
   - **PREFER**: `replace_in_file` for partial logic updates (saves tokens).
   - Use: Action: replace_in_file("/path/to/real/file", "OLD_BLOCK", "NEW_BLOCK")
   - Use: Action: write_file("/path/to/real/file", "FULL_NEW_CONTENT") 
   - **CRITICAL**: Do NOT use "/path/to/file". Use the ACTUAL absolute path (e.g., "{home}/Documents/MyProject/README.md").
   - **CRITICAL / MANDATORY**: If tool output says "DRAFT CREATED", you are FORBIDDEN from saying "Applied" or "Finalized".
   - You MUST say: "Draft created. Pending confirmation."
   - You MUST tell the user: "Please type `/approve` to apply this change."
   - IMPORTANT: If you get "Write Denied", ask user to set project root: "/project <path>"

4. DEBUGGING / ERROR ANALYSIS:
   - When the user provides an error/stack trace, output a structured diagnosis:
     ### Error Diagnosis
     **1. Full Stack Trace:** (Expose the raw relevant trace)
     **2. Why:** (Root cause analysis)
     **3. Where:** (File:Line)
     **4. Impact:** (What feature is broken?)
     **5. Fix:** (The solution logic + code draft)
   - Use 'read_file' on the stack trace paths to confirm the error line.
   - Use the "Silent Red Team" loop before proposing the Fix.

To use a tool, you MUST use one of these formats:
1. Action: <tool_name>: <arg1>, <arg2>
2. Action: <tool_name>("<arg1>", "<arg2>")

Example:
Thought: User wants to find 'config'. I will search for it.
Action: find_files: "*config*", "{home}"

If you have valid results, simply provide the final answer.
"""

    def _parse_action(self, text):
        """Extract tool call from text"""
        import csv
        from io import StringIO

        # 1. Cleaner Regex for "Action: tool: args"
        # Handle potential "Action: Action: tool" stutter
        cleaned_text = text.strip()
        if cleaned_text.lower().startswith("action: action:"):
            cleaned_text = cleaned_text[8:].strip() # Remove first "Action:"
            
        match = re.search(r"Action:\s*(\w+):\s*(.*)", cleaned_text, re.IGNORECASE)
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            
            # If tool_name is still "Action" (triple stutter?), recursive fix or hard fail
            if tool_name.lower() == "action":
                # Try to find next colon
                sub_match = re.search(r"Action:\s*(\w+):\s*(.*)", args_str, re.IGNORECASE)
                if sub_match:
                    tool_name = sub_match.group(1)
                    args_str = sub_match.group(2)
            
            # Clean args_str for CSV parser
            # LLM output often uses \" for quotes, but CSV expects ""
            args_str_csv = args_str.replace('\\"', '""')
            
            # Use CSV parser
            try:
                reader = csv.reader(StringIO(args_str_csv), quotechar='"', skipinitialspace=True)
                args = next(reader)
                # FIX: Unescape characters like \n, \t that the CSV parser treats literally
                # NOTE: Do NOT use unicode_escape, it mangles Unicode chars like ✨
                # FIX: Unescape characters like \n, \t that the CSV parser treats literally
                # Note: If arg looks like a list "[...]", parse it as JSON
                cleaned_args = []
                for arg in args:
                    arg_str = arg.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
                    if arg_str.strip().startswith("[") and arg_str.strip().endswith("]"):
                        try:
                            # Try to parse list string as JSON or literal
                            import ast
                            parsed_list = ast.literal_eval(arg_str)
                            if isinstance(parsed_list, list):
                                cleaned_args.append(parsed_list)
                            else:
                                cleaned_args.append(arg_str)
                        except:
                             cleaned_args.append(arg_str)
                    else:
                        cleaned_args.append(arg_str)
                
                return tool_name, cleaned_args
            except:
                # Fallback: Naive split is dangerous. Try regex for quoted strings.
                # Regex to match: "string 1", "string 2" or string1, string2
                quoted_args = re.findall(r'(?:[^,"]|"(?:\\.|[^"])*")+', args_str)
                if quoted_args:
                     # Also unescape regex results
                    cleaned_args = []
                    for arg in quoted_args:
                        a = arg.strip().strip('"')
                        cleaned_args.append(a.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"'))
                    return tool_name, cleaned_args
                return tool_name, [a.strip() for a in args_str.split(",")]
            
        # 2. Try "Action: tool(args)" (Function call style)
        match = re.search(r"Action:\s*(\w+)\((.*)\)", cleaned_text, re.IGNORECASE | re.DOTALL)
        if match:
            tool_name = match.group(1)
            args_str = match.group(2)
            
            if tool_name.lower() == "action":
                 pass

            try:
                # Clean args_str for CSV parser
                args_str_csv = args_str.replace('\\"', '""')
                reader = csv.reader(StringIO(args_str_csv), quotechar='"', skipinitialspace=True)
                args = next(reader)
                return tool_name, args
            except:
                 # Fallback: Regex for quoted arguments in parens
                 quoted_args = re.findall(r'(?:[^,"]|"(?:\\.|[^"])*")+', args_str)
                 if quoted_args:
                     return tool_name, [arg.strip().strip('"') for arg in quoted_args]
                 return tool_name, [a.strip().strip('"').strip("'") for a in args_str.split(",")]
            
        return None
