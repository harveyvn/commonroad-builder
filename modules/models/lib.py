from modules.common import smooth_line
from .stripe import Stripe


def generate(lst, r, width, is_smooth_line):
    coords = list(lst.coords)
    if is_smooth_line:
        coords = smooth_line(list(lst.coords))
    return [(p[0] * r, p[1] * r, 0, width) for p in coords]


def render_stripe(ax, line: Stripe, color: str):
    xs = [point[0] for point in line.points]
    ys = [point[1] for point in line.points]
    ax.plot(xs, ys, color=color,
            linewidth=4 if line.num == "double" else 1,
            linestyle=(0, (5, 10)) if line.pattern == "dashed" else "solid")
