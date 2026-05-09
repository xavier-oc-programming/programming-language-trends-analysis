"""
Shared chart style constants and helpers used by both notebooks and the dashboard.

Import in notebooks:
    import sys; sys.path.insert(0, '../pipeline')
    from style import *

Import in pipeline scripts:
    from style import BG, GREEN, style_ax, fmt_k
"""

# ── Backgrounds ───────────────────────────────────────────────────────────────
BG    = '#0f1117'   # main figure / axis background (very dark navy)
PANEL = '#1a1d27'   # legend box and secondary panel background
BORDER = '#2d3148'  # grid lines, axis spines, and borders

# ── Text colours ──────────────────────────────────────────────────────────────
TEXT     = '#c0c0c0'  # tick labels and axis label text
TEXT_DIM = '#8b90a8'  # secondary labels — axis titles, dim annotations
WHITE    = '#ffffff'  # chart title text

# ── Accent colours ────────────────────────────────────────────────────────────
BLUE   = '#5c6cfa'  # primary series / Dominant lifecycle
GREEN  = '#4ecb71'  # positive trend / Rising lifecycle
AMBER  = '#f0c040'  # neutral / Mature lifecycle / average reference lines
RED    = '#f07070'  # negative trend / Declining lifecycle
GREY   = '#aaaaaa'  # Niche lifecycle / muted elements
MARK   = '#e74c3c'  # ChatGPT inflection line (Nov 2022)
ORANGE = '#e67e22'  # secondary accent
PURPLE = '#9b59b6'  # tertiary accent

# ── Lifecycle colour map ───────────────────────────────────────────────────────
# Maps each lifecycle label to its display colour — used in scatter plots and bar charts
LIFECYCLE = {
    'Dominant':  BLUE,
    'Rising':    GREEN,
    'Mature':    AMBER,
    'Declining': RED,
    'Niche':     GREY,
}


def style_ax(ax, fig):
    """Apply consistent dark-theme styling to any matplotlib axis.

    Replaces the repeated 8-line styling block that appears after every chart.
    Call this once at the end of each chart before tight_layout() and savefig().
    """
    ax.set_facecolor(BG)          # dark axis background
    fig.patch.set_facecolor(BG)   # dark figure background (outside the axis)
    ax.tick_params(colors=TEXT, labelsize=10)   # light-coloured tick marks and numbers
    ax.xaxis.label.set_color(TEXT)              # x-axis label colour
    ax.yaxis.label.set_color(TEXT)              # y-axis label colour
    ax.title.set_color(WHITE)                   # chart title white
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)             # dim the axis border lines


def fmt_k(x, _):
    """Format a large number as K or M for axis tick labels.

    Examples: 1500 → '1k', 1_500_000 → '1.5M', 800 → '800'
    The second argument (_) is the tick position — matplotlib passes it but we ignore it.
    """
    if x >= 1_000_000:
        return f'{x / 1_000_000:.1f}M'
    if x >= 1_000:
        return f'{int(x / 1_000)}k'
    return str(int(x))


def fmt_pct(x, _):
    """Format a number as a percentage string for axis tick labels.

    Example: -7.6 → '-7.6%'
    """
    return f'{x:.1f}%'
