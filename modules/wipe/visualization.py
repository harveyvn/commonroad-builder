def draw(ax, points, color="red"):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.plot(xs, ys, linewidth=1, linestyle="solid", color=color)
    return ax


def draw_poly(ax, p):
    ax.plot(*p.exterior.xy)
    return ax