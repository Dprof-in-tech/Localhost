
import json
import re
import os

class ContentFormatter:
    """
    Robust formatter to clean up Agent output before writing to disk.
    Prevents 'minified' text/json and ensures consistent style.
    """
    
    @staticmethod
    def format(content: str, file_path: str) -> str:
        """
        Auto-format content based on file extension.
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        # 1. JSON Formatting
        if ext == '.json':
            try:
                # 0. Pre-Cleanup: If we see literal \n but it failed or looks sketchy, simple-fix it.
                # This handles cases where the Agent/Parser passed literal "\n" strings.
                if '\\n' in content:
                     # Be careful not to break valid escapes inside strings, but for structure it's confusing.
                     # If the file is ONE LINE and has \n, it's definitely broken.
                     if '\n' not in content: 
                         content = content.replace('\\n', '\n').replace('\\t', '\t')

                # Parse to ensure validity and re-dump with indent
                parsed = json.loads(content)
                return json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"
            except json.JSONDecodeError:
                # Fallback: aggressive repair
                try:
                     # Maybe it was just the newlines making it invalid syntax (e.g. {\n "key"})
                     fixed_content = content.replace('\\n', '\n').replace('\\t', '\t')
                     parsed = json.loads(fixed_content)
                     return json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"
                except:
                    # If still invalid, strict 'do no harm'
                    return content
                
        # 2. Markdown Formatting
        elif ext == '.md':
            return ContentFormatter._format_markdown(content)
            
        # 3. Python/Code Formatting (Basic)
        elif ext in ['.py', '.swift', '.js', '.ts', '.sh']:
            # Ensure final newline
            if not content.endswith('\n'):
                content += "\n"
            return content
            
        return content

    @staticmethod
    def _format_markdown(content: str) -> str:
        """
        Fix common LLM markdown issues like missing blank lines before headers.
        """
        # 0. Aggressive Repair (Same as JSON):
        # If we see literal \n but NO real newlines, the Parser likely failed.
        if '\\n' in content and '\n' not in content:
            content = content.replace('\\n', '\n').replace('\\t', '\t')

        # Ensure newlines are Unix style
        content = content.replace('\r\n', '\n')
        
        # 1. Ensure empty line before Headers (#)
        # Look for [Line of text]\n[# Header] and insert extra newline
        # But NOT if it's the start of the file.
        # Regex: (?<=[^\n])\n(?=#+ ) -> Match newline preceded by non-newline, followed by Header
        content = re.sub(r'([^\n])\n(#+ )', r'\1\n\n\2', content)
        
        # 2. Ensure empty line before Lists (-)
        # Be careful not to break nested lists or code blocks.
        # Safe heuristic: Top level lists usually need spacing from paragraphs.
        # content = re.sub(r'([^\n])\n(- )', r'\1\n\n\2', content) # Too risky for code blocks
        
        # 3. Ensure final newline
        if content and not content.endswith('\n'):
            content += "\n"
            
        return content
