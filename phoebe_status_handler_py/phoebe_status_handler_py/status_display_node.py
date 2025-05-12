from std_msgs.msg import Int32
from status_state import StatusState
from rclpy.node import Node

class StatusDisplayNode(Node):
    def __init__(self, display):
        super().__init__("status_display_node")
        self.display_ = display
        self.status_  = StatusState()

        self.robot_status_sub_ = self.create_subscription(Int32, 'status', self.status_callback, 10)
        self.robot_battery_sub_ = self.create_subscription(Int32, 'battery', self.battery_callback, 10)
        self.robot_charging_sub_ = self.create_subscription(Int32, 'charging', self.charging_callback, 10)
        self.timer_        = self.create_timer(1.0, self.timer_callback)
        display.set_logger(self.get_logger())

    def display_status(self):
        self.display_.update(self.status_)

    def status_callback(self, msg):
        self.status_.estop_state = msg.data

    def battery_callback(self, msg):
        self.status_.battery_state = msg.data

    def charging_callback(self, msg):
        self.status_.charging_state = msg.data

    def timer_callback(self):
        self.display_status()