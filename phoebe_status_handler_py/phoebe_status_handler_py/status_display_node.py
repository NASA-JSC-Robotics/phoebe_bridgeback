from std_msgs.msg import Bool
from rclpy.node import Node
from clearpath_platform_msgs.msg import Status, Power, StopStatus
from sensor_msgs.msg import BatteryState
from geometry_msgs.msg import Twist
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from phoebe_status_handler_py.status_state import StatusState
from functools import partial
import copy
import math

class SavedMsg(object):
    """Simple class to encapsulate the idea of a message that will be updated or not each cycle
    This allows us to see the difference between a message that arrives unchanged and
    a message that stops being received.
    """

    def __init__(self, msg_type):
        """Constructor

        Args:
            msg_type (any message type): the type of the message to store. Must be 
            default-contstrutible
        """
        self.msg_type = msg_type
        self.msg = msg_type()
        self.updated = False

    def update(self, msg):
        """Update the message with new content

        Args:
            msg (_type_): New content message

        Raises:
            RuntimeError: Attempt to update a message with a message of a different type
        """
        if self.msg_type != type(msg):
            raise RuntimeError("Attempt to update a message of type " + str(self.msg_type)
                               + " from a message of type " + str(type(msg)))
        self.msg = msg
        self.updated = True

    def clear(self):
        """Clear the update flag in preparation for the next cycle"""
        self.updated = False


class SubscriptionSet(object):
    """Container for a specific set of SavedMsg. Adds some convenience aggregated functions."""

    def __init__(self, msgs):
        self.msgs = msgs

    def is_all_updated(self):
        return all([self.msgs[k].updated for k in self.msgs])
    
    def reset_update(self):
        for k in self.msgs:
            self.msgs[k].updated = False


class StatusDisplayNode(Node):
    """Determines a simplified system state from a set of subscriptions"""

    def __init__(self, display=None):
        """Constructor

        Args:
            display (Any, optional): May be any class with an update function that can take a StatusState message or None. If None,
                                     the current state will be written to the terminal during display_status(). Defaults to None.
        """

        super().__init__("status_display_node")
        
        self.display_ = display
        self.status_ = StatusState()
        self.current_state_ = SubscriptionSet( {
            "status":         SavedMsg(Status),
            "power":          SavedMsg(Power),
            "stop_status":    SavedMsg(StopStatus),
            "battery_status": SavedMsg(BatteryState),
            "estop_status":   SavedMsg(Bool),
            "cmd_vel":        SavedMsg(Twist) }
        )

        # All of the subscriptions use SensorDataQoS on the C++ side.
        # Set up something equivalent for python
        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Data subscriptions
        # self.status_sub_  = self.create_subscription(Status,       'platform/mcu/status',        self.status_cb,      qos)
        self.status_sub_  = self.create_subscription(Status,       'platform/mcu/status',        partial(self.update_msg_cb, "status"),         qos)
        self.power_sub_   = self.create_subscription(Power,        'platform/mcu/status/power',  partial(self.update_msg_cb, "power"),          qos)
        self.stop_status_sub_ = self.create_subscription(StopStatus, 'platform/mcu/status/stop', partial(self.update_msg_cb, "stop_status"),    qos)
        self.battery_sub_ = self.create_subscription(BatteryState, 'platform/bms/state',         partial(self.update_msg_cb, "battery_status"), qos)
        self.estop_sub_   = self.create_subscription(Bool,         'platform/emergency_stop',    partial(self.update_msg_cb, "estop_status"),   qos)
        self.cmd_vel_sub_ = self.create_subscription(Twist,        'platform/cmd_vel_unstamped', partial(self.update_msg_cb, "cmd_vel"),        qos)

        # Timer used to drive the update cycle. The timing is limited by how often the subscriptions arrive
        self.timer_ = self.create_timer(2.0, self.timer_callback)
        if self.display_:
            self.display_.set_logger(self.get_logger())

    def display_status(self):
        """Update the display with the current status."""

        if self.display_:
            self.display_.update(self.status_)
        else:
            self.get_logger().info(str(self.status_))

    def update_msg_cb(self, which_state: str, msg):
        """Callback function to store a subscribed message

        Args:
            which_state (str): state name. Must be one of the states in the subscription set
            msg (any message type): incoming message
        """
        self.current_state_.msgs[which_state].update(msg)

    def compute_state(self):
        """Compute current state based on the latest subscribed messages"""

        # Shorthand for readability
        curr = self.current_state_

        # If we didn't get an update on battery state, can't determine battery or charging state
        if not curr.msgs["battery_status"].updated:
            self.status_.battery_state = StatusState.BATTERY_STATE_OFF
            self.status_.charging_state = StatusState.CHARGING_STATE_OFF
            self.status_.battery_percent = math.nan
            self.status_.battery_voltage = math.nan
            self.status_.battery_amps    = math.nan
        else:
            # Check battery state
            if curr.msgs["battery_status"].msg.power_supply_health != BatteryState.POWER_SUPPLY_HEALTH_GOOD:
                self.status_.battery_state = StatusState.BATTERY_STATE_FAULTED
            elif curr.msgs["battery_status"].msg.percentage < 0.2:
                self.status_.battery_state = StatusState.BATTERY_STATE_LOW
            elif curr.msgs["battery_status"].msg.percentage == 1.0:
                self.status_.battery_state = StatusState.BATTERY_STATE_FULL
            else:
                self.status_.battery_state = StatusState.BATTERY_STATE_OK

            # Check charging state. Charging is off if we are not charging or fully charged
            if curr.msgs["battery_status"].msg.power_supply_status == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
                if curr.msgs["battery_status"].msg.percentage == 1.0:
                    self.status_.charging_state = StatusState.CHARGING_STATE_OFF
                else:
                    self.status_.charging_state = StatusState.CHARGING_STATE_ACTIVE
            else:
                self.status_.charging_state = StatusState.CHARGING_STATE_OFF

            self.status_.battery_percent = int(curr.msgs["battery_status"].msg.percentage * 100)
            self.status_.battery_voltage = curr.msgs["battery_status"].msg.voltage
            self.status_.battery_amps    = curr.msgs["battery_status"].msg.current

        # Check EStop state
        if not curr.msgs["estop_status"].updated or not curr.msgs["stop_status"].updated:
            self.status_.run_state = StatusState.ROBOT_STATE_OFF
        else:
            if curr.msgs["estop_status"].msg.data:
                self.status_.run_state = StatusState.ROBOT_STATE_ESTOPPED
            elif curr.msgs["stop_status"].msg.needs_reset:
                self.status_.run_state = StatusState.ROBOT_STATE_NEEDS_RESET
            else:
                self.status_.run_state = StatusState.ROBOT_STATE_RUNNING

        # Reset update state to False for all subscriptions so we can tell if we receive
        # a message on the next cycle
        curr.reset_update()

    def timer_callback(self):
        """Compute and publish status"""
        self.compute_state()
        self.display_status()
