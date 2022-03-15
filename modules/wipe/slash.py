import copy
from itertools import combinations
import matplotlib.pyplot as plt
from .visualization import draw
from .common import get_poly, collapse, length


class Slash:
    def __init__(self, sm: dict):
        self.sm = sm

    def visualize(self):
        fig, ax = plt.subplots()
        for k in self.sm.keys():
            def viz(ax, sm):
                draw(ax, sm['l'], "green")
                draw(ax, sm['r'], "green")
                for m in sm['m']:
                    draw(ax, m, "green")
                return ax

            draw(ax, self.sm[k]['c'])
            viz(ax, self.sm[k])
        plt.show()

    def simplify(self, is_visual: bool = False):
        if is_visual:
            self.visualize()

        sm = self.sm

        # Find list of pairs of segments and collect lines of them
        dd = {}
        for (k1, k2) in combinations(list(sm.keys()), 2):
            l1, l2 = sm[k1], sm[k2]
            p1 = get_poly(l1)
            p2 = get_poly(l2)

            sm1 = collapse(copy.deepcopy(sm[k1]), p2)
            sm2 = collapse(copy.deepcopy(sm[k2]), p1)
            if k1 in dd:
                dd[k1].append(sm1)
            else:
                dd[k1] = [sm1]
            if k2 in dd:
                dd[k2].append(sm2)
            else:
                dd[k2] = [sm2]

        for k in sm.keys():
            tsm = {'l': [], 'r': [], 'm': []}
            for tm in dd[k]:
                for side in ['l', 'r']:
                    if len(tsm[side]) == 0:
                        tsm[side] = tm[side]
                    else:
                        if length(tm[side]) < length(tsm[side]):
                            tsm[side] = tm[side]
                for i, m in enumerate(tm['m']):
                    if len(tsm['m']) < i + 1:
                        tsm['m'].append(m)
                    else:
                        if length(m) < length(tsm['m'][i]):
                            tsm['m'][i] = m

            sm[k]['l'] = tsm['l']
            sm[k]['r'] = tsm['r']
            sm[k]['m'] = tsm['m']

        self.sm = sm

        if is_visual:
            self.visualize()

        return self.sm
