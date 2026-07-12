# TRACER — Setup Guide

## 1. GitHub Repository Setup

If you haven't already created the GitHub repo:

```bash
# On GitHub.com: create a new empty repository named "TRACER" (no README, no .gitignore —
# we already have our own)

# Locally, inside this project folder:
git init
git add .
git commit -m "Module 1: project foundation and environment setup"
git branch -M main
git remote add origin https://github.com/<your-username>/TRACER.git
git push -u origin main
```

**Branching convention for the rest of the project:**
```bash
git checkout -b module-2-vlm-integration
# ... do the work, commit ...
git push -u origin module-2-vlm-integration
# open a Pull Request into main, merge once the module is verified working
```
One branch per module keeps your Git history readable and demoable during your viva — you can
literally show the panel "here's the commit where Module 5 detection was added."

## 2. Local Development Environment

Requires Python 3.10+.

```bash
cd ai-engine
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python ../scripts/check_environment.py
```

You should see `Environment check PASSED. Ready for Module 2.` If any packages are missing, the
script tells you exactly which ones.

## 3. Google Colab + Google Drive Workflow

Colab's local disk is **ephemeral** — everything is wiped when the runtime disconnects. Google
Drive is where anything that needs to persist (datasets, trained model weights, generated
reports) actually lives.

**Drive folder convention** (created automatically by the bootstrap notebook):
```
MyDrive/TRACER/
├── datasets/     Raw and processed datasets
├── models/       Saved detector weights, fine-tuned checkpoints
└── outputs/      Generated reports, exported figures
```

**Every Colab session, run this first** (or open `ai-engine/notebooks/00_colab_bootstrap.ipynb`):
```python
from google.colab import drive
drive.mount('/content/drive')

!git clone https://github.com/<your-username>/TRACER.git /content/TRACER
%cd /content/TRACER/ai-engine
!pip install -q -r requirements.txt
```

## 4. Environment Variables

Copy the example env file and fill in your own values (never commit the real `.env`):

```bash
cp .env.example .env
```

See `.env.example` in the repo root for the variables needed by later modules (database URL,
JWT secret, Hugging Face token, etc.) — most are unused until Module 9 (Backend) but are listed
here now so the convention is established from day one.

## 5. Verifying Module 1 Is Complete

Run through this checklist:
- [ ] `git clone` the repo on a fresh machine (or fresh Colab runtime) and confirm the folder
      structure matches `README.md`
- [ ] `python scripts/check_environment.py` passes locally
- [ ] `ai-engine/notebooks/00_colab_bootstrap.ipynb` runs top-to-bottom in Colab without errors,
      ending in `Module 1 environment check PASSED.`
- [ ] Repo is pushed to GitHub with this initial commit

Once all boxes are checked, Module 1 is done — move to Module 2 (VLM Integration).
