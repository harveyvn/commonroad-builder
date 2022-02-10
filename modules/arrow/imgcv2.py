import cv2
import numpy as np
import matplotlib.pyplot as plt
from typing import List
from .contour import Contour
from .lib import Arrow


class ImgCV2:
    def __init__(self, img: np.array, kernel: np.array = np.ones((2, 2))):
        self.kernel = kernel
        self.img = img

    def get_contours(self, debug: bool = False):
        img_gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        img_canny = cv2.Canny(img_gray, 100, 100)
        img_dilate = cv2.dilate(img_canny, self.kernel, iterations=1)
        img_erode = cv2.erode(img_dilate, self.kernel, iterations=1)
        contours, hierarchy = cv2.findContours(img_erode, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if debug:
            Arrow.draw("Step 1", self.img)
            Arrow.draw("Step 2", img_gray)
            Arrow.draw("Step 3", img_canny)
            Arrow.draw("Step 4", img_dilate)
            Arrow.draw("Step 5", img_erode)
            exit()
        return contours

    def find_contour_triangle(self, contours: List, epsilon: float = 0.07, debug: bool = False):
        if len(contours) == 0:
            print("Error: Empty contours!")
            return [], []

        cnt_list, triangle, max_eps = [], None, 0.1
        # Search contour with triangle
        cnt_list = []
        for i, cnt in enumerate(contours):
            contour = Contour(i, cv2.arcLength(cnt, True), Arrow.get_centeroid(cnt), cnt)
            approx = cv2.approxPolyDP(cnt, epsilon * cv2.arcLength(cnt, True), True)
            if len(approx) == 3:
                contour.set_type("triangle")
                contour.set_vertexes(approx)
                triangle = contour
            cnt_list.append(contour)

        print(f'Found a triangle when epsilon is {epsilon}!')

        if debug:
            plt.imshow(self.img, cmap='gray')
            for v in Arrow.contour2list(triangle.vertexes):
                plt.scatter(x=v[0], y=v[1], s=1, color='g')
                plt.scatter(x=v[0], y=v[1], s=1, color='r')
            for cnt in cnt_list:
                c = cnt.centeroid
                plt.scatter(x=c[0], y=c[1], s=1, color='b')
            plt.show()

            for vertex in triangle.vertexes:
                cv2.circle(self.img, (vertex[0][0], vertex[0][1]), 2, (0, 0, 255), -1)
            for cnt in cnt_list:
                cv2.circle(self.img, cnt.centeroid, radius=3, color=(255, 0, 0), thickness=-1)
            cv2.imshow("Image", self.img)
            cv2.waitKey(0)
            exit()
        return triangle, cnt_list
