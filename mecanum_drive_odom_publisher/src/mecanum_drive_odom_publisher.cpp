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

#include "mecanum_drive_odom_publisher/mecanum_drive_odom_publisher.hpp"

#include <limits>
#include <memory>
#include <string>
#include <vector>

#include "controller_interface/helpers.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "lifecycle_msgs/msg/state.hpp"
#include "tf2/transform_datatypes.h"
#include "tf2_geometry_msgs/tf2_geometry_msgs.hpp"

namespace mecanum_drive_odom_publisher {
MecanumDriveOdomPublisher::MecanumDriveOdomPublisher()
    : controller_interface::ControllerInterface() {}

controller_interface::CallbackReturn MecanumDriveOdomPublisher::on_init() {
  try {
    param_listener_ =
        std::make_shared<mecanum_drive_odom_publisher::ParamListener>(
            get_node());
  } catch (const std::exception &e) {
    fprintf(stderr,
            "Exception thrown during controller's init with message: %s \n",
            e.what());
    return controller_interface::CallbackReturn::ERROR;
  }

  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn MecanumDriveOdomPublisher::on_configure(
    const rclcpp_lifecycle::State & /*previous_state*/) {
  params_ = param_listener_->get_params();

  if (!params_.state_joint_names.empty()) {
    state_joint_names_ = params_.state_joint_names;
  } else {
    RCLCPP_FATAL(get_node()->get_logger(),
                 "'state_joint_names' must be provided in the config file!");
  }

  odometry_.init(get_node()->now(),
                 {params_.kinematics.base_frame_offset.x,
                  params_.kinematics.base_frame_offset.y,
                  params_.kinematics.base_frame_offset.theta});
  // Set wheel params for the odometry computation
  odometry_.setWheelsParams(
      params_.kinematics.sum_of_robot_center_projection_on_X_Y_axis,
      params_.kinematics.wheels_radius);

  try {
    // Odom state publisher
    odom_s_publisher_ = get_node()->create_publisher<OdomStateMsg>(
        "~/odom", rclcpp::SystemDefaultsQoS());
    rt_odom_state_publisher_ =
        std::make_unique<OdomStatePublisher>(odom_s_publisher_);
  } catch (const std::exception &e) {
    fprintf(stderr,
            "Exception thrown during publisher creation at configure stage "
            "with message : %s \n",
            e.what());
    return controller_interface::CallbackReturn::ERROR;
  }

  rt_odom_state_publisher_->lock();
  rt_odom_state_publisher_->msg_.header.stamp = get_node()->now();
  rt_odom_state_publisher_->msg_.header.frame_id = params_.odom_frame_id;
  rt_odom_state_publisher_->msg_.child_frame_id = params_.base_frame_id;
  rt_odom_state_publisher_->msg_.pose.pose.position.z = 0;

  auto &pose_covariance = rt_odom_state_publisher_->msg_.pose.covariance;
  auto &twist_covariance = rt_odom_state_publisher_->msg_.twist.covariance;
  constexpr size_t NUM_DIMENSIONS = 6;
  for (size_t index = 0; index < 6; ++index) {
    const size_t diagonal_index = NUM_DIMENSIONS * index + index;
    pose_covariance[diagonal_index] = params_.pose_covariance_diagonal[index];
    twist_covariance[diagonal_index] = params_.twist_covariance_diagonal[index];
  }
  rt_odom_state_publisher_->unlock();

  try {
    // Tf State publisher
    tf_odom_s_publisher_ = get_node()->create_publisher<TfStateMsg>(
        "~/tf_odometry", rclcpp::SystemDefaultsQoS());
    rt_tf_odom_state_publisher_ =
        std::make_unique<TfStatePublisher>(tf_odom_s_publisher_);
  } catch (const std::exception &e) {
    fprintf(stderr,
            "Exception thrown during publisher creation at configure stage "
            "with message : %s \n",
            e.what());
    return controller_interface::CallbackReturn::ERROR;
  }

  rt_tf_odom_state_publisher_->lock();
  rt_tf_odom_state_publisher_->msg_.transforms.resize(1);
  rt_tf_odom_state_publisher_->msg_.transforms[0].header.stamp =
      get_node()->now();
  rt_tf_odom_state_publisher_->msg_.transforms[0].header.frame_id =
      params_.odom_frame_id;
  rt_tf_odom_state_publisher_->msg_.transforms[0].child_frame_id =
      params_.base_frame_id;
  rt_tf_odom_state_publisher_->msg_.transforms[0].transform.translation.z = 0.0;
  rt_tf_odom_state_publisher_->unlock();

  RCLCPP_INFO(get_node()->get_logger(), "configure successful");
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::InterfaceConfiguration
MecanumDriveOdomPublisher::command_interface_configuration() const {
  return controller_interface::InterfaceConfiguration{
      controller_interface::interface_configuration_type::NONE};
}

controller_interface::InterfaceConfiguration
MecanumDriveOdomPublisher::state_interface_configuration() const {
  controller_interface::InterfaceConfiguration state_interfaces_config;
  state_interfaces_config.type =
      controller_interface::interface_configuration_type::INDIVIDUAL;

  state_interfaces_config.names.reserve(state_joint_names_.size());

  for (const auto &joint : state_joint_names_) {
    state_interfaces_config.names.push_back(joint + "/" +
                                            params_.interface_name);
  }

  return state_interfaces_config;
}

controller_interface::CallbackReturn MecanumDriveOdomPublisher::on_activate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::CallbackReturn MecanumDriveOdomPublisher::on_deactivate(
    const rclcpp_lifecycle::State & /*previous_state*/) {
  return controller_interface::CallbackReturn::SUCCESS;
}

controller_interface::return_type
MecanumDriveOdomPublisher::update(const rclcpp::Time &time,
                                  const rclcpp::Duration &period) {
  // FORWARD KINEMATICS (odometry).
  double wheel_front_left_vel = state_interfaces_[0].get_value();
  double wheel_back_left_vel = state_interfaces_[1].get_value();
  double wheel_back_right_vel = state_interfaces_[2].get_value();
  double wheel_front_right_vel = state_interfaces_[3].get_value();

  if (!std::isnan(wheel_front_left_vel) && !std::isnan(wheel_back_left_vel) &&
      !std::isnan(wheel_back_right_vel) && !std::isnan(wheel_front_right_vel)) {
    // Estimate twist (using joint information) and integrate
    odometry_.update(wheel_front_left_vel, wheel_back_left_vel,
                     wheel_back_right_vel, wheel_front_right_vel,
                     period.seconds());
  }

  // Publish odometry message
  // Compute and store orientation info
  tf2::Quaternion orientation;
  orientation.setRPY(0.0, 0.0, odometry_.getRz());

  // Populate odom message and publish
  if (rt_odom_state_publisher_->trylock()) {
    rt_odom_state_publisher_->msg_.header.stamp = time;
    rt_odom_state_publisher_->msg_.pose.pose.position.x = odometry_.getX();
    rt_odom_state_publisher_->msg_.pose.pose.position.y = odometry_.getY();
    rt_odom_state_publisher_->msg_.pose.pose.orientation =
        tf2::toMsg(orientation);
    rt_odom_state_publisher_->msg_.twist.twist.linear.x = odometry_.getVx();
    rt_odom_state_publisher_->msg_.twist.twist.linear.y = odometry_.getVy();
    rt_odom_state_publisher_->msg_.twist.twist.angular.z = odometry_.getWz();
    rt_odom_state_publisher_->unlockAndPublish();
  }

  // Publish tf /odom frame
  if (params_.enable_odom_tf && rt_tf_odom_state_publisher_->trylock()) {
    rt_tf_odom_state_publisher_->msg_.transforms.front().header.stamp = time;
    rt_tf_odom_state_publisher_->msg_.transforms.front()
        .transform.translation.x = odometry_.getX();
    rt_tf_odom_state_publisher_->msg_.transforms.front()
        .transform.translation.y = odometry_.getY();
    rt_tf_odom_state_publisher_->msg_.transforms.front().transform.rotation =
        tf2::toMsg(orientation);
    rt_tf_odom_state_publisher_->unlockAndPublish();
  }

  return controller_interface::return_type::OK;
}

} // namespace mecanum_drive_odom_publisher

#include "pluginlib/class_list_macros.hpp"

PLUGINLIB_EXPORT_CLASS(mecanum_drive_odom_publisher::MecanumDriveOdomPublisher,
                       controller_interface::ControllerInterface)
