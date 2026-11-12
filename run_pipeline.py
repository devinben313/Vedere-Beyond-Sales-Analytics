"""
run_pipeline.py - rebuild everything end to end.

    python run_pipeline.py            # data -> clean -> SQLite -> SQL analysis -> Tableau extracts -> notebook
    python run_pipeline.py --no-notebook
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "scripts/01_generate_data.py",
    "scripts/02_clean_transform.py",
    "scripts/03_build_database.py",
    "scripts/04_run_analysis.py",
    "scripts/05_export_tableau.py",
]

for step in STEPS:
    print(f"\n=== {step} ===")
    subprocess.run([sys.executable, step], cwd=ROOT, check=True)

if "--no-notebook" not in sys.argv:
    print("\n=== executing notebooks/vedere_beyond_analysis.ipynb ===")
    subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
                    "notebooks/vedere_beyond_analysis.ipynb"], cwd=ROOT, check=True)
print("\nPipeline complete.")
