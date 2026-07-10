"""Chart color and layout helpers."""

PHASE_COLORS = {
    "ACCUMULATION": "#c8e6c9",  # light green
    "MARKUP": "#2e7d32",  # deep green (use alpha when filling)
    "DISTRIBUTION": "#ffcdd2",  # light red
    "MARKDOWN": "#c62828",  # deep red
    "CONSOLIDATION": "#eceff1",
}

PHASE_FACE_ALPHA = {
    "ACCUMULATION": 0.25,
    "MARKUP": 0.18,
    "DISTRIBUTION": 0.25,
    "MARKDOWN": 0.18,
    "CONSOLIDATION": 0.12,
}

POC_COLOR = "#f9a825"
VA_COLOR = "#90caf9"
HVN_COLOR = "#37474f"
LVN_COLOR = "#b0bec5"
