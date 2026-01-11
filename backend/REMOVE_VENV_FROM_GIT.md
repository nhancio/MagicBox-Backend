# How to Remove venv from Git Tracking

If your `venv` or `.venv` folder is already being tracked by Git, follow these steps:

## Step 1: Remove venv from Git (but keep the folder locally)

```bash
# Remove from Git tracking (keeps the folder on your machine)
git rm -r --cached .venv
# OR if it's named 'venv'
git rm -r --cached venv

# If venv is in backend directory
cd backend
git rm -r --cached .venv
```

## Step 2: Verify .gitignore is updated

The `.gitignore` file has been updated to include:
- `venv/`
- `.venv/`
- `env/`
- `.env/`

## Step 3: Commit the changes

```bash
git add .gitignore
git commit -m "Add venv to .gitignore and remove from tracking"
```

## Step 4: Verify it's ignored

```bash
git status
# venv/.venv should no longer appear in the status
```

## Alternative: If venv is in a subdirectory

If your venv is in `backend/.venv`:

```bash
cd backend
git rm -r --cached .venv
cd ..
git add .gitignore
git commit -m "Ignore venv directories"
```

## Note

- The `--cached` flag removes files from Git tracking but keeps them on your local filesystem
- Your venv folder will remain intact and functional
- Future commits will ignore the venv folder automatically
