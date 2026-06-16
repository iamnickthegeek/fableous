# Publishing Fable Orchestrator to GitHub

Session-tested recipe for publishing the fableous repo to GitHub.

## Prerequisites

- GitHub account: `iamnickthegeek` (or your own)
- Repo name: `fableous` (must match exactly — create it on GitHub first)
- SSH key pair generated on the Hermes machine
- Git installed on the Hermes machine

## Step 1: Create the repo on GitHub first

**Critical:** You must create the repo on GitHub.com BEFORE pushing from the terminal.

1. Go to `github.com/new`
2. Repository name: `fableous`
3. Description: `Open-source Fable-mode execution engine for Hermes Agent`
4. Visibility: Public
5. **Do NOT** check "Add a README", "Add .gitignore", or "Add a license" — these exist locally already
6. Click **Create repository**

If you skip this step and run `git push`, you get: `ERROR: Repository not found.`

## Step 2: Generate SSH key

```bash
# Generate the key
ssh-keygen -t ed25519 -C "your-comment-here" -f ~/.ssh/id_ed25519 -N ""

# The email/comment is just a label — it doesn't need to be a real email
```

## Step 3: Add SSH key to GitHub

```bash
# Copy the public key
cat ~/.ssh/id_ed25519.pub
```

1. Go to GitHub.com → Profile → Settings → SSH and GPG keys
2. Click **New SSH key**
3. Title: `Hermes Machine` (or whatever you want)
4. Paste the key
5. Click **Add SSH key**

## Step 4: Configure SSH to trust GitHub

```bash
# Add GitHub's host key to known_hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts

# Test the connection
ssh -T git@github.com
# Expected: "Hi iamnickthegeek! You've successfully authenticated..."
```

Without `ssh-keyscan`, you get: `Host key verification failed.`

## Step 5: Commit and push

```bash
cd ~/.hermes/skills/fableous

# Initialize git
git init
git branch -m main

# Commit everything
git add .
git commit -m "Initial release: v1.0.0 - Fable Orchestrator for Hermes"

# Set remote to SSH URL
git remote add origin git@github.com:iamnickthegeek/fableous.git

# Push
git push -u origin main
```

## Common errors

### "Repository not found"

- You didn't create the repo on GitHub first. Go to `github.com/new` and create it.
- The repo name doesn't match. Check `github.com/iamnickthegeek/fableous`.

### "Host key verification failed"

- Run `ssh-keyscan github.com >> ~/.ssh/known_hosts` before testing.

### "Could not read Username for 'https://github.com'"

- The remote URL is HTTPS. Switch to SSH:
  ```bash
  git remote set-url origin git@github.com:iamnickthegeek/fableous.git
  ```

### "Permission denied (publickey)"

- The SSH key isn't added to GitHub. Re-add it in Settings → SSH keys.
- The SSH agent isn't running. Start it:
  ```bash
  eval "$(ssh-agent -s)"
  ssh-add ~/.ssh/id_ed25519
  ```

## What to exclude from git

Before the first commit, add a `.gitignore` to exclude:

```gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
*.db
*.log
```

If you already committed these, remove them:
```bash
git rm -r --cached __pycache__
git commit -m "Remove cached files"
```

## Version bumps

After v1.0.0, increment the version in these places:

1. `fable_engine/__init__.py` — `__version__`
2. `setup.py` — `version=`
3. `SKILL.md` — frontmatter `version:`
4. `README.md` — any version references
5. `CHANGELOG.md` — add entry

Then commit and push:
```bash
git add .
git commit -m "Bump version to v1.1.0"
git push
```

## Key insight

GitHub requires two separate authentication steps:
1. **SSH key** authenticates your machine to GitHub
2. **Repo creation on web UI** creates the actual repository space

You cannot push to a repo that doesn't exist on GitHub. The `git init` creates a local repo. The `git remote add` points to GitHub. The `git push` uploads — but only if the GitHub repo already exists.
