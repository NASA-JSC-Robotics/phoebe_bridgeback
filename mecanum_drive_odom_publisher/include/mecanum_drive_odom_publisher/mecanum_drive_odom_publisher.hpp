/**
 * Copyright (c) 2025, United States Government, as represented by the
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

#ifndef MECANUM_DRIVE_ODOM_PUBLISHER__MECANUM_DRIVE_ODOM_PUBLISHER_HPP_
#define MECANUM_DRIVE_ODOM_PUBLISHER__MECANUM_DRIVE_ODOM_PUBLISHER_HPP_

#include <chrono>
#include <cmath>
#include <memory>
#include <queue>
#include <string>
#include <utility>
#include <vector>

#include <mecanum_drive_odom_publisher/mecanum_drive_odom_publisher_parameters.hpp>
#include "controller_interface/controller_interface.hpp"
#include "mecanum_drive_odom_publisher/odometry.hpp"
#include "mecanum_drive_odom_publisher/visibility_control.h"
#include "rclcpp_lifecycle/node_interfaces/lifecycle_node_interface.hpp"
#include "rclcpp_lifecycle/state.hpp"
#include "realtime_tools/realtime_buffer.hpp"
#include "realtime_tools/realtime_publisher.hpp"
#include "std_srvs/srv/set_bool.hpp"

#include "geometry_msgs/msg/twist_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "tf2_msgs/msg/tf_message.hpp"
namespace mecanum_drive_odom_publisher
{
// name constants for state interfaces
static constexpr size_t NR_STATE_ITFS = 4;

class MecanumDriveOdomPublisher : public controller_interface::ControllerInterface
{
public:
  MECANUM_DRIVE_ODOM_PUBLISHER__VISIBILITY_PUBLIC
  MecanumDriveOdomPublisher();

  MECANUM_DRIVE_ODOM_PUBLISHER__VISIBILITY_PUBLIC
  controller_interface::CallbackReturn on_init() override;

  MECANUM_DRIVE_ODOM_PUBLISHER__VISIBILITY_PUBLIC
  controller_interface::InterfaceConfiguration command_interface_configuration() const override;

  MECANUM_DRIVE_ODOM_PUBLISHER__VISIBILITY_PUBLIC
  controller_interface::InterfaceConfiguration state_interface_configuration() const override;

  MECANUM_DRIVE_ODOM_PUBLISHER__VISIBILITY_PUBLIC
  controller_interface::CallbackReturn on_configure(const rclcpp_lifecycle::State& previous_state) override;

  MECANUM_DRIVE_ODOM_PUBLISHER__VISIBILITY_PUBLIC
  controller_interface::CallbackReturn on_activate(const rclcpp_lifecycle::State& previous_state) override;

  MECANUM_DRIVE_ODOM_PUBLISHER__VISIBILITY_PUBLIC
  controller_interface::CallbackReturn on_deactivate(const rclcpp_lifecycle::State& previous_state) override;

  MECANUM_DRIVE_ODOM_PUBLISHER__VISIBILITY_PUBLIC
  controller_interface::return_type update(const rclcpp::Time& time, const rclcpp::Duration& period) override;

  using OdomStateMsg = nav_msgs::msg::Odometry;
  using TfStateMsg = tf2_msgs::msg::TFMessage;

protected:
  std::vector<std::string> state_joint_names_;

  std::shared_ptr<mecanum_drive_odom_publisher::ParamListener> param_listener_;
  mecanum_drive_odom_publisher::Params params_;

  using OdomStatePublisher = realtime_tools::RealtimePublisher<OdomStateMsg>;
  rclcpp::Publisher<OdomStateMsg>::SharedPtr odom_s_publisher_;
  std::unique_ptr<OdomStatePublisher> rt_odom_state_publisher_;

  using TfStatePublisher = realtime_tools::RealtimePublisher<TfStateMsg>;
  rclcpp::Publisher<TfStateMsg>::SharedPtr tf_odom_s_publisher_;
  std::unique_ptr<TfStatePublisher> rt_tf_odom_state_publisher_;

  Odometry odometry_;

private:
  double velocity_in_center_frame_linear_x_;   // [m/s]
  double velocity_in_center_frame_linear_y_;   // [m/s]
  double velocity_in_center_frame_angular_z_;  // [rad/s]
};

}  // namespace mecanum_drive_odom_publisher

#endif  // MECANUM_DRIVE_ODOM_PUBLISHER__MECANUM_DRIVE_ODOM_PUBLISHER_HPP_
