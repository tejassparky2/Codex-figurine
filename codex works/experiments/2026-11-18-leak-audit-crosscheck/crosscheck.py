import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "wedding-u1-skill" / "coloring"))
from approved_match import load_model

repo = Path(__file__).resolve().parents[3]
_, _, before, _ = load_model(repo / "Wedding-150mm-reviewed-paint-guide.3mf")
_, _, after, _ = load_model(repo / "Wedding-leak-candidate-guide.3mf")
changed = np.flatnonzero(before != after)
np.save(repo / "codex works" / "experiments" / "2026-11-18-leak-audit-crosscheck" / "changed-faces.npy", changed)
print("changed", len(changed))
