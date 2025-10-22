cmake_minimum_required(VERSION 3.16)
project(mecanum_drive_odom_publisher LANGUAGES CXX)

if(CMAKE_CXX_COMPILER_ID MATCHES "(GNU|Clang)")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
set(THIS_PACKAGE_INCLUDE_DEPENDS
  controller_interface
  hardware_interface
  generate_parameter_library
  nav_msgs
  pluginlib
  rclcpp
  rclcpp_lifecycle
  realtime_tools
  std_srvs
  tf2
  tf2_geometry_msgs
  tf2_msgs
)

find_package(ament_cmake REQUIRED)
find_package(backward_ros REQUIRED)
foreach(Dependency IN ITEMS ${THIS_PACKAGE_INCLUDE_DEPENDS})
  find_package(${Dependency} REQUIRED)
endforeach()

generate_parameter_library(mecanum_drive_odom_publisher_parameters
  src/mecanum_drive_odom_publisher.yaml
)

add_library(
  mecanum_drive_odom_publisher
  SHARED
  src/mecanum_drive_odom_publisher.cpp
  src/odometry.cpp
)
target_compile_features(mecanum_drive_odom_publisher PUBLIC cxx_std_17)
target_include_directories(mecanum_drive_odom_publisher PUBLIC
  "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>"
  "$<INSTALL_INTERFACE:include/${PROJECT_NAME}>")
target_link_libraries(mecanum_drive_odom_publisher PUBLIC
  mecanum_drive_odom_publisher_parameters)
ament_target_dependencies(mecanum_drive_odom_publisher PUBLIC ${THIS_PACKAGE_INCLUDE_DEPENDS})

# Causes the visibility macros to use dllexport rather than dllimport,
# which is appropriate when building the dll but not consuming it.
target_compile_definitions(mecanum_drive_odom_publisher PRIVATE "ACKERMANN_STEERING_CONTROLLER_BUILDING_DLL")

pluginlib_export_plugin_description_file(
  controller_interface mecanum_drive_odom_publisher.xml)

if(BUILD_TESTING)
  # no testing for now

  # find_package(ament_cmake_gmock REQUIRED)
  # find_package(controller_manager REQUIRED)
  # find_package(hardware_interface REQUIRED)
  # find_package(ros2_control_test_assets REQUIRED)

  # ament_add_gmock(test_load_mecanum_drive_odom_publisher test/test_load_mecanum_drive_odom_publisher.cpp)
  # target_include_directories(test_load_mecanum_drive_odom_publisher PRIVATE include)
  # ament_target_dependencies(
  #   test_load_mecanum_drive_odom_publisher
  #   controller_manager
  #   hardware_interface
  #   ros2_control_test_assets
  # )

  # add_rostest_with_parameters_gmock(
  #   test_mecanum_drive_odom_publisher test/test_mecanum_drive_odom_publisher.cpp
  #   ${CMAKE_CURRENT_SOURCE_DIR}/test/mecanum_drive_odom_publisher_params.yaml)
  # target_include_directories(test_mecanum_drive_odom_publisher PRIVATE include)
  # target_link_libraries(test_mecanum_drive_odom_publisher mecanum_drive_odom_publisher)
  # ament_target_dependencies(
  #   test_mecanum_drive_odom_publisher
  #   controller_interface
  #   hardware_interface
  # )

  # add_rostest_with_parameters_gmock(
  #   test_mecanum_drive_odom_publisher_preceeding test/test_mecanum_drive_odom_publisher_preceeding.cpp
  #   ${CMAKE_CURRENT_SOURCE_DIR}/test/mecanum_drive_odom_publisher_preceeding_params.yaml)
  # target_include_directories(test_mecanum_drive_odom_publisher_preceeding PRIVATE include)
  # target_link_libraries(test_mecanum_drive_odom_publisher_preceeding mecanum_drive_odom_publisher)
  # ament_target_dependencies(
  #   test_mecanum_drive_odom_publisher_preceeding
  #   controller_interface
  #   hardware_interface
  # )
endif()

install(
  DIRECTORY include/
  DESTINATION include/mecanum_drive_odom_publisher
)

install(
  TARGETS mecanum_drive_odom_publisher mecanum_drive_odom_publisher_parameters
  EXPORT export_mecanum_drive_odom_publisher
  RUNTIME DESTINATION bin
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
)

ament_export_targets(export_mecanum_drive_odom_publisher HAS_LIBRARY_TARGET)
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()
