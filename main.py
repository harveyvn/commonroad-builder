import os
import sys
import cv2
import json

import click
import platform
import numpy as np
import pandas as pd
import logging as logger
import matplotlib.pyplot as plt

from pathlib import Path
from modules.crisce.pre_processing import Pre_Processing
from modules.crisce.roads import Roads
from modules.crisce.car import Car
from modules.crisce.kinematics import Kinematics
from modules.crisce import extract_data_from_scenario
from modules.roadlane import categorize_roadlane, refine_roadlanes
from modules.analyzer import Analyzer
from modules.models import Map
from modules.constant import CONST

if platform.system() == CONST.WINDOWS:
    from modules.crisce.simulation import Simulation

# Ensure PythonRobotics modules are included
root_folder = Path(Path(Path(__file__).parent).parent).absolute()
sys.path.append(os.path.join(root_folder, "PythonRobotics", "PathPlanning", "BezierPath"))
# TODO REMOVE THOSE!
sys.path.append(os.path.join(root_folder, "PythonRobotics", "PathPlanning", "CubicSpline"))
sys.path.append(os.path.join(root_folder, "PythonRobotics", "PathPlanning", "BSplinePath"))


def setup_logging(log_to, debug):
    def log_exception(extype, value, trace):
        logger.exception('Uncaught exception:', exc_info=(extype, value, trace))

    # Disable annoyng messages from matplot lib.
    # See: https://stackoverflow.com/questions/56618739/matplotlib-throws-warning-message-because-of-findfont-python
    logger.getLogger('matplotlib.font_manager').disabled = True
    # Disable annoyng messages from Pillow lib.
    logger.getLogger('PIL').setLevel(logger.WARNING)

    term_handler = logger.StreamHandler()
    log_handlers = [term_handler]
    start_msg = "Process Started"

    if log_to is not None:
        file_handler = logger.FileHandler(log_to, 'a', 'utf-8')
        log_handlers.append(file_handler)
        start_msg += " ".join(["writing to file: ", str(log_to)])

    log_level = logger.DEBUG if debug else logger.INFO

    logger.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=log_level, handlers=log_handlers)

    sys.excepthook = log_exception

    logger.info(start_msg)


@click.group()
@click.option('--log-to', required=False, type=click.Path(exists=False),
              help="Location of the log file. If not specified logs appear on the console")
@click.option('--debug', required=False, is_flag=True, default=False, show_default='Disabled',
              help="Activate debugging (results in more logging)")
@click.pass_context
def cli(ctx, log_to, debug):
    # Pass the context of the command down the line
    ctx.ensure_object(dict)
    # Setup logging
    setup_logging(log_to, debug)


@cli.command()
@click.option('--accident-sketch', required=True, type=click.Path(exists=True), multiple=False,
              help="Input accident sketch for generating the simulation")
@click.option('--dataset-name', required=True, type=click.Choice(['CIREN', 'SYNTH'], case_sensitive=False),
              multiple=False,
              help="Name of the dataset the accident comes from.")
@click.option('--output-to', required=False, type=click.Path(exists=False), multiple=False,
              help="Folder to store outputs. It will created if not present. If omitted we use the accident folder.")
@click.option('--beamng-home', required=True, type=click.Path(exists=True), multiple=False,
              help="Home folder of the BeamNG.research simulator")
@click.option('--beamng-user', required=True, type=click.Path(exists=True), multiple=False,
              help="User folder of the BeamNG.research simulator")
