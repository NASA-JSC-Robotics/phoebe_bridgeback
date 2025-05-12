from std_msgs.msg import Bool
from rclpy.node import Node
from clearpath_platform_msgs.msg import Status, Power, StopStatus
from sensor_msgs.msg import BatteryState
from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from phoebe_status_handler_py.status_state import StatusState
import copy


class SavedMsg(object):
    def __init__(self, msg_type):
        self.msg_type = msg_type
        self.msg = None
        self.updated = False

    def update(self, msg):
        if self.msg_type != type(msg):
            raise RuntimeError("Attempt to update a message of type " + str(self.msg_type)
                               + " from a message of type " + str(type(msg)))
        self.msg = msg
        self.updated = True

    def clear(self, msg):
        self.updated = False


class SubscriptionSet(object):
    def __init__(self):
        self.msgs = {
            "status":         SavedMsg(Status),
            "power":          SavedMsg(Power),
            "stop_status":    SavedMsg(StopStatus),
            "battery_status": SavedMsg(BatteryState),
            "estop_status":   SavedMsg(Bool),
            "cmd_vel":        SavedMsg(Twist)
        }

    def is_all_updated(self):
        return all([self.msgs[k].updated for k in self.msgs])


class StatusDisplayNode(Node):
    def __init__(self, display):
        super().__init__("status_display_node")
        self.display_ = display
        self.status_ = StatusState()
        self.previous_state_ = None
        self.current_state_ = SubscriptionSet()

        # All of the subscriptions use SensorDataQoS on the C++ side.
        # Set up something equivalent for python
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Data subscriptions
        self.status_sub_ = self.create_subscription(
            Status,       'platform/mcu/status',        self.status_cb,      qos)
        self.power_sub_ = self.create_subscription(
            Power,        'platform/mcu/status/power',  self.power_cb,       qos)
        self.stop_status_sub_ = self.create_subscription(
            StopStatus,   'platform/mcu/status/stop',   self.stop_status_cb, qos)
        self.battery_sub_ = self.create_subscription(
            BatteryState, 'platform/mcu/status',        self.battery_cb,     qos)
        self.estop_sub_ = self.create_subscription(
            Bool,         'platform/emergency_stop',    self.estop_cb,       qos)
        self.cmd_vel_sub_ = self.create_subscription(
            Twist,        'platform/cmd_vel_unstamped', self.cmd_vel_cb,     qos)

        self.timer_ = self.create_timer(1.0, self.timer_callback)
        display.set_logger(self.get_logger())

    def display_status(self):
        self.display_.update(self.status_)

    def update_msg_cb(self, which_state, msg):
        which_state.status.update(msg)

    def status_cb(self, msg: Status):
        self.current_state_.status.update(msg)

    def power_cb(self, msg: Power):
        self.current_state_.power.update(msg)

    def stop_status_cb(self, msg: StopStatus):
        self.current_state_.stop_status.update(msg)

    def battery_cb(self, msg: BatteryState):
        self.current_state_.battery_status.update(msg)

    def estop_cb(self, msg: Bool):
        self.current_state_.estop_status.update(msg)

    def cmd_vel_cb(self, msg: Twist):
        self.current_state_.cmd_vel.update(msg)

    def compute_state(self):
        curr = self.current_state_
        if not curr.is_all_updated():
            self.get_logger.warn("Not all messages updated in the last cycle")

        # Check battery state
        if curr.msgs["battery_status"].power_supply_health != BatteryState.POWER_SUPPLY_HEALTH_GOOD:
            self.status_.battery_state = StatusState.BATTERY_STATE_FAULTED
        elif curr.msgs["battery_status"].percentage < 0.2:
            self.status_.battery_state = StatusState.BATTERY_STATE_LOW
        elif curr.msgs["battery_status"].percentage == 1.0:
            self.status_.battery_state = StatusState.BATTERY_STATE_FULL
        else:
            self.status_.battery_state = StatusState.BATTERY_STATE_OK

        # Check charging state. Charging is off if we are not charging or fully charged
        if curr.msgs["battery_status"].power_supply_status == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
            if curr.msgs["battery_status"].percentage == 1.0:
                self.status_.charging_state = StatusState.CHARGING_STATE_OFF
            else:
                self.status_.charging_state = StatusState.CHARGING_STATE_ACTIVE
        else:
            self.status_.charging_state = StatusState.CHARGING_STATE_OFF

        # Check EStop state
        if curr.msgs["stop_status"].needs_reset:
            if curr.msgs["estop_status"].data:
                self.status_.estop_state = StatusState.ROBOT_STATE_ESTOPPED
            else:
                self.status_.estop_state = StatusState.ROBOT_STATE_ESTOPPED
        else:
            self.status_.estop_state = StatusState.ROBOT_STATE_RUNNING

        # Save off state for comparison
        self.previous_state_ = copy.deepcopy(self.current_state_)

    def timer_callback(self):
        self.display_status()
