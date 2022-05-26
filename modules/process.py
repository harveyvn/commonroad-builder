import os
import sys
import cv2
import json
import copy
import click
import pickle
import platform
import warnings
import numpy as np
import pandas as pd
import logging as logger
import matplotlib.pyplot as plt

from pathlib import Path
from typing import List
from modules.crisce.pre_processing import Pre_Processing
from modules.crisce.roads import Roads
from modules.crisce.car import Car
from modules.crisce.kinematics import Kinematics
from modules.crisce.common import visualize_crisce_sketch, visualize_crisce_simlanes
from modules.crisce import extract_data_from_scenario, Vehicle

from modules.roadlane import categorize_roadlane, refine_roadlanes
from modules.analyzer import Analyzer
from modules.arrow import ArrowAnalyzer
from modules.common import pairs
from modules.constant import CONST
from modules.models import Segment, BngSegement
from modules.wipe import Slash
from modules import DataHandler


warnings.filterwarnings('ignore')


def run(accident_sketch: str):
    try:
        sketch = os.path.join(accident_sketch, "sketch.jpeg")
        if not os.path.exists(sketch):
            sketch = os.path.join(accident_sketch, "sketch.jpg")

        road = os.path.join(accident_sketch, "road.jpeg")
        road_arrow = os.path.join(accident_sketch, "road_arrow.jpeg")
        if not os.path.exists(road):
            road = os.path.join(accident_sketch, "road.jpg")
            road_arrow = os.path.join(accident_sketch, "road_arrow.jpg")

        ############   Setup  ###############
        # Additional controls
        show_image = False  # TODO Use --interactive?

        BLUE_CAR_BOUNDARY = np.array([[85, 50, 60],
                                      [160, 255, 255]])
        sketch_type_external = True
        RED_CAR_BOUNDARY = np.array([[0, 190, 215],  # red external crash sketches
                                     [179, 255, 255]])
        external_csv = os.path.join(accident_sketch, "external.csv")
        df = pd.read_csv(external_csv)
        external_impact_points = dict()
        for i in df.index:
            color = str.lower(df.vehicle_color[i])
            impact = str.lower(df.impact_point[i])
            external_impact_points[color] = dict()
            external_impact_points[color] = impact

        output_folder = os.path.join(accident_sketch, "output")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        logger.debug(f"Accident sketch file {sketch}")
        logger.debug(f"External {sketch_type_external}")

        # TODO ADD BEAMNG CONFIGURATIONS !

        ############   Generation  ###############

        logger.info(f"Generation of simulation starts")

        car = Car()
        roads = Roads()
        kinematics = Kinematics()
        pre_process = Pre_Processing()

        sketch_image_path = sketch
        road_image_path = road
        road_arrow_image_path = road_arrow

        #### ------ Read Sketch Image ------ #######

        image = pre_process.readImage(sketch_image_path)

        car.setColorBoundary(red_boundary=RED_CAR_BOUNDARY, blue_boundary=BLUE_CAR_BOUNDARY)

        # Step 1: Extract vehicles' information
        vehicles, time_efficiency = car.extractVehicleInformation(image_path=sketch_image_path, time_efficiency=dict(),
                                                                  show_image=show_image, output_folder=output_folder,
                                                                  external=sketch_type_external,
                                                                  external_impact_points=external_impact_points,
                                                                  crash_impact_locations=CONST.CRISCE_IMPACT_MODEL,
                                                                  car_length_sim=CONST.CAR_LENGTH_SIM)

        car_length, car_width = car.getCarDimensions()
        height, width = car.getImageDimensions()

        # Step 2: Extract roads' information. Note: We need the size of the vehicles to rescale the roads
        roads, lane_nodes, road_lanes, a_ratio = roads.extractRoadInformation(image_path=road_image_path,
                                                                              time_efficiency=time_efficiency,
                                                                              show_image=show_image,
                                                                              output_folder=output_folder,
                                                                              car_length=car_length,
                                                                              car_width=car_width,
                                                                              car_length_sim=CONST.CAR_LENGTH_SIM)

        # Step 3: Plan the trajectories
        # TODO Add parameter to decide whih planner to use
        vehicles, time_efficiency = kinematics.extractKinematicsInformation(image_path=sketch_image_path,
                                                                            vehicles=vehicles,
                                                                            time_efficiency=time_efficiency,
                                                                            output_folder=output_folder,
                                                                            show_image=show_image)

        print("==================================================")
        print("==================================================")
        print("OUTPUT FOLDER")

        try:
            SKETCH_NAME = sketch.split('/')[2]
        except Exception as ex:
            SKETCH_NAME = ""
        if platform.system() == CONST.WINDOWS:
            SKETCH_NAME = sketch.split('\\')[2]

        OUTPUT_PATH = f'outputs/{SKETCH_NAME}'
        if not os.path.exists(OUTPUT_PATH):
            os.makedirs(OUTPUT_PATH)

        print("==================================================")
        print("==================================================")
        print("EXTRACT VEHICLES INFORMATION")
        vhs = []
        for color in vehicles:
            color_code = CONST.RED_RGBA
            if color == "blue":
                color_code = CONST.BLUE_RGBA
            vehicle = vehicles[color]
            angle = vehicle["vehicle_info"]["0"]["angle_of_car"]
            orig_pos = vehicle["snapshots"][0]["center_of_car"]
            distorted_height = height * CONST.CAR_LENGTH_SIM / car_length
            x = orig_pos[0] * CONST.CAR_LENGTH_SIM / car_length
            y = distorted_height - (orig_pos[1] * CONST.CAR_LENGTH_SIM / car_length)
            vh = Vehicle(
                script=vehicle["trajectories"]["script_trajectory"],
                pos=(round(x, 1), round(y, 1), 0),
                rot=(0, 0, -angle - 90),
                color=color,
                color_code=color_code,
                debug_script=vehicle["trajectories"]["debug_trajectory"],
                spheres=vehicle["trajectories"]["spheres"],
                delay=vehicle["trajectories"]["delay"]
            )
            vh.set_speed()
            vhs.append(vh)
            # print(vh.color)
            # print(vh.script)

        print("==================================================")
        print("==================================================\n\n")

        print("==================================================")
        print("==================================================")
        print("EXTRACT ARROW INFORMATION")

        diff = 0
        # Extract arrow direction
        kernel = np.ones((2, 2))
        if os.path.exists(road_arrow_image_path):
            img = cv2.imread(road_arrow_image_path)
        else:
            img = cv2.imread(road_image_path)

        diff, cm = ArrowAnalyzer(kernel=kernel, img=img).run()

        print("==================================================")
        print("==================================================\n\n")

        if road_lanes["road_type"] > 0:
            road_lanes = refine_roadlanes(copy.deepcopy(road_lanes))

        lane_factory = categorize_roadlane(copy.deepcopy(road_lanes))
        (image, baselines, segments) = lane_factory.run()
        for i, segment in enumerate(segments):
            analyzer = Analyzer(image=image, lanelines=baselines, segment=segment)
            lane_dict = analyzer.search_laneline(num_points=12)
            segment.lines = analyzer.categorize_laneline(lane_dict)
            flipped_lines = segment.flip(image.shape[0])
            segment.get_bng_segment(flipped_lines, a_ratio)
            # analyzer.visualize(title=SKETCH_NAME, is_save=True)

        def render_vehicle_trajectory(ax, vehicles):
            for v in vehicles:
                xs = [p['x'] for p in v.script]
                ys = [p['y'] for p in v.script]
                c = 'r' if v.color == "red" else 'b'
                ax.plot(xs, ys, c=c, marker="x")
            return ax

        print("==================================================")
        print("==================================================")
        print("==================================================")
        print("==================================================")
        plt.clf()
        fig, ax = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle(f'Case: {SKETCH_NAME} - Arrow: {diff}', fontsize=40)
        ax[0][0].imshow(image, cmap="gray", origin="lower")
        # ax[0][0] = visualize_crisce_sketch(ax[0][0], roads["sketch_lane_width"][0], roads["large_lane_midpoints"])
        ax[0][0].title.set_text("Road Sketch")
        ax[0][0].set_aspect("equal")

        ax[0][1] = visualize_crisce_simlanes(ax[0][1], roads["scaled_lane_width"], roads["simulation_lane_midpoints"])
        ax[0][1].title.set_text("CRISCE Road")
        ax[0][1].set_aspect("equal")

        ax[0][2] = visualize_crisce_simlanes(ax[0][2], roads["scaled_lane_width"], roads["simulation_lane_midpoints"])
        ax[0][2].title.set_text("CRISCE Road with Vehicle Trajectory")
        ax[0][2].set_aspect("equal")

        for segment in segments:
            ax[1][0] = segment.visualize(ax[1][0], segment.lines)
        ax[1][0].set_aspect("equal")

        for segment in segments:
            sm: Segment = segment
            flipped_lines = sm.flip(image.shape[0])
            ax[1][1] = sm.visualize(ax[1][1], flipped_lines, "Rotate the coordinates")
        ax[1][1].set_aspect("equal")

        # Remove overlapping lines
        original_lines = {}
        for i, segment in enumerate(segments):
            sm: Segment = segment
            original_lines[i] = sm.bng_segment.get_lines()
        try:
            slash = Slash(original_lines)
            modified_lines = slash.simplify()
        except Exception as e:
            print("Overlapping Remove Exception")
            modified_lines = original_lines

        for i, segment in enumerate(segments):
            bng_segment: BngSegement = segment.bng_segment
            bng_segment.set_lines(modified_lines[i])
            ax[1][2] = bng_segment.visualize(ax[1][2], show_center=False)
        ax[1][2].set_aspect("equal")
        ax[1][2].title.set_text("Final Road with Lane Marking")

        ax[0][0] = render_vehicle_trajectory(ax[0][0], vhs)
        ax[0][2] = render_vehicle_trajectory(ax[0][2], vhs)
        ax[1][0] = render_vehicle_trajectory(ax[1][0], vhs)
        ax[1][1] = render_vehicle_trajectory(ax[1][1], vhs)
        ax[1][2] = render_vehicle_trajectory(ax[1][2], vhs)
        plt.show()
        print("==================================================")
        print("==================================================")

        print("Data Export Handler")
        dh = DataHandler(sketch_name=SKETCH_NAME,
                         vehicles=vhs,
                         roads=[sm.bng_segment for sm in segments],
                         rot_deg=diff)
        dh.to_json()

        fig.savefig(f'outputs/{SKETCH_NAME}/viz.png', bbox_inches="tight")
    finally:
        pass