#
# TODO This is not working right now, I suspect we need the CSV in any case !
# @click.option('--validate', is_flag=True, default=False, show_default='Disabled',
#              help="If activate a file named external.csv containing the expected impact must be provided in the accident folder."
#                   "This file contains the data necerrary to validate the generated simulation")
@click.pass_context
def generate(ctx, accident_sketch, dataset_name, output_to, beamng_home=None, beamng_user=None):
    # Pass the context of the command down the line
    ctx.ensure_object(dict)

    try:
        sketch = os.path.join(accident_sketch, "sketch.jpeg")
        if not os.path.exists(sketch):
            sketch = os.path.join(accident_sketch, "sketch.jpg")

        road = os.path.join(accident_sketch, "road.jpeg")
        if not os.path.exists(road):
            road = os.path.join(accident_sketch, "road.jpg")

        ############   Setup  ###############
        # Additional controls
        show_image = False  # TODO Use --interactive?

        BLUE_CAR_BOUNDARY = np.array([[85, 50, 60],
                                      [160, 255, 255]])
        if dataset_name == "SYNTH":
            sketch_type_external = False
            RED_CAR_BOUNDARY = np.array([[0, 200, 180],  # red internal crash sketches
                                         [110, 255, 255]])
            external_impact_points = None
        else:
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

        output_folder = output_to if output_to is not None else os.path.join(accident_sketch, "output")
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        logger.debug(f"Accident sketch file {sketch}")
        logger.debug(f"External {sketch_type_external}")
        logger.debug(f"Output to {output_folder}")

        # TODO ADD BEAMNG CONFIGURATIONS !

        ############   Generation  ###############

        logger.info(f"Generation of simulation starts")

        car = Car()
        roads = Roads()
        kinematics = Kinematics()
        pre_process = Pre_Processing()

        sketch_image_path = sketch
        road_image_path = road

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
        roads, lane_nodes, road_lanes = roads.extractRoadInformation(image_path=road_image_path,
                                                                     time_efficiency=time_efficiency,
                                                                     show_image=show_image,
                                                                     output_folder=output_folder, car_length=car_length,
                                                                     car_width=car_width,
                                                                     car_length_sim=CONST.CAR_LENGTH_SIM)

        # Step 3: Plan the trajectories
        # TODO Add parameter to decide whih planner to use
        vehicles, time_efficiency = kinematics.extractKinematicsInformation(image_path=sketch_image_path,
                                                                            vehicles=vehicles,
                                                                            time_efficiency=time_efficiency,
                                                                            output_folder=output_folder,
                                                                            show_image=show_image)

        road_lanes = generate_lane_markings(road_lanes)

        # Step 4: Generate the simulation
        simulation_folder = os.path.join(output_folder, "simulation/")
        if not os.path.exists(simulation_folder):
            os.makedirs(simulation_folder)

        simulation = Simulation(vehicles=vehicles, roads=roads,
                                lane_nodes=lane_nodes, kinematics=kinematics,
                                time_efficiency=time_efficiency, output_folder=simulation_folder,
                                car_length=car_length, car_width=car_width,
                                car_length_sim=CONST.CAR_LENGTH_SIM, sketch_type_external=sketch_type_external,
                                height=height, width=width,
                                crash_impact_model=CONST.CRISCE_IMPACT_MODEL,
                                sampling_frequency=5,
                                road_lanes=road_lanes)

        logger.info("Generation Ends")

        # Step 5: Execute the simulation on BeamNG.research
        sketch_id = os.path.basename(os.path.dirname(sketch_image_path))
        logger.info(f"Execution of sketch {sketch_id} Starts")

        simulation.bng, simulation.scenario = simulation.setupBeamngSimulation(sketch_id, beamng_port=64257,
                                                                               beamng_home=beamng_home,
                                                                               beamng_user=beamng_user)
        # Make sure user sees the crash from the above
        simulation.aerialViewCamera()

        ###### ------ Plotting Roads ---------- ##########
        fig = plt.figure(figsize=(30, 20))

        # Must be called while the simulation runs...
        simulation.plot_road(plt.gca())
        plt.gca().set_aspect("equal")
        # plt.axis('off')
        plt.axis(False)
        plt.gca().invert_yaxis()
        plt.gca().invert_xaxis()
        # plt.show()
        plt.savefig(simulation.output_folder + '{}_sim_plot_road.jpg'.format(simulation.process_number),
                    bbox_inches='tight')
        simulation.process_number += 1
        # fig.savefig(simulation.output_folder + ".jpg", bbox_inches='tight')
        plt.close()

        # This also requires the road, so cannot be called before the end of the simulation
        simulation.plotSimulationCrashSketch()
        simulation.initiateDrive()

        logger.info("Execution Ends")

        ############   Reporting  ###############

        logger.info("Reporting Starts")

        simulation.postCrashDamage()

        for vehicle_color in vehicles:
            ref_impact_side = vehicles[vehicle_color]["impact_point_details"]["internal_impact_side"]
            print(vehicle_color, ref_impact_side)

        simulation.effectAndAccurayOfSimulation()

        road_similarity = simulation.computeRoadGeometricSimilarity()
        placement_similarity, orientation_similarity = simulation.computeVehiclesSimilarity()
        simulation.computeBboxTrajectory(image.copy(), show_image=show_image)

        simulation_accuracy = simulation.computeSimulationAccuracy(road_similarity, placement_similarity,
                                                                   orientation_similarity)

        total_time = simulation.computeCrisceEfficiency()
        simulation.plotCrisceEfficiency(total_time)
        simulation.traceVehicleBbox()

        analysis_log_df = pd.DataFrame([[simulation.log["simulated_impact"], simulation.log["road_similarity"],
                                         simulation.log["placement_similarity"],
                                         simulation.log["orientation_similarity"],
                                         simulation.log["quality_of_env"], simulation.log["red_side_match"],
                                         simulation.log["blue_side_match"], simulation.log["quality_of_crash"],
                                         simulation.log["red_cum_iou"], simulation.log["blue_cum_iou"],
                                         simulation.log["quality_of_traj"],
                                         {"red": simulation.log["vehicles"]["red"]["crash_veh_disp_error"],
                                          "blue": simulation.log["vehicles"]["blue"]["crash_veh_disp_error"]},
                                         {"red": simulation.log["vehicles"]["red"]["crash_veh_IOU"],
                                          "blue": simulation.log["vehicles"]["blue"]["crash_veh_IOU"]},
                                         simulation.log["simulation_accuracy"],
                                         simulation.log["total_time"]]],
                                       index=[sketch],
                                       columns=['simulated_impact', 'road_similarity', 'placement_similarity',
                                                'orientation_similarity', "quality_of_environment",
                                                "red_side_match", "blue_side_match", "quality_of_crash",
                                                "red_cum_iou", "blue_cum_iou", "quality_of_trajectory",
                                                "crash_veh_disp_error", "crash_veh_IOU",
                                                'simulation_accuracy', 'total_time'])

        index_value = analysis_log_df.index.values
        # print("index values", p)
        analysis_log_df.insert(0, column="file_name", value=index_value)
        analysis_log_df.reset_index(drop=True, inplace=True)

        for v_color in vehicles:
            vehicles[v_color]["trajectories"]["computed"]["bezier_curve"] = [waypoint.tolist()
                                                                             for waypoint in
                                                                             vehicles[v_color]["trajectories"][
                                                                                 "computed"][
                                                                                 "bezier_curve"]]
            vehicles[v_color]["trajectories"]["computed"]["b_spline"] = [waypoint.tolist()
                                                                         for waypoint in
                                                                         vehicles[v_color]["trajectories"]["computed"][
                                                                             "b_spline"]]
            vehicles[v_color]["trajectories"]["computed"]["cubic_spline"] = [waypoint.tolist()
                                                                             for waypoint in
                                                                             vehicles[v_color]["trajectories"][
                                                                                 "computed"][
                                                                                 "cubic_spline"]]
            vehicles[v_color]["trajectories"]["original_trajectory"] = [waypoint.tolist()
                                                                        for waypoint in
                                                                        vehicles[v_color]["trajectories"][
                                                                            "original_trajectory"]]
            vehicles[v_color]["trajectories"]["distorted_trajectory"] = [waypoint.tolist()
                                                                         for waypoint in
                                                                         vehicles[v_color]["trajectories"][
                                                                             "distorted_trajectory"]]
            vehicles[v_color]["trajectories"]["simulation_trajectory"] = [waypoint.tolist()
                                                                          for waypoint in
                                                                          vehicles[v_color]["trajectories"][
                                                                              "simulation_trajectory"]]

        log = {"vehicles": vehicles,
               "vehicle_crash_specifics": simulation.log["vehicles"],
               "simulation_trajectory": {
                   "red": simulation.crash_analysis_log["vehicles"]["red"]["simulation_trajectory"],
                   "blue": simulation.crash_analysis_log["vehicles"]["blue"][
                       "simulation_trajectory"]},
               "simulation_rotations": {"red": simulation.crash_analysis_log["vehicles"]["red"]["rotations"],
                                        "blue": simulation.crash_analysis_log["vehicles"]["blue"]["rotations"]},
               "sim_veh_speed": {"red": simulation.crash_analysis_log["vehicles"]["red"]["wheel_speed"],
                                 "blue": simulation.crash_analysis_log["vehicles"]["blue"]["wheel_speed"]},
               "sim_time": {"red": simulation.crash_analysis_log["vehicles"]["red"]["sim_time"],
                            "blue": simulation.crash_analysis_log["vehicles"]["blue"]["sim_time"]},
               "simulated_impact": simulation.log["simulated_impact"],
               "road_similarity": simulation.log["road_similarity"],
               "placement_similarity": simulation.log["placement_similarity"],
               "orientation_similarity": simulation.log["orientation_similarity"],
               "quality_of_env": simulation.log["quality_of_env"], "red_side_match": simulation.log["red_side_match"],
               "blue_side_match": simulation.log["blue_side_match"],
               "quality_of_crash": simulation.log["quality_of_crash"],
               "red_cum_iou": simulation.log["red_cum_iou"], "blue_cum_iou": simulation.log["blue_cum_iou"],
               "quality_of_traj": simulation.log["quality_of_traj"],
               "crash_disp_error": {"red": simulation.log["vehicles"]["red"]["crash_veh_disp_error"],
                                    "blue": simulation.log["vehicles"]["blue"]["crash_veh_disp_error"]},
               "crash_IOU": {"red": simulation.log["vehicles"]["red"]["crash_veh_IOU"],
                             "blue": simulation.log["vehicles"]["blue"]["crash_veh_IOU"]},
               "simulation_accuracy": simulation.log["simulation_accuracy"],
               "total_time": simulation.log["total_time"]}

        with open(os.path.join(output_folder, "summary.json"), 'w') as fp:
            json.dump(log, fp, indent=1)




    finally:
        pass


