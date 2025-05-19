#!/usr/bin/env python3
from rclpy.node import Node
from controller_manager_msgs.srv import ListControllers, SwitchController
from controller_manager_msgs.msg import ControllerState
import yaml

class MockControllerManager(Node):
    def __init__(self):
        super().__init__("controller_manager")

        # Callback group for multithreading
        self.load_controllers()

        # Create server for controller manager service
        self.list_controllers_client = self.create_service(
            ListControllers, "~/list_controllers", self.list_controllers
        )

        # Create server for controller manager service
        self.switch_controllers_client = self.create_service(
            SwitchController, "~/switch_controller", self.switch_controllers
        )

    def load_controllers(self):
        with open('/home/er4-user/ws/src/phoebe_bridgeback/phoebe_safety/tests/mock_controllers.yaml', 'r') as f:
            params = yaml.safe_load(f)

        self.controllers = []
        controllers = params["controllers"]
        for controller_param in controllers:
            controller = ControllerState()
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
        response = ListControllers.Response

        response.controller = []
        for controller in self.controllers:
            response.controller.append(controller)

        return response
    
    def switch_controllers(self, request, response):
        response = SwitchController.Response

        for controller in request.deactivate_controllers:
            for controller in self.controllers:
                if controller.active == False:
                    self.get_logger().info(f"Controller {controller.name} was already disabled")
                    response.ok = False
                else:
                    controller.active = False

        for controller in request.deactivate_controllers:
            for controller in self.controllers:
                if controller.active == True:
                    self.get_logger().info(f"Controller {controller.name} was already enabled")
                    response.ok = False
                else:
                    controller.active = True

        return response