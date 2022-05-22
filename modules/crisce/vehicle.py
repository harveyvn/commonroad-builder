import matplotlib.colors as colors
from shapely.geometry import Point


class Vehicle:
    def __init__(self, script, pos, rot, color, color_code, debug_script, spheres, delay=0):
        self.script = script
        self.debug_script = debug_script
        self.pos = pos
        self.rot = rot
        self.color = color
        self.color_code = colors.to_rgba(list(map(float, color_code.split())))
        self.spheres = spheres
        self.speed = 0
        self.delay = delay

    def obj_dict(obj):
        return obj.__dict__

    def set_speed(self):
        first, last = self.script[0], self.script[-1]

        p1 = Point(first['x'], first['y'])
        p2 = Point(last['x'], last['y'])

        delta_t = last['t'] - first['t']
        distance = p1.distance(p2)
        self.speed = distance / delta_t  # m/s
