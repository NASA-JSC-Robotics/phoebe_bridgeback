cmake_minimum_required(VERSION 3.5)
project(phoebe_deploy)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(
  DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
    scripts/keyboard_joy.py
    scripts/magic_carpet_diff_drive.py
    scripts/odometry_joint_state_publisher.py
    scripts/prioritize_threads.sh
    scripts/world_publisher.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})

ament_package()
