import re
import subprocess
import sys
import shutil
from pathlib import Path

GH_PATH = shutil.which("gh") or r"C:\Program Files\GitHub CLI\gh.exe"

def parse_tasks(tasks_file: Path):
    content = tasks_file.read_text(encoding="utf-8")
    pattern = r"## (\d+)\. ([^\n]+)\nGoal: ([^\n]+)\nDescription: ([^\n]+)"
    matches = re.findall(pattern, content)
    
    tasks = []
    for num, title, goal, desc in matches:
        issue_title = f"Task #{num}: {title}"
        issue_body = f"""@google-jules

## Overview & Goal
{goal}

## Description
{desc}

## Definition of Done (DoD)
- [ ] Code implementation complete
- [ ] Unit & integration tests written and passing
- [ ] Documented and verified
"""
        tasks.append((num, issue_title, issue_body))
    return tasks

def create_github_issues(tasks):
    print(f"Parsed {len(tasks)} tasks from tasks.md using GH CLI ({GH_PATH}).")
    for num, title, body in tasks:
        print(f"Creating GitHub Issue #{num}: {title}...")
        cmd = [
            GH_PATH, "issue", "create",
            "--repo", "denis911/ai-consilium",
            "--title", title,
            "--body", body
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"  -> Created: {res.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"  -> Failed: {e.stderr.strip() or e.stdout.strip()}")
            return False
    return True

if __name__ == "__main__":
    tasks_path = Path("_docs/tasks.md")
    if not tasks_path.exists():
        print("Error: _docs/tasks.md not found.")
        sys.exit(1)
    
    tasks = parse_tasks(tasks_path)
    success = create_github_issues(tasks)
    if not success:
        sys.exit(1)
