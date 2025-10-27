# Fork This Repo to Your GitHub

Currently the repo is pointing to:
- **Origin**: https://github.com/beagleboard/cloud9-examples
- **Upstream**: https://github.com/jadonk/cloud9-examples.git

## To Fork to Your Own Repo:

### Option 1: Keep upstream tracking (recommended for contributions)
```bash
# Create a new repo on GitHub first, then:
git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
git push -u origin v2020.01
```

### Option 2: Start fresh (remove upstream)
```bash
git remote remove upstream
git remote set-url origin https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
git push -u origin v2020.01
```

## Current Status:
- Many files are modified (probably from Cloud9 IDE)
- You have untracked files: `.vscode/`, `MyFirstPythonProject/`, `beaglebone-setup.md`

Choose what to do with the modified files before pushing!