def generate_lane_markings(road_lanes):
    lane_factory = categorize_roadlane(road_lanes)
    (image, baselines, roads) = lane_factory.run()
    for road in roads:
        analyzer = Analyzer(image=image, lanelines=baselines, road=road)
        lane_dict = analyzer.search_laneline()
        analyzer.categorize_laneline(lane_dict)
        road.generate_lanes()
    return roads


# Execute the Command Line Interpreter
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from modules.arrow import ArrowAnalyzer

    kernel = np.ones((2, 1))
    img = cv2.imread("samples/road5a.jpeg")
    ArrowAnalyzer(kernel=kernel, img=img).run()

    exit()

    # straights = [99817, 100343, 102804, 105165, 108812, 109176, 109536, 117692]
    # for name in [102804]:
    #     roads, lane_nodes, road_lanes = extract_data_from_scenario(f'CIREN/single/{name}')
    #     lane_factory = categorize_roadlane(road_lanes)
    #     (image, baselines, segments) = lane_factory.run()
    #
    #     for segment in segments:
    #         analyzer = Analyzer(image=image, lanelines=baselines, road=segment)
    #         lane_dict = analyzer.search_laneline()
    #         analyzer.categorize_laneline(lane_dict)
    #         analyzer.visualize()
    #         segment.generate_lanes()
    #
    #     network = Map(segments, image)
    #     network.draw(True)
    #     network.generate_road_with_ratio(lane_nodes, name)

    # single = [99817, 100343, 102804, 105165, 108812, 109176, 109536, 117692, 135859, 142845]
    # parallel = [100, 101, 105222, 119897, 128719, 171831]
    for s in [128719]:
        roads, lane_nodes, road_lanes = extract_data_from_scenario(f'CIREN/parallel/{s}')

        if road_lanes["road_type"] > 0:
            road_lanes = refine_roadlanes(road_lanes)

        lane_factory = categorize_roadlane(road_lanes)
        (image, baselines, segments) = lane_factory.run()
        for segment in segments:
            analyzer = Analyzer(image=image, lanelines=baselines, segment=segment)
            lane_dict = analyzer.search_laneline()
            analyzer.categorize_laneline(lane_dict)
            analyzer.visualize()
            # segment.generate_lanes()

    # cli()
