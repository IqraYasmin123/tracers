# TRACER AI Engine

The research and inference core: VLM integration, adversarial attack generation, attention-entropy
detection, gradient-based attribution, and diffusion-based reconstruction. Developed primarily in
Google Colab (free GPU), then exported as a stable Python package the backend imports.

## Folder Structure

```
ai-engine/
├── notebooks/     Colab notebooks (one per module: 02_vlm, 04_attacks, 05_detection, ...)
├── src/           Stable, tested Python modules — promoted here once a notebook works
│   ├── vlm/           VLM loading and feature extraction (Module 2)
│   ├── attacks/        FGSM / PGD / DeepFool (Module 4)
│   ├── detection/       Attention-entropy detector (Module 5)
│   ├── attribution/    Gradient-based heatmaps (Module 6)
│   ├── reconstruction/ Diffusion-guided recovery (Module 7)
│   └── explainability/ XAI summaries (Module 8)
├── models/        Saved model weights (.joblib, .pt) — gitignored, stored on Drive/releases instead
├── data/          Datasets — gitignored, stored on Drive instead
└── requirements.txt
```

**Why notebooks *and* `src/`?** Notebooks are for experimentation (Module-by-module, visual,
fast iteration on free GPU). Once a piece of logic is correct and stable, it gets promoted into
`src/` as a plain importable Python module — that's what the FastAPI backend actually imports at
inference time. The backend never imports a notebook.

## Local Setup

```bash
cd ai-engine
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Google Colab Setup

Open `notebooks/00_colab_bootstrap.ipynb` in Colab, or paste this into a fresh notebook cell:

```python
from google.colab import drive
drive.mount('/content/drive')

!git clone https://github.com/<your-username>/TRACER.git
%cd TRACER/ai-engine
!pip install -q -r requirements.txt
```

Persistent storage (datasets, trained weights) lives under Google Drive, not Colab's ephemeral
disk — see `docs/setup_guide.md` in the repo root for the exact folder convention.

## Verifying Your Environment

Run `notebooks/00_colab_bootstrap.ipynb` (or `scripts/check_environment.py` locally) — it checks
GPU availability, library versions, and does one dummy CLIP forward pass.
