class StatusState(object):
    ROBOT_STATE_OFF = 0
    ROBOT_STATE_NO_COMM = 1
    ROBOT_STATE_ESTOPPED = 2
    ROBOT_STATE_NEEDS_RESET = 3
    ROBOT_STATE_RUNNING = 4

    BATTERY_STATE_OFF = 0
    BATTERY_STATE_OK  = 1
    BATTERY_STATE_LOW = 2
    BATTERY_STATE_FULL = 3

    CHARGING_STATE_OFF = 0
    CHARGING_STATE_ACTIVE = 1

    def __init__(self):
        self.estop_state    = self.ROBOT_STATE_OFF
        self.battery_state  = self.BATTERY_STATE_OFF
        self.charging_state = self.CHARGING_STATE_OFF
