#!/usr/bin/env python3
from rclpy.node import Node
from controller_manager_msgs.srv import ListControllers, SwitchController
from controller_manager_msgs.msg import ControllerState
from ament_index_python.packages import get_package_share_directory
import yaml

class MockControllerManager(Node):
    def __init__(self):
        super().__init__("controller_manager")

        # pull in the mock concotrllers
        self.load_controllers()

        # Create server for list controllers service
        self.list_controllers_client = self.create_service(
            ListControllers, "~/list_controllers", self.list_controllers
        )

        # Create server for switch controllers service
        self.switch_controllers_client = self.create_service(
            SwitchController, "~/switch_controller", self.switch_controllers
        )

    def load_controllers(self):
        phoebe_safety_dir = get_package_share_directory("phoebe_safety")
        with open(f"{phoebe_safety_dir}/tests/mock_controllers.yaml", "r") as f:
            params = yaml.safe_load(f)

        self.controllers = []
        controllers = params["controllers"]
        for controller_param in controllers:
            controller = ControllerState()
            controller.name = controller_param["name"]
            controller.state = controller_param["state"]
            controller.type = controller_param["type"]
            controller.claimed_interfaces = controller_param["claimed_interfaces"]
            controller.required_command_interfaces = controller_param["required_command_interfaces"]
            controller.required_state_interfaces = controller_param["required_state_interfaces"]
            controller.is_chainable = controller_param["is_chainable"]
            controller.is_chained = controller_param["is_chained"]
            controller.reference_interfaces = controller_param["reference_interfaces"]
            controller.chain_connections = controller_param["chain_connections"]
            self.controllers.append(controller)

    def list_controllers(self, request, response):
        response.controller = self.controllers
        return response

    def switch_controllers(self, request, response):
        response.ok = True

        # check that the controllers exist
        controller_names = [controller.name for controller in self.controllers]

        for deactivate_controller in request.deactivate_controllers:
            if deactivate_controller not in controller_names:
                self.get_logger().error(f"Controller {controller.name} does not exist")
                response.ok = False
                return response

            for controller in self.controllers:
                if deactivate_controller == controller.name:
                    if controller.state == "inactive":
                        self.get_logger().info(f"Controller {controller.name} was already disabled")
                        response.ok = False
                    else:
                        controller.state = "inactive"
                    break

        for activate_controller in request.activate_controllers:
            if activate_controller not in controller_names:
                self.get_logger().error(f"Controller {activate_controller} does not exist")
                response.ok = False
                return response

            for controller in self.controllers:
                if activate_controller == controller.name:
                    if controller.state == "active":
                        self.get_logger().info(f"Controller {controller.name} was already enabled")
                        response.ok = False
                    else:
                        controller.state = "active"
                    break

        return response

    def get_active_controllers(self):
        active_list = []
        for controller in self.controllers:
            if controller.state == "active":
                active_list.append(controller.name)

        return active_list

    def get_inactive_controllers(self):
        active_list = []
        for controller in self.controllers:
            if controller.state == "inactive":
                active_list.append(controller.name)

        return active_list

    def any_controllers_with_command_interfaces_active(self, exceptions = []):
        for controller in self.controllers:
            if controller.state == "active" and controller.name not in exceptions:
                if len(controller.required_command_interfaces) > 0:
                    return True

        return False