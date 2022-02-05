class Constant:
    def __init__(self):
        self.ROAD_CURVE_OR_STRAIGHT = 0
        self.ROAD_INTERSECTION = 1
        self.ROAD_PARALLEL = 2
        self.SINGLE_LINE = 0
        self.SINGLE_DASHED_LINE = 1
        self.DOUBLE_LINE = 2
        self.DOUBLE_DASHED_LINE = 3
        self.CAR_LENGTH_SIM = 4.670000586694935
        self.MAX_PERCENTAGE_ZEROS = 0.8
        self.MAX_PERCENTAGE_ZEROS_CONT = 0.28
        self.LINUX = "Linux"
        self.DARWIN = "Darwin"
        self.WINDOWS = "Windows"
        self.CRISCE_IMPACT_MODEL = {
            "front_left": [
                "headlight_L", "hood", "fender_L", "bumper_F", "bumperbar_F", "suspension_F", "body_wagon"
            ],

            "front_right": [
                "hood", "bumper_F", "bumperbar_F", "fender_R", "headlight_R", "body_wagon", "suspension_F"
            ],

            "front_mid": [
                "bumperbar_F", "radiator", "body_wagon", "headlight_R", "headlight_L", "bumper_F", "fender_R",
                "fender_L",
                "hood", "suspension_F"
            ],

            "left_mid": [
                "door_RL_wagon", "body_wagon", "doorglass_FL", "mirror_L", "door_FL"
            ],

            "rear_left": [
                "suspension_R", "exhaust_i6_petrol", "taillight_L""body_wagon", "bumper_R", "tailgate", "bumper_R"
            ],

            "rear_mid": [
                "tailgate", "tailgateglass", "taillight_L", "taillight_R", "exhaust_i6_petrol", "bumper_R",
                "body_wagon",
                "suspension_R"
            ],

            "rear_right": [
                "suspension_R", "exhaust_i6_petrol", "taillight_R", "body_wagon", "tailgateglass", "tailgate",
                "bumper_R"
            ],

            "right_mid": [
                "door_RR_wagon", "body_wagon", "doorglass_FR", "mirror_R", "door_FR"
            ]
        }

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


CONST = Constant()
