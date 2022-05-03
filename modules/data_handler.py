import json
from typing import List
import pathlib
from modules.models.bng_segment import BngSegement
from modules.crisce.vehicle import Vehicle
from modules.common import intersect
from shapely.geometry import LineString


class DataHandler:
    def __init__(self, vehicles: List[Vehicle], roads: List[BngSegement], sketch_name: str, rot_deg: int):
        self.vehicles = vehicles
        self.roads = roads
        self.sketch_name = sketch_name
        self.rot_deg = rot_deg

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

        return [v.obj_dict() for v in self.vehicles], intersection

    def roads2json(self):
        print("Number of roads: ", len(self.roads))

        roads = []
        for i, road in enumerate(self.roads):
            item = {
                "left": road.left.__dict__,
                "center": road.center.__dict__,
                "right": road.right.__dict__,
                "marks": [m.__dict__ for m in road.marks],
                "width": road.width,
            }
            roads.append(item)

        return roads

    def to_json(self):
        vehicles, crash_point = self.vehicles2json()
        roads = self.roads2json()

        data = {
            "roads": roads,
            "vehicles": vehicles,
            "crash_point": crash_point,
            "rot_deg": self.rot_deg
        }

        # Using a JSON string
        json_string = json.dumps(data)

        # Create a folder and filename
        pathlib.Path(f'outputs/{self.sketch_name}/').mkdir(parents=True, exist_ok=True)
        with open(f'outputs/{self.sketch_name}/data.json', 'w') as outfile:
            outfile.write(json_string)
        print(f'Output is written to outputs/{self.sketch_name}/ !')
