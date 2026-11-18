# Audit the painted surface

Run the audit on finish labels before mapping colors to four physical tool IDs. Two pigments can share a head at different heights. A screenshot in Prepare mode displays head swatches and cannot establish which exposed skin or hair will have the wrong filament.

After reviewed/replay.py, use its job directory as the working directory. The wedding example protects the face, deliberate facial marks and soles while checking clothing and hand contacts. The detector still scores those protected faces. On another sculpt supply its own protected mask.

    python -c "import numpy as n; z=n.load('repaired-u1.npz'); h=z['v'][z['f'],2].mean(1); n.save('protected.npy',(h>80)|(h<3))"
    python /path/to/reviewed/leak_audit.py repaired-u1.npz final.npy rgb.npy audit --protect protected.npy
    python /path/to/reviewed/export_leak_candidate.py /path/to/repo repaired-u1.npz final.npy audit/finish.npy candidates

The audit evaluates local source-texture colors, surface normals and distance to painted interiors at two scales. An automatic change needs agreement at both scales and an edge-connected path to the proposed paint. findings.npz records face indices, original and proposed slots, confidence and whether the edit was applied. Confidence is weighted neighbor agreement. It is not calibrated correctness. Inspect unresolved boundaries and projected close-ups. A large uniformly mispainted area can agree with its own neighbors. Supply verified part masks through --approved-labels (signed per-face finish label, -1 for unknown) to detect and replace every wrong solid label in those areas, including interior faces. Explicit approvals override automatic protection.

For a saved manual repaint, use the entire Orca project as a regression reference. Confirm identical head order and default filament assignments before interpreting an encoded difference as a physical color change.

    python /path/to/scripts/compare_orca_paint.py candidate.3mf manual-repaint.3mf --csv differences.csv

The comparison locates the mesh inside single-file and multi-file single-mesh 3MF projects and compares whole paint strings, including split-triangle brush paint. Blank means inherited/default paint. The comparison verifies corresponding triangle corners up to a constant translation and rejects incompatible geometry. Exit 0 means identical encoded face paint, 1 means differences; the CSV locates them in local model coordinates. Different encodings may describe the same visible paint. Keep the manual Orca file as the source of truth for its fine brush strokes.
