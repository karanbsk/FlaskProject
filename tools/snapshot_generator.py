import os
from datetime import datetime

# === CONFIGURATION ===
# PROJECT_ROOT points to the FlaskProject root directory dynamically
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "PROJECT_SNAPSHOT.md")

# Folders or files to exclude from folder structure                                                   
EXCLUDE_FOLDERS = {'.git', 'flask_venv', '__pycache__', '.env'}
EXCLUDE_FILES = {'.gitignore'}
EXCLUDE_CODE_SNIPPETS_IN_FOLDERS = {'.github', 'tools'} # Skip code snippets here
# Allowed file extensions for code snippets                                           
ALLOWED_EXTENSIONS = {'.py', '.html', '.css', '.js', '.json', '.md', '.txt'}

# === HELPER FUNCTION TO GENERATE FOLDER STRUCTURE ===
def generate_folder_structure(root_dir, exclude=None):
    exclude = exclude or set()
    tree_lines = []

    for root, dirs, files in os.walk(root_dir):
        # Remove excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude]
        depth = root.replace(root_dir, '').count(os.sep)
        indent = '    ' * depth
        folder_name = os.path.basename(root)
        tree_lines.append(f"{indent}{folder_name}/")
        for f in files:
            if f not in EXCLUDE_FILES:
                tree_lines.append(f"{indent}    {f}")
    return tree_lines

# === HELPER FUNCTION TO COLLECT CODE SNIPPETS ===
def collect_code_snippets(root_dir, exclude=None, allowed_ext=None):
    exclude = exclude or set()
    allowed_ext = allowed_ext or ALLOWED_EXTENSIONS
    snippets = []
    for root, dirs, files in os.walk(root_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude]
        # Skip folders where we don't want code snippets
        if any(skip in root.split(os.sep) for skip in EXCLUDE_CODE_SNIPPETS_IN_FOLDERS):
            continue
        for f in files:
            if f in EXCLUDE_FILES:
                continue
            if os.path.splitext(f)[1] in allowed_ext:
                file_path = os.path.join(root, f)
                rel_path = os.path.relpath(file_path, root_dir)
                snippets.append((rel_path, file_path))
    return snippets

# === GENERATE SNAPSHOT ===
def generate_snapshot():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# PROJECT SNAPSHOT\n\n")
        f.write(f"**Project Path:** {PROJECT_ROOT}\n\n")
        f.write(f"**Generated on:** {timestamp}\n\n")
        
        f.write("## Folder Structure\n\n")
        folder_tree = generate_folder_structure(PROJECT_ROOT, EXCLUDE_FOLDERS)
        f.write("```\n")
        for line in folder_tree:
            f.write(f"{line}\n")
        f.write("```\n\n")

        f.write("## Key Code Snippets\n\n")
        code_files = collect_code_snippets(PROJECT_ROOT, exclude=EXCLUDE_FOLDERS)
        for rel_path, full_path in code_files:
            f.write(f"### {rel_path}\n\n")
            ext = os.path.splitext(rel_path)[1][1:]  # use extension as code type
            f.write(f"```{ext}\n")
            try:
                with open(full_path, 'r', encoding='utf-8') as code_file:
                    f.write(code_file.read())
            except Exception as e:
                f.write(f"# Could not read file: {e}\n")
            f.write("\n```\n\n")

        f.write("## Project Overview & Commands\n\n")
        f.write("- Python version: 3.x\n")
        f.write("- Virtual Environment: flask_venv\n")
        f.write("- Database: SQLite (dev_database.db)\n")
        f.write("- To create DB: `python create_db.py`\n")
        f.write("- To run app:\n")
        f.write("```powershell\n")
        f.write("$env:FLASK_APP=\"wsgi\"\n")
        f.write("$env:FLASK_ENV=\"development\"\n")
        f.write("flask run\n")
        f.write("```\n\n")
        
        f.write("## Next Planned Features\n\n")
        f.write("- Add Flask-Login authentication\n")
        f.write("- Add CI/CD via GitHub Actions\n")
        f.write("- Environment-based configuration\n")

    print(f"Snapshot generated successfully at {OUTPUT_FILE}")

# === RUN SCRIPT ===
if __name__ == "__main__":
    generate_snapshot()
