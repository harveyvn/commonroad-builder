import os
import sys
import click
import platform
import warnings
from pathlib import Path
from modules.crisce import extract_data_from_scenario
from modules.roadlane import categorize_roadlane, refine_roadlanes
from modules.analyzer import Analyzer
from modules.constant import CONST
from modules.process import run

warnings.filterwarnings('ignore')

if platform.system() == CONST.WINDOWS:
    from modules.crisce.simulation import Simulation

# Ensure PythonRobotics modules are included
root_folder = Path(Path(Path(__file__).parent).parent).absolute()
sys.path.append(os.path.join(root_folder, "PythonRobotics", "PathPlanning", "BezierPath"))
sys.path.append(os.path.join(root_folder, "PythonRobotics", "PathPlanning", "CubicSpline"))
sys.path.append(os.path.join(root_folder, "PythonRobotics", "PathPlanning", "BSplinePath"))


@click.group()
@click.option('--log-to', required=False, type=click.Path(exists=False),
              help="Location of the log file. If not specified logs appear on the console")
@click.option('--debug', required=False, is_flag=True, default=False, show_default='Disabled',
              help="Activate debugging (results in more logging)")
@click.pass_context
def cli(ctx, log_to, debug):
    # Pass the context of the command down the line
    ctx.ensure_object(dict)


@cli.command()
@click.option('--accident-sketch', required=True, type=click.Path(exists=True), multiple=False,
              help="Input accident sketch for generating the simulation")
@click.option('--output-to', required=False, type=click.Path(exists=False), multiple=False,
              help="Folder to store outputs. It will created if not present. If omitted we use the accident folder.")
@click.option('--beamng-home', required=False, type=click.Path(exists=True), multiple=False,
              help="Home folder of the BeamNG.research simulator")
@click.option('--beamng-user', required=False, type=click.Path(exists=True), multiple=False,
              help="User folder of the BeamNG.research simulator")
@click.pass_context
def generate(ctx, accident_sketch, output_to, beamng_home=None, beamng_user=None):
    # Pass the context of the command down the line
    ctx.ensure_object(dict)
    run(accident_sketch, output_to)


# Execute the Command Line Interpreter
if __name__ == '__main__':
    BASE_DIR = "cases/original"
    CASES = [100271, 103378, 105203, 105222, 108812, 117021, 119489, 119839, 120013, 120305, 121520, 122080, 122168,
             128066, 128697, 129224, 137748, 148154, 171831, 99817]

    for case in CASES:
        run(accident_sketch=f'{BASE_DIR}/{case}')
    cli()
    exit()
    # single = [99817, 100343, 102804, 105165, 108812, 109176, 109536, 117692, 135859, 142845]
    # parallel = [100, 101, 105222, 119897, 128719, 171831]
    # intersections = [100237, 103378, 117021]
    # 119839 - num_points=20
    # 128066 - num_points=12
    # 108812 - outlier_threshold = 0
    # 120305 - outlier_threshold = 0
    three_legs = [100271, 105203, 119489, 119839, 120013]
    for s in [128066]:
        path = f'CIREN/4roads/{s}'

        # Extract arrow direction
        # kernel = np.ones((2, 2))
        # img = cv2.imread(f'{path}/road.jpeg')
        # diff, cm = ArrowAnalyzer(kernel=kernel, img=img).run()
        # print(diff, cm)

        # Extract road lanes
        roads, lane_nodes, road_lanes, ratio = extract_data_from_scenario(path)

        if road_lanes["road_type"] > 0:
            road_lanes = refine_roadlanes(road_lanes)

        lane_factory = categorize_roadlane(road_lanes)
        (image, baselines, segments) = lane_factory.run()

        lines = []
        for i, segment in enumerate(segments):
            if i == 3:
                analyzer = Analyzer(image=image, lanelines=baselines, segment=segment)
                lane_dict = analyzer.search_laneline(num_points=12)
                lines = analyzer.categorize_laneline(lane_dict)
                analyzer.visualize()
                segment.generate_lanes(lines)
                print("==")
            # segment.get_bng_segment(0.4, True)
