# Contributing

Install with uv sync --locked --extra dev. Run uv run pytest -q,
uv run ruff check src tests examples, and
uv run ruff format --check src tests examples.

Numerical changes need an independent physical limit, reference connection,
conservation identity, or separately implemented estimator. Tests must not
silently turn modeled protection failures into successful expected operations.

Record RMS/peak convention, terminal polarity, units, sampling, grounding,
current ceilings, validity, timing and model exclusions. Preserve None for missing
operations and explicit masks for unavailable measured data.

Keep commits substantive and reviewable. Do not add empty commits, fabricate
timestamps or split unrelated formatting into history targets.

For a new study, register its strict case, add physical parameters and assumptions,
provide a targeted behavior check, and update the experiment catalog.
Reproduce publication artifacts from one clean source revision into ignored
outputs/, render, verify, inspect figures, then use examples/build_gallery.py.

Never relabel an old capture with a newer solver revision. Capture changed
certificates and resolved measurement constants. Keep generated text LF for
cross-platform manifest integrity. Exclude credentials and scratch environments.

Documentation should link primary method sources and distinguish implemented
models from manufacturer behavior or standards certification.
