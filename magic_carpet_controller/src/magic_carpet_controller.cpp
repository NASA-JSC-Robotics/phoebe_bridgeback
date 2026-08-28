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
    auto_declare<double>("odom_publish_rate", 50.0);
    auto_declare<std::string>("odom_frame_id", "odom");
    auto_declare<std::string>("base_frame_id", "base_link");
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
  odom_frame_id_ = get_node()->get_parameter("odom_frame_id").as_string();
  base_frame_id_ = get_node()->get_parameter("base_frame_id").as_string();

  const double odom_publish_rate =
      get_node()->get_parameter("odom_publish_rate").as_double();
  if (odom_publish_rate > 0.0) {
    odom_publish_period_ = rclcpp::Duration::from_seconds(1.0 / odom_publish_rate);
  } else {
    odom_publish_period_ = rclcpp::Duration::from_seconds(0.0);
  }

  // Subscribe to the platform velocity controller reference topic
  cmd_vel_sub_ =
      get_node()->create_subscription<geometry_msgs::msg::TwistStamped>(
          reference_topic_, rclcpp::SystemDefaultsQoS(),
          [this](const geometry_msgs::msg::TwistStamped::SharedPtr msg) {
            rt_command_buf_.writeFromNonRT(*msg);
          });

  // Set up the odometry publisher with a realtime wrapper
  odom_pub_ = get_node()->create_publisher<nav_msgs::msg::Odometry>(
      "~/odom", rclcpp::SystemDefaultsQoS());
  rt_odom_pub_ =
      std::make_unique<realtime_tools::RealtimePublisher<nav_msgs::msg::Odometry>>(
          odom_pub_);

  // These won't change
  auto &odom_msg = rt_odom_pub_->msg_;
  odom_msg.header.frame_id = odom_frame_id_;
  odom_msg.child_frame_id = base_frame_id_;

  RCLCPP_INFO(get_node()->get_logger(),
              "Configured: listening on '%s', commanding joints [%s, %s, %s], "
              "odom rate %.1f Hz, frames [%s -> %s]",
              reference_topic_.c_str(), linear_x_joint_.c_str(),
              linear_y_joint_.c_str(), yaw_joint_.c_str(), odom_publish_rate,
              odom_frame_id_.c_str(), base_frame_id_.c_str());

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
      linear_x_joint_ + "/" + hardware_interface::HW_IF_POSITION,
      linear_y_joint_ + "/" + hardware_interface::HW_IF_POSITION,
      yaw_joint_ + "/" + hardware_interface::HW_IF_POSITION,
  };
  return config;
}

controller_interface::CallbackReturn MagicCarpetController::on_activate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
  // Reset the command buffer so we don't act on stale data
  rt_command_buf_.writeFromNonRT(geometry_msgs::msg::TwistStamped());

  last_odom_publish_time_ = get_node()->get_clock()->now();

  RCLCPP_INFO(get_node()->get_logger(), "Activated");
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn MagicCarpetController::on_deactivate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
  // Zero out commands on deactivation
  for (auto &cmd_if : command_interfaces_) {
    if (!cmd_if.set_value(0.0)) {
      RCLCPP_WARN(get_node()->get_logger(),
                  "Failed to zero command interface '%s'",
                  cmd_if.get_name().c_str());
    }
  }
  RCLCPP_INFO(get_node()->get_logger(), "Deactivated");
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::return_type
MagicCarpetController::update(const rclcpp::Time &time,
                              const rclcpp::Duration & /*period*/) {
  // Read current positions from state interfaces, needed for odom.
  // state_interfaces_ order matches state_interface_configuration():
  //   [0] linear_x_joint/position
  //   [1] linear_y_joint/position
  //   [2] yaw_joint/position
  const auto x_opt = state_interfaces_[0].get_optional();
  const auto y_opt = state_interfaces_[1].get_optional();
  const auto yaw_opt = state_interfaces_[2].get_optional();

  if (!x_opt.has_value() || !y_opt.has_value() || !yaw_opt.has_value()) {
    RCLCPP_WARN_THROTTLE(get_node()->get_logger(), *get_node()->get_clock(),
                         1000, "Could not read one or more state interfaces");
    return controller_interface::return_type::OK;
  }

  const double x = x_opt.value();
  const double y = y_opt.value();
  const double yaw = yaw_opt.value();

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
  if (!command_interfaces_[0].set_value(vx_odom) ||
      !command_interfaces_[1].set_value(vy_odom) ||
      !command_interfaces_[2].set_value(wz)) {
    RCLCPP_WARN_THROTTLE(get_node()->get_logger(), *get_node()->get_clock(),
                         1000, "Failed to set one or more command interfaces");
  }

  // Publish odometry at the configured rate
  if (odom_publish_period_.seconds() > 0.0 &&
      (time - last_odom_publish_time_) >= odom_publish_period_) {
    last_odom_publish_time_ = time;

    if (rt_odom_pub_->trylock()) {
      auto &odom_msg = rt_odom_pub_->msg_;
      odom_msg.header.stamp = time;

      odom_msg.pose.pose.position.x = x;
      odom_msg.pose.pose.position.y = y;
      odom_msg.pose.pose.position.z = 0.0;

      odom_msg.pose.pose.orientation.x = 0.0;
      odom_msg.pose.pose.orientation.y = 0.0;
      odom_msg.pose.pose.orientation.z = std::sin(yaw * 0.5);
      odom_msg.pose.pose.orientation.w = std::cos(yaw * 0.5);

      odom_msg.twist.twist.linear.x = vx_body;
      odom_msg.twist.twist.linear.y = vy_body;
      odom_msg.twist.twist.angular.z = wz;

      rt_odom_pub_->unlockAndPublish();
    }
  }

  return controller_interface::return_type::OK;
}

} // namespace phoebe_controllers

PLUGINLIB_EXPORT_CLASS(phoebe_controllers::MagicCarpetController,
                       controller_interface::ControllerInterface)
