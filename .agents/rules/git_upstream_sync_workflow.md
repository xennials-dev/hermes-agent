# Git Upstream Sync Workflow Protocol

Whenever syncing this workspace with upstream (`NousResearch/hermes-agent:main`), strictly execute:

```bash
git fetch upstream
git pull upstream main
```

### Protocol Steps:
1. `rebase.autoStash` will automatically stash uncommitted changes.
2. `pull.rebase` fetches and applies `upstream/main` cleanly.
3. Your custom commits are re-applied on top of the latest upstream commits.
4. Auto-stash un-stashes your dirty workspace changes.

### Conflict Handling:
- Resolve conflicts in files.
- `git add <file>`
- `git rebase --continue`

### Verification:
```bash
git log --oneline -n 10
git status
```
