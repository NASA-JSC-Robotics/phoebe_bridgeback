/*
 * Copyright (c) 2026, United States Government, as represented by the
 * Administrator of the National Aeronautics and Space Administration.
 *
 * All rights reserved.
 *
 * This software is licensed under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with the
 * License. You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

#include "magic_carpet_controller/magic_carpet_controller.hpp"

#include <cmath>
#include <string>

#include "pluginlib/class_list_macros.hpp"

namespace phoebe_controllers {

controller_interface::CallbackReturn MagicCarpetController::on_init() {
  try {
    auto_declare<std::string>("linear_x_joint", "linear_x_joint");
    auto_declare<std::string>("linear_y_joint", "linear_y_joint");
    auto_declare<std::string>("yaw_joint", "rotational_yaw_joint");
    auto_declare<std::string>("reference_topic",
                              "/platform_velocity_controller/reference");
  } catch (const std::exception &e) {
    RCLCPP_ERROR(get_node()->get_logger(), "on_init failed: %s", e.what());
    return controller_interface::CallbackReturn::ERROR;
  }
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn MagicCarpetController::on_configure(
    const rclcpp_lifecycle::State & /*previous_state*/) {
  reference_topic_ = get_node()->get_parameter("reference_topic").as_string();
  linear_x_joint_ = get_node()->get_parameter("linear_x_joint").as_string();
  linear_y_joint_ = get_node()->get_parameter("linear_y_joint").as_string();
  yaw_joint_ = get_node()->get_parameter("yaw_joint").as_string();

  // Subscribe to the platform velocity controller reference topic
  cmd_vel_sub_ =
      get_node()->create_subscription<geometry_msgs::msg::TwistStamped>(
          reference_topic_, rclcpp::SystemDefaultsQoS(),
          [this](const geometry_msgs::msg::TwistStamped::SharedPtr msg) {
            rt_command_buf_.writeFromNonRT(*msg);
          });

  RCLCPP_INFO(get_node()->get_logger(),
              "Configured: listening on '%s', commanding joints [%s, %s, %s]",
              reference_topic_.c_str(), linear_x_joint_.c_str(),
              linear_y_joint_.c_str(), yaw_joint_.c_str());

  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::InterfaceConfiguration
MagicCarpetController::command_interface_configuration() const {
  controller_interface::InterfaceConfiguration config;
  config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
  config.names = {
      linear_x_joint_ + "/" + hardware_interface::HW_IF_VELOCITY,
      linear_y_joint_ + "/" + hardware_interface::HW_IF_VELOCITY,
      yaw_joint_ + "/" + hardware_interface::HW_IF_VELOCITY,
  };
  return config;
}

controller_interface::InterfaceConfiguration
MagicCarpetController::state_interface_configuration() const {
  controller_interface::InterfaceConfiguration config;
  config.type = controller_interface::interface_configuration_type::INDIVIDUAL;
  config.names = {
      yaw_joint_ + "/" + hardware_interface::HW_IF_POSITION,
  };
  return config;
}

controller_interface::CallbackReturn MagicCarpetController::on_activate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
  // Reset the command buffer so we don't act on stale data
  rt_command_buf_.writeFromNonRT(geometry_msgs::msg::TwistStamped());

  RCLCPP_INFO(get_node()->get_logger(), "Activated");
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn MagicCarpetController::on_deactivate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
  // Zero out commands on deactivation
  for (auto &cmd_if : command_interfaces_) {
    cmd_if.set_value(0.0);
  }
  RCLCPP_INFO(get_node()->get_logger(), "Deactivated");
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::return_type
MagicCarpetController::update(const rclcpp::Time & /*time*/,
                              const rclcpp::Duration & /*period*/) {
  // Read current yaw from state interface (the only state interface we claim)
  const double yaw = state_interfaces_[0].get_value();

  // Read latest command (realtime-safe)
  const auto &cmd = *rt_command_buf_.readFromRT();

  // Rotate body-frame velocities into the odom frame
  const double cos_yaw = std::cos(yaw);
  const double sin_yaw = std::sin(yaw);

  const double vx_body = cmd.twist.linear.x;
  const double vy_body = cmd.twist.linear.y;

  const double vx_odom = vx_body * cos_yaw - vy_body * sin_yaw;
  const double vy_odom = vx_body * sin_yaw + vy_body * cos_yaw;
  const double wz = cmd.twist.angular.z;

  // Write to command interfaces
  // command_interfaces_ order matches command_interface_configuration():
  //   [0] linear_x_joint/velocity
  //   [1] linear_y_joint/velocity
  //   [2] rotational_yaw_joint/velocity
  command_interfaces_[0].set_value(vx_odom);
  command_interfaces_[1].set_value(vy_odom);
  command_interfaces_[2].set_value(wz);

  return controller_interface::return_type::OK;
}

} // namespace phoebe_controllers

PLUGINLIB_EXPORT_CLASS(phoebe_controllers::MagicCarpetController,
                       controller_interface::ControllerInterface)
