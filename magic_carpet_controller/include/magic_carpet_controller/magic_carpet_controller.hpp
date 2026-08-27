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

#pragma once

#include <memory>
#include <string>
#include <vector>

#include "controller_interface/controller_interface.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "realtime_tools/realtime_publisher.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/subscription.hpp"
#include "rclcpp_lifecycle/state.hpp"
#include "realtime_tools/realtime_buffer.hpp"

namespace phoebe_controllers {

/*
 * \brief Bridges platform velocity controller commands to the magic carpet
 * controller.
 *
 * Subscribes to body-frame TwistStamped commands (from the platform velocity
 * controller), rotates them into the odom frame using the current yaw joint
 * state, and writes the resulting velocities directly to the magic carpet
 * joint command interfaces (linear_x, linear_y, rotational_yaw).
 *
 * Parameters:
 *   - tf_prefix (string, default: ""): Joint name prefix.
 *   - reference_topic (string, default:
 * "/platform_velocity_controller/reference"): TwistStamped topic to subscribe
 * to.
 *
 * Command interfaces (velocity): linear_x_joint, linear_y_joint,
 * rotational_yaw_joint State interfaces (position): rotational_yaw_joint
 */
class MagicCarpetController : public controller_interface::ControllerInterface {
public:
  MagicCarpetController() = default;
  ~MagicCarpetController() override = default;

  controller_interface::InterfaceConfiguration
  command_interface_configuration() const override;
  controller_interface::InterfaceConfiguration
  state_interface_configuration() const override;

  controller_interface::CallbackReturn on_init() override;

  controller_interface::CallbackReturn
  on_configure(const rclcpp_lifecycle::State &previous_state) override;

  controller_interface::CallbackReturn
  on_activate(const rclcpp_lifecycle::State &previous_state) override;

  controller_interface::CallbackReturn
  on_deactivate(const rclcpp_lifecycle::State &previous_state) override;

  controller_interface::return_type
  update(const rclcpp::Time &time, const rclcpp::Duration &period) override;

private:
  // Joint names (constructed from tf_prefix)
  std::string linear_x_joint_;
  std::string linear_y_joint_;
  std::string yaw_joint_;

  // Parameter values
  std::string tf_prefix_;
  std::string reference_topic_;

  // Realtime-safe buffer for incoming twist commands
  realtime_tools::RealtimeBuffer<geometry_msgs::msg::TwistStamped>
      rt_command_buf_;
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr
      cmd_vel_sub_;

  // Odometry publisher
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
  std::unique_ptr<realtime_tools::RealtimePublisher<nav_msgs::msg::Odometry>>
      rt_odom_pub_;
  rclcpp::Duration odom_publish_period_{0, 0};
  rclcpp::Time last_odom_publish_time_{0, 0, RCL_CLOCK_UNINITIALIZED};

};

} // namespace phoebe_controllers
