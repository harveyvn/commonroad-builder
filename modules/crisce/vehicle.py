class Vehicle:
    def __init__(self, script, pos, rot, color, color_code, debug_script, spheres):
        import matplotlib.colors as colors
        self.script = script
        self.debug_script = debug_script
        self.pos = pos
        self.rot = rot
        self.color = color
        self.color_code = colors.to_rgba(list(map(float, color_code.split())))
        self.spheres = spheres
