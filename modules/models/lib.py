def generate(lst, r, width):
    return [(p[0] * r, p[1] * r, 0, width) for p in list(lst.coords)]


def render_stripe(plt, line):
    xs = [point[0] for point in line.points]
    ys = [point[1] for point in line.points]
    plt.plot(xs, ys, color='b',
             linewidth=4 if line.num == "double" else 1,
             linestyle=(0, (5, 10)) if line.pattern == "dashed" else "solid")
