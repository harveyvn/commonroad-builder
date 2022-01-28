import time
from typing import List

from beamngpy import BeamNGpy, Scenario, Road, Vehicle
from beamngpy.sensors import Electrics, Camera, Damage, Timer
import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
import numpy as np
import math
import cv2
from shapely.geometry import MultiLineString, Polygon
import pandas as pd
from shapely.geometry import LineString
import modules.crisce.common as common
from modules.models import LaneMarking
from modules.constant import CONST
from math import floor


class Simulation():

    def __init__(self, vehicles, roads, lane_nodes, kinematics, time_efficiency, output_folder,
                 car_length, car_width, car_length_sim, sketch_type_external, height, width,
                 crash_impact_model, road_lanes, sampling_frequency=10):
        self.crash_analysis_log = dict()
        self.crash_analysis_log["vehicles"] = dict()
        self.crash_analysis_log["roads"] = dict()
        self.bng = None
        self.scenario = None
        self.log = dict()
        self.output_folder = output_folder
        self.vehicles = vehicles
        self.roads = roads
        self.lane_nodes = lane_nodes
        self.kinematics = kinematics
        self.time_efficiency = time_efficiency
        self.car_length = car_length
        self.car_width = car_width
        self.car_length_sim = car_length_sim
        self.sketch_type_external = sketch_type_external
        self.height = height
        self.width = width
        self.process_number = 0
        self.crash_impact_model = crash_impact_model
        # This decides how frequently (in simulation steps) CRISCE records the state of the simulated vehicles
        self.sampling_frequency = sampling_frequency
        self.road_lanes = road_lanes

    def setupBeamngSimulation(self, file, beamng_port, beamng_home, beamng_user):
        t0 = time.time()

        # TODO Use GLOBAL Constants!
        # beamng = BeamNGpy('localhost', 64257, home="F:\\BeamNG\\BeamNG.research.v1.7.0.1")
        beamng = BeamNGpy('localhost', beamng_port, home=beamng_home, user=beamng_user)
        beamng = beamng.open(launch=True)
        scenario = Scenario('smallgrid', "{}".format(file))  # 'CRISCE')#
        # beamng.set_tod()
        electrics = Electrics()
        damage = Damage()
        timer = Timer()

        width_of_coverage = self.width * self.car_length_sim / self.car_length
        distorted_height = self.height * self.car_length_sim / self.car_length
        lane_midpoints = self.roads["small_lane_midpoints"]
        orig = lane_midpoints[0][len(lane_midpoints[0]) // 2]
        # cam_pos = (orig[0] - 5 , self.height - orig[1], width_of_coverage - 20)
        cam_pos = (orig[0] - 5, distorted_height - orig[1], width_of_coverage)
        cam_dir = (0, 1, -60)
        # Real World 3D picture of the crash sketch
        cam = Camera(cam_pos, cam_dir, 90, (2048, 2048), near_far=(1, 4000), colour=True)
        scenario.add_camera(cam, 'cam')

        road_id = ['main_road_1', 'main_road_2', 'main_road_3', 'main_road_4', 'main_road_5', 'main_road_6']
        for i, lane in enumerate(self.lane_nodes):
            left_marking_nodes = common.generate_left_marking(self.lane_nodes[i], floor(self.lane_nodes[i][0][-1]/2))
            left_marking = Road('line_white', rid=f'{road_id[i]}_left_white')
            left_marking.nodes.extend(left_marking_nodes)
            scenario.add_road(left_marking)

            right_marking_nodes = common.generate_right_marking(self.lane_nodes[i], floor(self.lane_nodes[i][0][-1]/2))
            right_marking = Road('line_white', rid=f'{road_id[i]}_right_white')
            right_marking.nodes.extend(right_marking_nodes)
            scenario.add_road(right_marking)

            if len(self.road_lanes[i].lane_markings) > 2:
                internal_lane_markings: List[LaneMarking] = self.road_lanes[i].lane_markings
                for idx, il in enumerate(internal_lane_markings[1:-1]):
                    cm_nodes = common.generate_right_marking(left_marking_nodes, floor(il.ratio * self.lane_nodes[i][0][-1]))
                    road_line = ""
                    if il.type == CONST.SINGLE_LINE or il.type == CONST.SINGLE_DASHED_LINE:
                        road_line = "line_yellow"
                    else:
                        road_line = "line_yellow_double"

                    central_marking = Road(road_line, rid=f'{road_id[i]}_central_{idx}')
                    central_marking.nodes.extend(cm_nodes)
                    scenario.add_road(central_marking)

            road = Road('road_asphalt_2lane', rid=road_id[i], interpolate=True)
            road.nodes.extend(self.lane_nodes[i])
            scenario.add_road(road)

        for vehicle_color in self.vehicles:
            self.crash_analysis_log["vehicles"][vehicle_color] = dict()
            script = self.vehicles[vehicle_color]["trajectories"]["script_trajectory"]
            angle = self.vehicles[vehicle_color]["vehicle_info"]["0"]["angle_of_car"]
            orig_pos = self.vehicles[vehicle_color]["snapshots"][0]["center_of_car"]
            x = orig_pos[0] * self.car_length_sim / self.car_length
            y = distorted_height - (orig_pos[1] * self.car_length_sim / self.car_length)
            # print("vehicle", vehicle_color, "postition = ", x, y)

            vehicle = Vehicle("{}_vehicle".format(vehicle_color),
                              model='etk800',
                              licence="{}_007".format(vehicle_color),
                              color=str.capitalize(vehicle_color))
            scenario.add_vehicle(vehicle, pos=(round(x, 1), round(y, 1), 0), rot=(0, 0, -angle - 90), rot_quat=None)
            # scenario.add_vehicle(vehicle, pos=( round(script[0]["x"], 3), round(script[0]["y"], 3), 0), rot=(0,0, -angle -90) , rot_quat=None)
            vehicle.attach_sensor('electrics', electrics)
            vehicle.attach_sensor("damage", damage)
            vehicle.attach_sensor("timer", timer)
            self.crash_analysis_log["vehicles"][vehicle_color]["vehicle"] = vehicle

        scenario.make(beamng)

        # bng.set_steps_per_second(20) #### One second is equal to sps(int) steps per simulation...
        # bng = beamng.open()
        beamng.load_scenario(scenario)
        # After loading, the simulator waits for further input to actually start
        beamng.start_scenario()
        # print(scenario._get_prefab())

        # This one on the mac takes ages to complete
        # TODO Is this necessary?
        # scenario.update()
        # frames = scenario.render_cameras()
        # plt.figure(figsize=(30, 30))
        # plt.imshow(np.asarray(frames['cam']['colour'].convert('RGB')))
        # plt.savefig(self.output_folder + '{}_aerial_camera.jpg'.format(self.process_number), dpi=250)
        # # plt.show()
        # plt.close()

        t1 = time.time()
        print("loaded beamng scenario in =", t1 - t0)
        self.time_efficiency["beamng_loaded"] = t1 - t0
        # self.bng = bng
        return beamng, scenario

    def aerialViewCamera(self):
        """ Aerial Camera setup for taking picture and monitoring the crash """
        width_of_coverage = max(self.height, self.width) * self.car_length_sim / self.car_length
        distorted_height = self.height * self.car_length_sim / self.car_length
        a_ratio = self.car_length_sim / self.car_length
        orig = [(self.height * a_ratio) // 2, (self.width * a_ratio) // 2]
        # cam_pos = (orig[0] - 10, self.height - orig[1], width_of_coverage - 20)
        cam_pos = (orig[0], distorted_height - orig[1], width_of_coverage)
        cam_dir = (0, 1, -60)
        self.bng.set_free_camera(cam_pos, cam_dir)

        # # Real World 3D picture of the crash sketch
        # cam = Camera(cam_pos, cam_dir, 80, (2048, 2048), near_far=(1, 4000), colour=True)
        # self.scenario.add_camera(cam, 'cam')
        # self.scenario.update()
        # frames = self.scenario.render_cameras()
        # plt.figure(figsize=(30, 30))
        # plt.imshow(np.asarray(frames['cam']['colour'].convert('RGB')))
        # plt.savefig(self.output_folder + '{}_aerial_camera.jpg'.format(self.process_number), dpi=150)
        # # plt.show()
        # plt.close()

    def plot_road(self, ax, print_road_values=True):
        # fig = plt.figure(figsize=(20, 17))
        # ax = fig.add_subplot(111)

        road_names_list = list(self.bng.get_roads().keys())
        road_geometry_edges = [self.bng.get_road_edges(road) for road in road_names_list]
        for i, road in enumerate(road_geometry_edges):
            self.crash_analysis_log["roads"][road_names_list[i]] = dict()

            left_edge_x = np.array([e['left'][0] for e in road])
            left_edge_y = np.array([e['left'][1] for e in road])
            right_edge_x = np.array([e['right'][0] for e in road])
            right_edge_y = np.array([e['right'][1] for e in road])
            simulation_road_width = np.sqrt(
                np.square(right_edge_x[0] - left_edge_x[0]) + np.square(right_edge_y[0] - left_edge_y[0]))
            x_min = min(left_edge_x.min(), right_edge_x.min())
            x_max = max(left_edge_x.max(), right_edge_x.max())
            y_min = min(left_edge_y.min(), right_edge_y.min())
            y_max = max(left_edge_y.max(), right_edge_y.max())
            simulation_road_length = np.sqrt(np.square(x_max - x_min) + np.square(y_max - y_min))
            if print_road_values:
                print("simulation_road_width = ", simulation_road_width)
                print("simulation_road_length = ", simulation_road_length)

            # simulation_road.append([simulation_road_width, simulation_road_length])
            self.crash_analysis_log["roads"][road_names_list[i]]["simulation_road_width"] = simulation_road_width
            self.crash_analysis_log["roads"][road_names_list[i]]["simulation_road_length"] = simulation_road_length

            x_min = x_min - 20  # We add/subtract 10 from the min/max coordinates to pad
            x_max = x_max + 20  # the area of the plot a bit
            y_min = y_min - 20
            y_max = y_max + 20
            ax.set_aspect('equal', 'datalim')
            # pyplot & bng coordinate systems have different origins
            ax.set_xlim(left=x_max, right=x_min)
            ax.set_ylim(bottom=y_max, top=y_min)  # so we flip them here
            ax.plot(left_edge_x, left_edge_y, 'k-')
            ax.plot(right_edge_x, right_edge_y, 'k-')
            # break

        # plt.gca().set_aspect("auto")
        # plt.axis(False)
        # plt.gca().invert_yaxis()
        # plt.gca().invert_xaxis()
        # plt.show()
        # plt.close()
        # plt.savefig("Internal_Validity\internal_road_7.jpg", bbox_inches='tight')
        # fig.savefig("Internal_Validity\internal_road_7.jpg", bbox_inches='tight')

    def getBboxRect(self, vehicle):
        bbox = vehicle.get_bbox()
        boundary_x = [
            bbox['front_bottom_left'][0],
            bbox['front_bottom_right'][0],
            bbox['rear_bottom_right'][0],
            bbox['rear_bottom_left'][0],
        ]
        boundary_y = [
            bbox['front_bottom_left'][1],
            bbox['front_bottom_right'][1],
            bbox['rear_bottom_right'][1],
            bbox['rear_bottom_left'][1],
        ]

        return bbox, boundary_x, boundary_y

    def extractingAngleUsingBbox(self, vehicle):
        bbox = self.getBboxRect(vehicle=vehicle)[0]
        fbl = bbox['front_bottom_left']
        fbr = bbox['front_bottom_right']
        rbr = bbox['rear_bottom_right']
        rbl = bbox['rear_bottom_left']
        ### Extracting the front the node and rear node of the car and using them for extracting the angle using arctan2
        front_node = ((fbl[0] + fbr[0]) / 2, (fbl[1] + fbr[1]) / 2)
        rear_node = ((rbl[0] + rbr[0]) / 2, (rbl[1] + rbr[1]) / 2)

        x = [(rear_node[0]), (front_node[0])]
        y = [(rear_node[1]), (front_node[1])]
        dy = y[1] - y[0]
        dx = x[1] - x[0]

        angle_of_vehicle = math.degrees(math.atan2(dy, dx))
        angle_of_vehicle = (-angle_of_vehicle if angle_of_vehicle < 0 else (-angle_of_vehicle + 360))
        angle_of_vehicle = -angle_of_vehicle + 360
        # print("angle = ", angle_of_vehicle)

        return angle_of_vehicle

    def computeTriangle(self, bbox):
        # format e.g [80.80281829833984, 15.481525421142578,   -0.031248807907104492]
        fbl = bbox['front_bottom_left']
        fbr = bbox['front_bottom_right']
        rbr = bbox['rear_bottom_right']
        rbl = bbox['rear_bottom_left']

        ### Midpoint of the Car
        mid_fbl_rbr = ((fbl[0] + rbr[0]) / 2, (fbl[1] + rbr[1]) / 2)
        mid_fbr_rbl = ((fbr[0] + rbl[0]) / 2, (fbr[1] + rbl[1]) / 2)

        tri_left = ((fbl[0] + mid_fbl_rbr[0]) / 2, (fbl[1] + mid_fbl_rbr[1]) / 2)
        tri_right = ((fbr[0] + mid_fbl_rbr[0]) / 2, (fbr[1] + mid_fbl_rbr[1]) / 2)
        tri_top = ((fbl[0] + fbr[0]) / 2, (fbl[1] + fbr[1]) / 2)

        return (tri_left, tri_right, tri_top)

    def centerOfRect(self, boundary_x, boundary_y):
        midpoint = (
            (boundary_x[0] + boundary_x[1] + boundary_x[2] + boundary_x[3]) / len(boundary_x),
            (boundary_y[0] + boundary_y[1] + boundary_y[2] + boundary_y[3]) / len(boundary_y)
        )
        return midpoint

    def plot_bbox_rect(self, ax, vehicle):
        bbox, boundary_x, boundary_y = self.getBboxRect(vehicle=vehicle)
        midpoint = self.centerOfRect(boundary_x, boundary_y)
        print("midpoint = ", midpoint)

        if vehicle.vid == "red_vehicle":
            ax.fill(boundary_x, boundary_y, 'r-')
        else:
            ax.fill(boundary_x, boundary_y, 'b-')

        triangle_coord = self.computeTriangle(bbox)
        # print(triangle_coord)
        # ax.Polygon(np.array(triangle_coord), closed=False, color="blue", alpha=0.3, fill=True, edgecolor=None)
        poly = plt.Polygon(np.array(triangle_coord), closed=False, color="white", alpha=1, fill=True, edgecolor=None)
        circle = plt.Circle((midpoint[0], midpoint[1]), 0.4, color='green')
        ax.add_patch(circle)
        ax.add_patch(poly)

    def plotSimulationCrashSketch(self):
        fig = plt.figure(figsize=(30, 20))
        plt.gca().set_aspect("auto")
        plt.axis('off')

        self.plot_road(plt.gca())
        # plot_script(plt.gca())

        for vehicle_color in self.vehicles:
            vehicle = self.crash_analysis_log["vehicles"][vehicle_color]["vehicle"]
            self.plot_bbox_rect(plt.gca(), vehicle)
            vehicle.update_vehicle()
            angle = self.extractingAngleUsingBbox(vehicle)
            self.crash_analysis_log["vehicles"][vehicle_color]["initial_position"] = vehicle.state['pos']
            self.crash_analysis_log["vehicles"][vehicle_color]["initial_direction"] = angle
            self.crash_analysis_log["vehicles"][vehicle_color]["init_bbox"] = self.getBboxRect(vehicle)[0]
            # self.crash_analysis_log["vehicles"][vehicle_color]["center_of_bbox"]    = self.centerOfRect(self.getBboxRect(vehicle=vehicle)[1],
            #                                                                                             self.getBboxRect(vehicle=vehicle)[2])
            print(vehicle_color, "vehicle \n\tinitial_positions = ", vehicle.state['pos'])
            print("\tAngle =", angle)
            # self.plot_bbox_rect(plt.gca(), vehicle)

        plt.gca().invert_yaxis()
        plt.gca().invert_xaxis()
        plt.savefig(self.output_folder + '{}_sim_initial_pos_dir.jpg'.format(self.process_number), bbox_inches='tight')
        self.process_number += 1
        # plt.show()
        plt.close()

    def eulerToDegree(self, euler):
        return ((euler) / (2 * np.pi)) * 360

    def eulerToQuat(self, angle):
        """ Converts an euler angle in degree to quaternion. """
        angle = np.radians(angle)

        cy = np.cos(angle[2] * 0.5)
        sy = np.sin(angle[2] * 0.5)
        cp = np.cos(angle[1] * 0.5)
        sp = np.sin(angle[1] * 0.5)
        cr = np.cos(angle[0] * 0.5)
        sr = np.sin(angle[0] * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy

        return (x, y, z, w)

    def initiateDrive(self):
        for vehicle_color in self.vehicles:
            self.bng.add_debug_line(points=self.vehicles[vehicle_color]["trajectories"]["debug_trajectory"],
                                    point_colors=self.vehicles[vehicle_color]["trajectories"]["point_colors"],
                                    spheres=self.vehicles[vehicle_color]["trajectories"]["spheres"],
                                    sphere_colors=self.vehicles[vehicle_color]["trajectories"]["sphere_colors"],
                                    cling=True,
                                    offset=0.1)

        # bng.step(10)

        # """ AI script must have at least 3 nodes """

        vehicle_red = self.crash_analysis_log["vehicles"]["red"]["vehicle"]
        vehicle_blue = self.crash_analysis_log["vehicles"]["blue"]["vehicle"]

        position_red = list()
        positions_blue = list()
        red_bbox = list()
        blue_bbox = list()
        speed_r = list()
        speed_b = list()
        direction_b = list()
        direction_r = list()
        sim_time_red = list()
        sim_time_blue = list()

        position_red.append(self.crash_analysis_log["vehicles"]["red"]["initial_position"])
        positions_blue.append(self.crash_analysis_log["vehicles"]["blue"]["initial_position"])

        t0 = time.time()
        if (len(self.vehicles["red"]["snapshots"]) > 1):
            vehicle_red.ai_set_mode('manual')
            vehicle_red.ai_set_script(self.vehicles["red"]["trajectories"]["script_trajectory"], cling=False)

        if (len(self.vehicles["blue"]["snapshots"]) > 1):
            vehicle_blue.ai_set_mode('manual')
            vehicle_blue.ai_set_script(self.vehicles["blue"]["trajectories"]["script_trajectory"], cling=False)

        self.bng.set_steps_per_second(160)
        self.bng.pause()
        self.bng.display_gui_message("Drive Initiated !!!")

        # time_out = 20
        while True:
            # time.sleep(0.1)
            # Synchs the vehicle's "state" variable with the simulator
            vehicle_red.update_vehicle()
            vehicle_blue.update_vehicle()
            red_bbox.append(self.getBboxRect(vehicle_red)[0])
            blue_bbox.append(self.getBboxRect(vehicle_blue)[0])
            red_sensors = self.bng.poll_sensors(vehicle=vehicle_red)
            blue_sensors = self.bng.poll_sensors(vehicle=vehicle_blue)
            wheelspeed_r = red_sensors["electrics"]["wheelspeed"] * 3.6
            wheelspeed_b = blue_sensors["electrics"]["wheelspeed"] * 3.6
            speed_r.append(red_sensors["electrics"]["wheelspeed"])
            speed_b.append(blue_sensors["electrics"]["wheelspeed"])
            direction_r.append(vehicle_red.state['dir'])
            direction_b.append(vehicle_blue.state['dir'])
            position_red.append(vehicle_red.state['pos'])
            positions_blue.append(vehicle_blue.state['pos'])
            sim_time_red.append(red_sensors["timer"]["time"])
            sim_time_blue.append(blue_sensors["timer"]["time"])
            if (red_sensors["damage"]["damage"] != 0 or blue_sensors["damage"][
                "damage"] != 0):  # or blue_sensors["damage"]["damage"] != 0):
                print("crashed !!!")
                if (wheelspeed_r < 7 or wheelspeed_b < 7):
                    print("vehicles came to halt")
                    break
            self.bng.step(self.sampling_frequency)

        self.bng.resume()

        t1 = time.time()
        print("\nBeamNG scenario executed in =", t1 - t0)
        self.time_efficiency["beamng_executed"] = t1 - t0

        self.crash_analysis_log["vehicles"]["red"]["final_bboxes"] = red_bbox
        self.crash_analysis_log["vehicles"]["blue"]["final_bboxes"] = blue_bbox
        self.crash_analysis_log["vehicles"]["red"]["simulation_trajectory"] = position_red
        self.crash_analysis_log["vehicles"]["blue"]["simulation_trajectory"] = positions_blue
        self.crash_analysis_log["vehicles"]["red"]["rotations"] = direction_r
        self.crash_analysis_log["vehicles"]["blue"]["rotations"] = direction_b
        self.crash_analysis_log["vehicles"]["red"]["wheel_speed"] = speed_r
        self.crash_analysis_log["vehicles"]["blue"]["wheel_speed"] = speed_b
        self.crash_analysis_log["vehicles"]["red"]["sim_time"] = sim_time_red
        self.crash_analysis_log["vehicles"]["blue"]["sim_time"] = sim_time_blue

    def postCrashDamage(self):
        t0 = time.time()
        is_crashed = False
        for vehicle_color in self.vehicles:
            vehicle = self.crash_analysis_log["vehicles"][vehicle_color]["vehicle"]
            vehicle_sensor = self.bng.poll_sensors(vehicle=vehicle)
            if (vehicle_sensor["damage"]["damage"] > 0):
                is_crashed = True
                # crash_analysis_log["vehicles"][vehicle_color]["simulation_damage"] = dict()
                self.crash_analysis_log["vehicles"][vehicle_color]["crashed_happened"] = is_crashed
                self.crash_analysis_log["vehicles"][vehicle_color]["simulation_damage"] = vehicle_sensor["damage"][
                    "part_damage"]
                print(vehicle.vid, "crash happened !!!")
        t1 = time.time()
        # print("total time", t1-t0)
        self.time_efficiency["eval_crash_damage"] = t1 - t0

    """1. Quality and Accuracy of Simulated Crash Impact Sides of the Vehicles """

    def effectAndAccurayOfSimulation(self):
        t0 = time.time()
        self.log["vehicles"] = dict()

        for vehicle_color in self.vehicles:
            self.log["vehicles"][vehicle_color] = dict()

            int_impact_side = self.vehicles[vehicle_color]["impact_point_details"]["internal_impact_side"]
            ref_impact_side_values = list(
                self.vehicles[vehicle_color]["impact_point_details"]["reference_deformations"])
            try:
                sim_impact_side_values = list(
                    self.crash_analysis_log["vehicles"][vehicle_color]["simulation_damage"].keys())
            except:
                sim_impact_side_values = ["Observed_No-Damage-Reported", "Observed_No-Damage-Reportedn"]
            lenght_of_ref_values = len(ref_impact_side_values)
            lenght_of_sim_values = len(sim_impact_side_values)

            sim_impact_side_values = [sim_side_value.split("_", maxsplit=1)[1] for sim_side_value in
                                      sim_impact_side_values]

            crash_damage = list()

            for crash_side in self.crash_impact_model:
                side_values = set(self.crash_impact_model[crash_side])
                sim_side_values = set(sim_impact_side_values)
                difference = side_values.difference(sim_side_values)
                diff_per = (1 - len(difference) / len(side_values)) * 100
                crash_damage.append([diff_per, crash_side, side_values, sim_side_values])
                # print("crash side calculation", [diff_per, crash_side, side_values, sim_side_values])

            crash_damage = np.array(crash_damage)
            print("\nCrash values reported by Beamng: \n", crash_damage[crash_damage[:, 0].argsort()][-3:])
            # print("\n crash values", crash_damage)
            crash_damage = crash_damage[crash_damage[:, 0].argsort()][-3:]

            for crash_values in crash_damage:

                crash_impact_hits = crash_values[0]
                sim_impact_side = crash_values[1]
                ref_side_values = list(crash_values[2])
                sim_side_values = list(crash_values[3])
                missed_values = list(crash_values[2].difference(crash_values[3]))
                out_of_bound = list(crash_values[3].difference(crash_values[2]))

                if crash_values[1] in ['front_left', 'front_right', 'front_mid']:
                    sim_impact_side = "front"
                elif crash_values[1] in ['rear_left', 'rear_mid', 'rear_right']:
                    sim_impact_side = "rear"
                elif crash_values[1] == "right_mid":
                    sim_impact_side = "right"
                elif crash_values[1] == "left_mid":
                    sim_impact_side = "left"

                if not self.sketch_type_external:
                    crash_impact_side = str.split(int_impact_side, "_")[0]
                    self.vehicles[vehicle_color]["impact_point_details"]["external_impact_side"] = "Internal"
                else:
                    ext_impact_side = self.vehicles[vehicle_color]["impact_point_details"]["external_impact_side"]
                    crash_impact_side = str.lower(ext_impact_side)

                crash_impact_match = crash_values[0]
                crash_impact_hits = len(
                    list(crash_values[2].intersection(crash_values[3])))  # len(sim_side_values) - len(missed_values)
                # crash_impact_hits   = (crash_impact_hits if crash_impact_hits >= 0 else 0)
                crash_impact_miss = len(missed_values)

                if sim_impact_side == crash_impact_side:
                    break

            print("\n")
            print("Vehicle", str.capitalize(vehicle_color))
            print("reference impact points from the crash sketch: ")
            print("\t", ref_side_values)
            print("count of reference impact points: ", len(ref_side_values))

            print("simulation impact points from the sensor damage: ")
            print("\t", sim_impact_side_values)
            print("count of simulation impact points: ", lenght_of_sim_values)

            self.crash_analysis_log["vehicles"][vehicle_color]["crash_side_generic"] = str.capitalize(crash_impact_side)
            self.crash_analysis_log["vehicles"][vehicle_color]["crash_side_specific"] = int_impact_side
            self.crash_analysis_log["vehicles"][vehicle_color]["crash_impact_match"] = crash_impact_match
            self.crash_analysis_log["vehicles"][vehicle_color]["crash_side_match"] = (
                    sim_impact_side == crash_impact_side)
            self.crash_analysis_log["vehicles"][vehicle_color]["crash_impact_hits"] = crash_impact_hits
            self.crash_analysis_log["vehicles"][vehicle_color]["crash_impact_miss"] = crash_impact_miss
            self.crash_analysis_log["vehicles"][vehicle_color]["missed_values"] = missed_values
            self.crash_analysis_log["vehicles"][vehicle_color]["out_of_bound"] = out_of_bound

            #### ---- For Storing  the log in the excel file for data analysis------- ####
            self.log["vehicles"][vehicle_color]["crash_side_generic"] = str.capitalize(crash_impact_side)
            self.log["vehicles"][vehicle_color]["crash_side_specific"] = int_impact_side
            self.log["vehicles"][vehicle_color]["crash_impact_match"] = crash_impact_match
            self.log["vehicles"][vehicle_color]["crash_side_match"] = (sim_impact_side == crash_impact_side)
            self.log["vehicles"][vehicle_color]["crash_impact_hits"] = crash_impact_hits
            self.log["vehicles"][vehicle_color]["crash_impact_miss"] = crash_impact_miss
            self.log["vehicles"][vehicle_color]["missed_values"] = missed_values
            self.log["vehicles"][vehicle_color]["out_of_bound"] = out_of_bound

            print("\nEffectiveness of simulation ")
            print("Hits = ", int(crash_impact_hits))
            print("Miss = ", len(missed_values))
            print("Crash Impact Side by CRISCE      = ", str.capitalize(crash_impact_side))
            if self.sketch_type_external:
                print("External Impact Side             = ",
                      str.capitalize(self.vehicles[vehicle_color]["impact_point_details"]["external_impact_side"]))
            print("Crash Impact Side Observed       = ", str.capitalize(crash_values[1]))  # .split("_")[0]))
            # print("Crash Impact Hits Percentage     = ", int((len(sim_side_values) - len(missed_values)) / len(ref_side_values) * 100), "%")
            print("Crash Impact Miss Percentage     = ", int(len(missed_values) / len(ref_side_values) * 100), "%")
            print("Crash Impact Match Succussfull   = ", crash_impact_match, "%")
            print("Crash Impact Side Match          = ", (sim_impact_side == crash_impact_side))
            print("Crash Impact Miss Values         = ", missed_values)
            print("Crash Impact Out-of-bound Values = ", out_of_bound)

        print("\n\n\nACCURACY OF THE SIMULATED IMPACTS")
        impact_acc_red = 50 * self.crash_analysis_log["vehicles"]["red"]["crash_side_match"]
        impact_acc_blue = 50 * self.crash_analysis_log["vehicles"]["blue"]["crash_side_match"]

        if (impact_acc_red + impact_acc_blue) == 100:
            print("TOTAL MATCH")
            simulated_impact = "TM"
        elif (impact_acc_red + impact_acc_blue) == 50:
            print("PARTIAL MATCH")
            simulated_impact = "PM"
        else:
            print("NO MATCH")
            simulated_impact = "NM"

        self.crash_analysis_log["vehicles"][vehicle_color]["simulated_impact"] = simulated_impact

        #### ---- For Storing  the log in the excel file for data analysis------- ####
        self.log["simulated_impact"] = simulated_impact

        t1 = time.time()
        print("\nBeamNG evaluation -- side impact calculated in =", t1 - t0)
        self.time_efficiency["eval_side_impact"] = t1 - t0

    """ 
    2. Quality of Environment:
        a. Road Geometry: Sketch roads comparison with Simulation roads (widths and lengths of the lanes).
        b. Initial Placement of the vehicles: Comparison of the initial vehicle placement in the sketch to the placement in the simulation.
        c. Orientation of Vehicles: Comparison of the orientation of the vehicles from sketch to simulation.
    """

    def distanceMetricComputation(self, point_1, point_2):
        return np.linalg.norm(point_1 - point_2)

    def geometricDifference(self, value_1, value_2):
        return (100 - (value_1 / value_2) * 100)

    ### a. Road Geometry

    def computeRoadGeometricSimilarity(self):
        t0 = time.time()
        road_geometry = 0
        # number_of_roads = 0

        try:
            for i in range(0, len(self.lane_nodes)):
                del self.crash_analysis_log["roads"][f'main_road_{i + 1}_right_white']
                del self.crash_analysis_log["roads"][f'main_road_{i + 1}_left_white']
                if len(self.road_lanes[i].lane_markings) > 2:
                    internal_lane_markings = self.road_lanes[i].lane_markings.copy()
                    print(len(internal_lane_markings))
                    for x in range(0, len(internal_lane_markings)-2):
                        del self.crash_analysis_log["roads"][f'main_road_{i + 1}_central_{x}']

        except Exception as e:
            print(f'Exception: {e}')

        for i, road_name in enumerate(self.crash_analysis_log["roads"]):
            sim_road_width = self.crash_analysis_log["roads"][road_name]["simulation_road_width"]
            sim_road_length = self.crash_analysis_log["roads"][road_name]["simulation_road_length"]
            sketch_road_width = self.roads["scaled_lane_width"][i]
            sketch_road_length = self.roads["scaled_lane_length"][i]
            width_similarity, length_similarity = False, False

            ### 1st Approach as the simulation values for road uses the Cat-Rom-Mull splines so the values will always
            ### be greater than the sketch values as the values elongated by the splines to ensures the smooth curves.
            if sim_road_width > sketch_road_width:
                width_similarity = True
            if sim_road_length > sketch_road_length:
                length_similarity = True
            if width_similarity == False or length_similarity == False:
                width_similarity = math.isclose(sim_road_width, sketch_road_width, abs_tol=6)
                length_similarity = math.isclose(sim_road_length, sketch_road_length, abs_tol=6)

            ### 2st Approach takes the difference between the sketch and simulation and the using geometric difference
            ### gives us the value for the either lenght or the width of the road.
            # width_difference    = self.distanceMetricComputation(np.array(sim_road_width), np.array(sketch_road_width))
            # width_similarity    = self.geometricDifference(width_difference, sketch_road_width)
            # length_difference   = self.distanceMetricComputation(np.array(sim_road_length), np.array(sketch_road_length))
            # length_similarity   = self.geometricDifference(length_difference, sketch_road_length)
            # road_similarity     = (0.5 * width_similarity + 0.5 * length_similarity) / 100

            self.crash_analysis_log["roads"][road_name]["width_similarity"] = width_similarity
            self.crash_analysis_log["roads"][road_name]["length_similarity"] = length_similarity
            if (width_similarity and length_similarity):
                road_similarity = 1
            elif (width_similarity or length_similarity):
                road_similarity = 0.5
            else:
                road_similarity = 0
            self.crash_analysis_log["roads"][road_name]["road_similarity"] = road_similarity
            road_geometry += road_similarity
            # number_of_roads += 1

            print(road_name)
            print("\tsketch road width      = ", sketch_road_width)
            print("\tsimulation road width  = ", sim_road_width)
            print("\tsketch road length     = ", sketch_road_length)
            print("\tsimulation road length = ", sim_road_length)
            print("\troad width similar     =  {} %", width_similarity)
            print("\troad length similar    =  {} %", length_similarity)
            print("\troad geomerty similar  =  {} %".format(road_similarity * 100))

        ## Calculating the road geometry similarity for the environment

        t1 = time.time()
        print("\nBeamNG evaluation -- Road Geometry calculated in =", t1 - t0)
        self.time_efficiency["eval_quality_road_geom"] = t1 - t0

        road_similarity = (road_geometry / len(self.crash_analysis_log["roads"]) * 100)

        #### ---- For Storing  the log in the excel file for data analysis------- ####
        self.log["road_similarity"] = road_similarity

        return road_similarity

    ### b and c. Initial Placement and Orientation of the Vehicles

    def computeVehiclesSimilarity(self):
        """ Compute Red and Blue Vehicle Orientataion and Initial placement Similarity """
        t0 = time.time()
        pos_sim = 0
        distorted_height = self.height * self.car_length_sim / self.car_length
        orient_sim = 0
        for vehicle_color in self.vehicles:
            # script_pos   = self.vehicles[vehicle_color]["trajectories"]["script_trajectory"]
            skt_pos = self.vehicles[vehicle_color]["snapshots"][0]["center_of_car"]
            x = skt_pos[0] * self.car_length_sim / self.car_length
            y = distorted_height - (skt_pos[1] * self.car_length_sim / self.car_length)
            # print("vehicle", vehicle_color, "postition = ", x, y)
            init_skt_pos = [x, y, 0]
            init_skt_dir = [self.vehicles[vehicle_color]["vehicle_info"]["0"]["angle_of_car"]]
            init_sim_pos = self.crash_analysis_log["vehicles"][vehicle_color]["initial_position"]
            init_sim_dir = [self.crash_analysis_log["vehicles"][vehicle_color]["initial_direction"]]

            position_distance = self.distanceMetricComputation(np.array(init_skt_pos), np.array(init_sim_pos))
            orientation_distance = self.distanceMetricComputation(np.array(init_skt_dir), np.array(init_sim_dir))
            position_similarity = (True if (position_distance < 2) else False)
            orientation_similarity = (True if (orientation_distance < 2) else False)
            self.crash_analysis_log["vehicles"][vehicle_color]["pos_sim"] = position_similarity
            self.crash_analysis_log["vehicles"][vehicle_color]["orient_sim"] = orientation_similarity
            pos_sim += position_similarity
            orient_sim += orientation_similarity

            print("\n", str.capitalize(vehicle_color), "Vehicle")
            print("\tinit_skt_pos =", init_skt_pos)
            print("\tinit_sim_pos =", init_sim_pos)
            print("\tinit_skt_dir =", init_skt_dir)
            print("\tinit_sim_dir =", init_sim_dir)
            print("\tsketch and simulation vehicle positions are similar    = ",
                  (True if (position_distance < 1) else False))
            print("\tsketch and simulation vehicle orientations are similar = ",
                  (True if (orientation_distance < 1) else False))

        t1 = time.time()
        print("\nBeamNG evaluation -- quality of Vehicle Orientataion and Initial placement calculated in =", t1 - t0)
        self.time_efficiency["eval_quality_orien_pos"] = t1 - t0

        #### ---- For Storing  the log in the excel file for data analysis------- ####
        placement_similarity = pos_sim / len(self.vehicles) * 100
        orientation_similarity = orient_sim / len(self.vehicles) * 100
        self.log["placement_similarity"] = placement_similarity
        self.log["orientation_similarity"] = orientation_similarity

        return (placement_similarity, orientation_similarity)

    def computeSimVehBboxCoord(self, sim_box):
        # sim_box = self.crash_analysis_log["vehicles"][v_color]["init_bbox"]
        distorted_height = self.height * self.car_length_sim / self.car_length
        fbl = sim_box['front_bottom_left'][:2]
        fbr = sim_box['front_bottom_right'][:2]
        rbr = sim_box['rear_bottom_right'][:2]
        rbl = sim_box['rear_bottom_left'][:2]
        sim_veh = np.asarray([fbl, fbr, rbr, rbl])
        sim_veh = np.array([tuple([temp[0], distorted_height - temp[1]]) for temp in sim_veh])
        sim_veh = sim_veh * self.car_length / self.car_length_sim
        # sim_veh  = np.int0(sim_veh)
        sim_veh = sim_veh.tolist()
        # sim_veh  = [tuple([temp[0], temp[1]]) for temp in sim_veh]
        return sim_veh

    def computeSktVehBboxCoord(self, v_color, snap_id):
        skt_veh = self.vehicles[v_color]["snapshots"][snap_id]["min_area_rect"]
        skt_veh = cv2.boxPoints(skt_veh)
        # skt_veh = np.int0(skt_veh)
        skt_veh = skt_veh.tolist()
        # skt_veh = [tuple(temp) for temp in skt_veh]
        return skt_veh

    def midOfVehicle(self, bbox):
        midpoint = ((bbox[0][0] + bbox[1][0] + bbox[2][0] + bbox[3][0]) / len(bbox),
                    (bbox[0][1] + bbox[1][1] + bbox[2][1] + bbox[3][1]) / len(bbox))
        return midpoint

    def createRectangle(self, image, box_points, color):
        for i in range(len(box_points) - 1):
            cv2.line(image, box_points[i], box_points[i + 1], color, thickness=2)
        cv2.line(image, box_points[0], box_points[-1], color, thickness=2)

    """ 
    3. Computing the Bounding Box trajectory Accuracy, IOU and Displacement Error
        a. Accuracy for the BBOX trajectory
        b. IOU (Overlap) Error
        c. Displacement Error
    """

    def computeBboxTrajectory(self, bbox_image, show_image):
        t0 = time.time()
        # bbox_image = image.copy()
        count = 0

        for v_color in self.vehicles:
            veh_iou = 0
            displacement = 0
            for snap_id in range(len(self.vehicles[v_color]["snapshots"])):
                skt_veh = self.computeSktVehBboxCoord(v_color, snap_id)
                high_iou_values = list()
                for sim_veh_bbox in self.crash_analysis_log["vehicles"][v_color]["final_bboxes"]:
                    sim_veh = self.computeSimVehBboxCoord(sim_veh_bbox)
                    skt_veh_poly = Polygon(skt_veh)
                    sim_veh_poly = Polygon(sim_veh)
                    iou = skt_veh_poly.intersection(sim_veh_poly).area / skt_veh_poly.union(sim_veh_poly).area
                    # print(iou)
                    if ((iou * 100) > 10):
                        high_iou_values.append([iou, skt_veh, sim_veh])
                    else:
                        continue

                high_iou_values = np.array(high_iou_values)
                # print("high IoU values = ", high_iou_values)
                if len(high_iou_values) < 1:
                    continue
                # print("high IoU values = ", high_iou_values[high_iou_values[:,0].argsort()])
                highest_iou = high_iou_values[high_iou_values[:, 0].argsort()][-1]
                # print("Highest IoU = ", highest_iou)
                highest_iou = highest_iou.tolist()
                iou = highest_iou[0]
                skt_veh = highest_iou[1]
                sim_veh = highest_iou[2]
                # print("sketch vehicle midpoint      = ", midOfVehicle(skt_veh))
                # print("simulation vehicle midpoint  = ", midOfVehicle(sim_veh))
                aspect_ratio = self.car_length_sim / self.car_length
                d_error = self.distanceMetricComputation(np.array(self.midOfVehicle(skt_veh)),
                                                         np.array(self.midOfVehicle(sim_veh))) * aspect_ratio
                displacement = displacement + d_error
                # displacement_error.append((True if (d_error    < 5) else False))

                # self.distanceMetricComputation(np.array(init_skt_pos), np.array(init_sim_pos))
                # orientation_distance   = self.distanceMetricComputation(np.array(init_skt_dir), np.array(init_sim_dir))
                # position_similarity    = (True if (position_distance    < 2) else False)

                print("\nVehicle", v_color)
                print("\tVehicle snapshot   =", snap_id)
                print("\tIOU                = {} %".format(round(iou * 100, 2)))
                print("\tDisplacement Error in pixel(s)         =", d_error / aspect_ratio)
                print("\tDisplacement Error in meter(s)         =", d_error)
                print("\tTotal Displacement Error in meter(s)   =", displacement)
                # if ((iou*100) > 50):
                #     veh_iou +=1
                # else:
                #     veh_iou +=0

                if snap_id == (len(self.vehicles[v_color]["snapshots"]) - 1):
                    self.crash_analysis_log["vehicles"][v_color]["crash_veh_disp_error"] = d_error
                    self.crash_analysis_log["vehicles"][v_color]["crash_veh_IOU"] = round(iou * 100, 2)
                    self.log["vehicles"][v_color]["crash_veh_disp_error"] = d_error
                    self.log["vehicles"][v_color]["crash_veh_IOU"] = round(iou * 100, 2)
                else:
                    self.crash_analysis_log["vehicles"][v_color]["crash_veh_disp_error"] = "Undefined"
                    self.crash_analysis_log["vehicles"][v_color]["crash_veh_IOU"] = round(iou * 100, 2)
                    self.log["vehicles"][v_color]["crash_veh_disp_error"] = "Undefined"
                    self.log["vehicles"][v_color]["crash_veh_IOU"] = round(iou * 100, 2)

                veh_iou += iou * 100
                count += 20
                cv2.putText(bbox_image, "IoU: {:.2f}%".format(iou * 100), (10, 0 + count), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 255, 0), 2)
                skt_veh = np.int0(skt_veh)
                sim_veh = np.int0(sim_veh)
                sim_veh = [tuple([temp[0], temp[1]]) for temp in sim_veh]
                skt_veh = [tuple(temp) for temp in skt_veh]

                # sketch vehicle BBox
                self.createRectangle(bbox_image, skt_veh, (0, 255, 0))
                # simulator vehicle BBox
                self.createRectangle(bbox_image, sim_veh, (0, 64, 255))

                # for i in range(len(skt_veh)):
                # cv2.circle(bbox_image, skt_veh[i], 3, (0, 255, 0), -1) ## sketch vehicle BBox
                # cv2.circle(bbox_image, sim_veh[i], 3, (0, 128, 255), -1) ## simulator vehicle BBox
                # cv2.imshow("bbox_image", bbox_image)
                if show_image:
                    cv2.imshow("bbox_image", bbox_image)
                    cv2.waitKey(400)

            self.crash_analysis_log["vehicles"][v_color]["cum_iou"] = (veh_iou / (
                    len(self.vehicles[v_color]["snapshots"]) * 100)) * 100
            self.crash_analysis_log["vehicles"][v_color]["cum_iou_error"] = 100 - self.crash_analysis_log["vehicles"][
                v_color]["cum_iou"]
            self.crash_analysis_log["vehicles"][v_color]["displacement_error"] = displacement / len(
                self.vehicles[v_color]["snapshots"])

            #### ---- For Storing  the log in the excel file for data analysis------- ####
            self.log["vehicles"][v_color]["cum_iou"] = (veh_iou / (
                        len(self.vehicles[v_color]["snapshots"]) * 100)) * 100
            self.log["vehicles"][v_color]["cum_iou_error"] = 100 - self.crash_analysis_log["vehicles"][v_color][
                "cum_iou"]
            self.log["vehicles"][v_color]["displacement_error"] = displacement / len(
                self.vehicles[v_color]["snapshots"])

            print("\nAccuracy for the BBOX trajectory of the {} vehicles = {} % ".format(
                v_color, (veh_iou / (len(self.vehicles[v_color]["snapshots"]) * 100)) * 100))
            print("\nIOU (Overlap) Error =", self.crash_analysis_log["vehicles"][v_color]["cum_iou_error"])
            print("\nDisplacement Error ", displacement / len(self.vehicles[v_color]["snapshots"]))
        print("Overall Average IOU = ",
              (self.crash_analysis_log["vehicles"]["red"]["cum_iou"] +
               self.crash_analysis_log["vehicles"]["blue"]["cum_iou"]) / 2)

        cv2.imwrite(self.output_folder + '{}_sim_bbox_traj.jpg'.format(self.process_number), bbox_image)
        self.process_number += 1
        cv2.destroyAllWindows()
        t1 = time.time()
        print("\nBeamNG evaluation -- trajectory of movement in simulation =", t1 - t0)
        self.time_efficiency["eval_quality_traj"] = t1 - t0

    def computeSimulationAccuracy(self, road_similarity, placement_similarity, orientation_similarity):
        quality_of_environment = 0.33 * (
                0.33 * road_similarity + 0.33 * placement_similarity + 0.34 * orientation_similarity)
        quality_of_crash = 0.34 * (50 * self.crash_analysis_log["vehicles"]["red"]["crash_side_match"] +
                                   50 * self.crash_analysis_log["vehicles"]["blue"]["crash_side_match"])
        quality_of_trajecory = 0.33 * (0.5 * self.crash_analysis_log["vehicles"]["red"]["cum_iou"] +
                                       0.5 * self.crash_analysis_log["vehicles"]["blue"]["cum_iou"])
        simulation_accuracy = quality_of_environment + quality_of_crash + quality_of_trajecory

        print("\n")
        print("Quality_of_environment = {}, quality_of_crash = {}, quality_of_trajecory = {}".format(
            quality_of_environment, quality_of_crash, quality_of_trajecory))
        print("Crash Simulation Accuracy = ", simulation_accuracy, "%")

        #### ---- For Storing  the log in the excel file for data analysis------- ####
        self.log["red_side_match"] = self.crash_analysis_log["vehicles"]["red"]["crash_side_match"]
        self.log["blue_side_match"] = self.crash_analysis_log["vehicles"]["blue"]["crash_side_match"]
        self.log["red_cum_iou"] = self.crash_analysis_log["vehicles"]["red"]["cum_iou"]
        self.log["blue_cum_iou"] = self.crash_analysis_log["vehicles"]["blue"]["cum_iou"]
        self.log["quality_of_env"] = quality_of_environment
        self.log["quality_of_crash"] = quality_of_crash
        self.log["quality_of_traj"] = quality_of_trajecory
        self.log["simulation_accuracy"] = simulation_accuracy

        return simulation_accuracy

    def computeCrisceEfficiency(self):
        print("red cummulative IOU = {}, blue cummulative IOU = {}".format(
            self.crash_analysis_log["vehicles"]["red"]["cum_iou"],
            self.crash_analysis_log["vehicles"]["blue"]["cum_iou"]))

        vehicle_ext_time = self.time_efficiency["preprocess"] + self.time_efficiency["calc_crash_pt"] + \
                           self.time_efficiency["seq_movement"] + \
                           self.time_efficiency["tri_ext"] + self.time_efficiency["angle_cal"] + \
                           self.time_efficiency["oriented_nodes"] + self.time_efficiency["skt_veh_impact"]

        roads_ext_time = self.time_efficiency["road_ext"]

        traj_ext_time = self.time_efficiency["ext_snapshots"] + self.time_efficiency["ext_waypoint"] + \
                        self.time_efficiency["compute_bezier"] + \
                        self.time_efficiency["script_traj"]

        beamng_exe_time = self.time_efficiency["beamng_loaded"] + self.time_efficiency["beamng_executed"]

        eval_ext_time = self.time_efficiency["eval_crash_damage"] + self.time_efficiency["eval_side_impact"] + \
                        self.time_efficiency["eval_quality_road_geom"] + self.time_efficiency[
                            "eval_quality_orien_pos"] + \
                        self.time_efficiency["eval_quality_traj"]

        total_time = {"vehicles_extraction": vehicle_ext_time,
                      "roads_extraction": roads_ext_time,
                      "trajectory_extraction": traj_ext_time,
                      "beamng_execution": beamng_exe_time,
                      "evaluation_time": eval_ext_time}

        #### ---- For Storing  the log in the excel file for data analysis------- ####
        self.log["total_time"] = total_time

        return total_time

    def full_extent(self, ax, pad=0.0):
        """Get the full extent of an axes, including axes labels, tick labels, and
        titles."""
        # For text objects, we need to draw the figure first, otherwise the extents
        # are undefined.
        ax.figure.canvas.draw()
        items = ax.get_xticklabels() + ax.get_yticklabels()
        # items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
        items += [ax, ax.title]
        bbox = Bbox.union([item.get_window_extent() for item in items])

        return bbox.expanded(1.1 + pad, 1.1 + pad)

    def plotCrisceEfficiency(self, total_time):
        # fig = plt.figure(figsize=(20,10))
        fig, (ax1, ax2) = plt.subplots(nrows=1, ncols=2, figsize=(16, 8))
        df1 = pd.DataFrame([total_time], columns=['vehicles_extraction', 'roads_extraction', 'trajectory_extraction',
                                                  'evaluation_time'])
        df2 = pd.DataFrame([total_time], columns=list(total_time.keys()))

        # Use ax1 to plot Time efficiency of CRISCE
        df1.plot(kind="bar", ax=ax1, title="Time efficiency of CRISCE")
        # ax1.set_title("Time efficiency of CRISCE")
        ax1.set_xticklabels(['values '], rotation="0")
        ax1.set_ylabel("time in seconds")
        extent_1 = self.full_extent(ax1).transformed(fig.dpi_scale_trans.inverted())
        fig.savefig(self.output_folder + '{}_crisce_efficiency.jpg'.format(self.process_number), bbox_inches=extent_1)

        # Use ax2 to plot Time efficiency of CRISCE without BeamNG execution
        df2.plot(kind="bar", ax=ax2, title="Time efficiency of CRISCE without BeamNG execution")
        # ax2.set_title("Time efficiency of CRISCE without BeamNG execution")
        ax2.set_xticklabels(['values '], rotation="0")
        ax2.set_ylabel("time in seconds")
        extent_2 = self.full_extent(ax2).transformed(fig.dpi_scale_trans.inverted())
        fig.savefig(self.output_folder + '{}_crisce_beamng_efficiency.jpg'.format(self.process_number),
                    bbox_inches=extent_2)

        # If you don't do tight_layout() you'll have weird overlaps
        plt.tight_layout()
        self.process_number += 1
        # plt.show()
        plt.close()

    def plot_crash(self, vehicle_red, vehicle_blue):
        self.plot_road(plt.gca())
        # self.plot_script(ax[row, 0])
        # self.plot_bbox(plt.gca())
        self.plot_bbox_rect(plt.gca(), vehicle=vehicle_red)
        self.plot_bbox_rect(plt.gca(), vehicle=vehicle_blue)
        # self.plot_overhead(ax[row, 1])

        plt.grid(False)
        plt.axis(False)
        plt.gca().invert_xaxis()
        plt.gca().invert_yaxis()
        # plt.show()
        plt.close()

    def traceVehicleBbox(self):
        Bbox = dict()
        vehicle_red = self.crash_analysis_log["vehicles"]["red"]["vehicle"]
        vehicle_blue = self.crash_analysis_log["vehicles"]["blue"]["vehicle"]
        Bbox[vehicle_red.vid] = self.crash_analysis_log["vehicles"]["red"]["final_bboxes"]
        Bbox[vehicle_blue.vid] = self.crash_analysis_log["vehicles"]["blue"]["final_bboxes"]
        # plt.figure(figsize=(30, 10))
        fig_traj, ax = plt.subplots(1, figsize=(30, 20))
        self.plot_road(ax, False)

        for vehicle in Bbox.keys():
            for i, veh_bbox in enumerate(Bbox[vehicle]):
                bbox = veh_bbox
                # boundary_x = veh_bbox[1]
                # boundary_y = veh_bbox[2]
                # bbox = vehicle.get_bbox()
                boundary_x = [
                    bbox['front_bottom_left'][0],
                    bbox['front_bottom_right'][0],
                    bbox['rear_bottom_right'][0],
                    bbox['rear_bottom_left'][0],
                ]
                boundary_y = [
                    bbox['front_bottom_left'][1],
                    bbox['front_bottom_right'][1],
                    bbox['rear_bottom_right'][1],
                    bbox['rear_bottom_left'][1],
                ]

                ax.fill(boundary_x, boundary_y, "r")
                if vehicle == "red_vehicle":
                    ax.fill(boundary_x, boundary_y, 'r-')
                else:
                    ax.fill(boundary_x, boundary_y, 'b-')

                triangle_coord = self.computeTriangle(bbox)
                # print(triangle_coord)
                # ax.Polygon(np.array(triangle_coord), closed=False, color="blue", alpha=0.3, fill=True, edgecolor=None)
                poly = plt.Polygon(np.array(triangle_coord), closed=False,
                                   color="white", alpha=1, fill=True, edgecolor=None)
                ax.add_patch(poly)

        # bounding_boxes_red.append(self.getBboxRect(vehicle=vehicle_red)[1:])
        # bounding_boxes_blue.append(self.getBboxRect(vehicle=vehicle_blue)[1:])

        # self.plot_bbox_rect(plt.gca(), vehicle=vehicle_red)
        # self.plot_bbox_rect(plt.gca(), vehicle=vehicle_blue)
        ### plot_overhead(ax[row, 1])

        plt.axis('off')

        plt.grid(False)
        plt.axis(False)
        plt.gca().invert_xaxis()
        plt.gca().invert_yaxis()
        plt.savefig(self.output_folder + '{}_trace_veh_BBOX.jpg'.format(self.process_number), bbox_inches='tight')
        self.process_number += 1
        # plt.show()
        plt.close()

    def close(self):
        self.bng.close()
