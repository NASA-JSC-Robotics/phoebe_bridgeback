# Holder to gather high-level state
# This could easily be converted to a message if we desired, and
# possibly for logging that would be nice
class StatusState:
    # Robot stop state
    ROBOT_STATE_NO_COMM = 0
    ROBOT_STATE_ESTOPPED = 1
    ROBOT_STATE_NEEDS_RESET = 2
    ROBOT_STATE_RUNNING = 3

    # Battery state
    BATTERY_STATE_NO_COMM = 0
    BATTERY_STATE_OK = 1
    BATTERY_STATE_LOW = 2
    BATTERY_STATE_FULL = 3
    BATTERY_STATE_FAULTED = 4

    # Charging state
    CHARGING_STATE_NO_COMM = 0
    CHARGING_STATE_INACTIVE = 1
    CHARGING_STATE_ACTIVE = 2
    CHARGING_STATE_FAULT_SHORE_POWER = 3

    # Driving state
    DRIVING_STATE_NO_COMM = 0
    DRIVING_STATE_OFF = 1
    DRIVING_STATE_ON = 2

    def __init__(self):
        self.run_state = self.ROBOT_STATE_NO_COMM
        self.battery_state = self.BATTERY_STATE_NO_COMM
        self.charging_state = self.CHARGING_STATE_NO_COMM
        self.driving_state = self.DRIVING_STATE_NO_COMM
        self.battery_percent = 0
        self.battery_voltage = 0
        self.battery_amps = 0

    def __str__(self):
        serialized_msg = f"Run state: {self.run_state}\n"
        serialized_msg += f"Battery state: {self.battery_state}\n"
        serialized_msg += f"Battery percent: {self.battery_percent}\n"
        serialized_msg += f"Battery volts: {self.battery_voltage}\n"
        serialized_msg += f"Battery amps: {self.battery_amps}\n"
        serialized_msg += f"Charging state: {self.charging_state}\n"
        serialized_msg += f"Driving state: {self.driving_state}\n"
        return serialized_msg
