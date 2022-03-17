import json
from typing import List
from modules.models.bng_segment import BngSegement
from modules.crisce.vehicle import Vehicle
from modules.common import intersect
from shapely.geometry import LineString


class DataHandler:
    def __init__(self, vehicles: List[Vehicle], roads: List[BngSegement], sketch_name: str):
        self.vehicles = vehicles
        self.roads = roads
        self.sketch_name = sketch_name

    def vehicles2json(self):
        print("Number of vehicles: ", len(self.vehicles))

        list_lst = []
        intersection = []
        for v in self.vehicles:
            coords = [(p['x'], p['y']) for p in v.script]
            if len(coords) == 1:
                intersection = coords
                break
            list_lst.append(LineString(coords))

        if len(intersection) == 0:
            intersection = intersect(list_lst)

        data = {"vehicles": [v.obj_dict() for v in self.vehicles], "crash_point": intersection}
        json_string = json.dumps(data)

        # Using a JSON string
        with open(f'cases/{self.sketch_name}-vehicles.json', 'w') as outfile:
            outfile.write(json_string)

    def roads2json(self):
        print("Number of roads: ", len(self.roads))
        # data = {"roads": [r for r in self.roads]}
        # json_string = json.dumps(data)
        #
        # # Using a JSON string
        # with open(f'cases/{self.sketch_name}-roads.json', 'w') as outfile:
        #     outfile.write(json_string)
