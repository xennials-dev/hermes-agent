import subprocess
from typing import Optional

def _handle_pr_review(raw_args: str) -> Optional[str]:
    args = raw_args.strip().split()
    if len(args) < 2: return "Usage: /pr_review <repo> <pr_number>"
    repo, pr_num = args[0], args[1]
    
    output = f"Triggering PR Review for {repo}#{pr_num}...\n"
    try:
        output += "> Checking out PR...\n"
        subprocess.run(["gh", "pr", "checkout", pr_num, "-R", repo], check=True, capture_output=True)
        
        output += "> Running pytest...\n"
        test_res = subprocess.run(["pytest"], capture_output=True, text=True)
        
        comment = f"Hermes Agent Review:\nTests passed: {'Yes' if test_res.returncode == 0 else 'No'}\n\n```\n{test_res.stdout[-500:]}\n```"
        output += "> Posting comment...\n"
        subprocess.run(["gh", "pr", "comment", pr_num, "-R", repo, "-b", comment], check=True, capture_output=True)
        output += "Done! Review posted."
    except Exception as e:
        output += f"Error during PR review workflow: {e}"
        
    return output

def register(ctx) -> None:
    ctx.register_command("pr_review", handler=_handle_pr_review, description="Automated CI/CD PR Review using gh CLI.")
