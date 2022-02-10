import numpy as np
from .imgcv2 import ImgCV2
from .dbscan import DBScan
from .lib import ArrowLib


class ArrowAnalyzer:
    def __init__(self, img: np.array, kernel: np.array = np.ones((2, 1))):
        self.kernel = kernel
        self.img = img

    def run(self):
        kernel = self.kernel
        img = self.img
        imgcv2 = ImgCV2(img, kernel)
        contours = imgcv2.get_contours(debug=False)
        assert len(contours) > 0

        cnt_tri, cnt_list = imgcv2.find_contour_triangle(contours=contours, debug=False)
        assert cnt_tri is not None

        centers = imgcv2.get_centers_from(contours=cnt_list, debug=False)
        db = DBScan(points=centers)
        group = db.find_group_contain_point(point=cnt_tri.centeroid, debug=False, img=img)
        # db.debug(img=img)
        assert 0 < len(group) < 4

        arrow_contours = ArrowLib.find_contours_by_centroid(group, cnt_list, debug=False, img=img)
        assert len(arrow_contours) == 3

        pair = ArrowLib.find_shortest_pair(contours=arrow_contours, debug=False, img=img)
        assert cnt_tri in pair

        ArrowLib.find_deg_of(pair[0], pair[1], debug=True)
