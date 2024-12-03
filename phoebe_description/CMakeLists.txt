cmake_minimum_required(VERSION 3.5)
project(phoebe_description)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)

install(
  DIRECTORY launch meshes rviz urdf
  DESTINATION share/${PROJECT_NAME}
)

ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})

ament_python_install_package(${PROJECT_NAME})

install(PROGRAMS
  phoebe_description/scripts/spawn_phoebe.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
