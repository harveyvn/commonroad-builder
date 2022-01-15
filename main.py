import os
import numpy as np
import pandas as pd
from modules import CONST
from modules.crisce import Roads, Car
from modules.roadlane import categorize_roadlane
from modules.models import Analyzer


def exec_road_from_scenarion(dir_path, dataset_name=None, output_to=None):
    file = f'{dir_path}/sketch.jpeg'
    road = f'{dir_path}/road.jpeg'

    BLUE_CAR_BOUNDARY = np.array([[85, 50, 60], [160, 255, 255]])

    if dataset_name == "SYNTH":
        sketch_type_external = False
        RED_CAR_BOUNDARY = np.array([[0, 200, 180],  # red internal crash sketches
                                     [110, 255, 255]])
        external_impact_points = None
    else:
        RED_CAR_BOUNDARY = np.array([[0, 190, 215], [179, 255, 255]])  # red external_0
        external_csv = f'{dir_path}/external.csv'
        sketch_type_external = True
        external_impact_points = None
        if sketch_type_external:
            df = pd.read_csv(external_csv)
            external_impact_points = dict()
            for i in df.index:
                color = str.lower(df.vehicle_color[i])
                impact = str.lower(df.impact_point[i])
                external_impact_points[color] = dict()
                external_impact_points[color] = impact

    # --------- Main Logic Of the Code Starts Here ---------
    car = Car()
    roads = Roads()
    sketch = file
    output_folder = os.path.join(dir_path, "output")  # sketch.split(".")[0])
    car_length_sim = 4.670000586694935
    sketch_image_path = sketch
    road_image_path = road
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # ------ Read Sketch Image ------
    car.setColorBoundary(red_boundary=RED_CAR_BOUNDARY, blue_boundary=BLUE_CAR_BOUNDARY)
    vehicles, time_efficiency = car.extractVehicleInformation(image_path=sketch_image_path,
                                                              time_efficiency=dict(),
                                                              show_image=False, output_folder=output_folder,
                                                              external=sketch_type_external,
                                                              external_impact_points=external_impact_points,
                                                              crash_impact_locations=CONST.CRISCE_IMPACT_MODEL,
                                                              car_length_sim=car_length_sim)
    car_length, car_width = car.getCarDimensions()
    return roads.extractRoadInformation(image_path=road_image_path,
                                        time_efficiency=time_efficiency,
                                        show_image=False, output_folder=output_folder,
                                        car_length=car_length, car_width=car_width,
                                        car_length_sim=car_length_sim)


if __name__ == '__main__':
    road_data = exec_road_from_scenarion("cases/01")
    lane_factory = categorize_roadlane(road_data)
    (image, baselines, roads) = lane_factory.run()

    for road in roads:
        road = Analyzer(image=image, lanelines=baselines, road=road).run()

    for road in roads:
        print("Angle: ", road.angle)
