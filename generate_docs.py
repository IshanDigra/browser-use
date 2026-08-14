import os
import ast

def extract_signatures(filepath):
    """Extracts function and class signatures from a python file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        signatures = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                signatures.append(f"def {node.name}(...): ...")
            elif isinstance(node, ast.ClassDef):
                signatures.append(f"class {node.name}: ...")

        if signatures:
            return "\n".join(signatures)
        else:
            return "# No classes or functions defined."
    except Exception as e:
        return f"# Could not parse Python file: {e}"

def generate_markdown(output_file="project_codebase.md"):
    exclude_dirs = {'.git', '.github', 'node_modules', '__pycache__', 'venv', '.venv', 'build', 'dist', '.pytest_cache', 'htmlcov'}

    # Files to explicitly ignore
    exclude_files = {'project_codebase.md', 'generate_docs.py', 'package-lock.json', 'poetry.lock', 'uv.lock'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write("# Summarized Project Codebase\n\n")
        outfile.write("This document contains a summarized view of the source code and configuration files for the project. For Python files, it shows class and function signatures.\n\n")
        outfile.write("## Table of Contents\n\n")

        all_files = []
        for root, dirs, files in os.walk('.'):
            # Exclude unwanted directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

            for file in sorted(files):
                if file in exclude_files:
                    continue
                # Skip compiled files or media files
                ext = os.path.splitext(file)[1]
                if ext.lower() in ['.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.mp4', '.webm', '.zip', '.tar', '.gz', '.lock']:
                    continue

                filepath = os.path.join(root, file)
                # Normalize path
                filepath = filepath.replace('./', '', 1) if filepath.startswith('./') else filepath
                all_files.append(filepath)

        # Generate Table of Contents
        for filepath in sorted(all_files):
            outfile.write(f"- [{filepath}](#{filepath.replace('.', '').replace('/', '').lower()})\n")

        outfile.write("\n---\n\n")

        # Generate Content
        for filepath in sorted(all_files):
            try:
                outfile.write(f"## File: `{filepath}`\n\n")
                outfile.write(f"<a name=\"{filepath.replace('.', '').replace('/', '').lower()}\"></a>\n\n")

                ext = os.path.splitext(filepath)[1]
                lang = ""
                if ext == '.py': lang = 'python'
                elif ext == '.sh': lang = 'bash'
                elif ext in ['.yaml', '.yml']: lang = 'yaml'
                elif ext == '.json': lang = 'json'
                elif ext == '.toml': lang = 'toml'
                elif ext == '.md': lang = 'markdown'
                elif ext == '.html': lang = 'html'
                elif ext == '.js': lang = 'javascript'
                elif ext == '.css': lang = 'css'

                if ext == '.py':
                    content = extract_signatures(filepath)
                else:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()

                    # If it's a very large non-python file, just show the first 50 lines to keep it summarized.
                    if content.count('\n') > 100:
                        lines = content.split('\n')
                        content = "\n".join(lines[:100]) + "\n\n... (truncated for brevity) ..."

                outfile.write(f"```{lang}\n")
                outfile.write(content)
                if not content.endswith('\n'):
                    outfile.write("\n")
                outfile.write(f"```\n\n")
            except Exception as e:
                print(f"Skipped {filepath}: {e}")

if __name__ == "__main__":
    generate_markdown()
