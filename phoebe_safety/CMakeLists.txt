cmake_minimum_required(VERSION 3.5)
project(phoebe_safety)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
ament_python_install_package(${PROJECT_NAME})

install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
    phoebe_safety/mock_estop_publisher.py
    phoebe_safety/pb_safety_light_manager.py
    DESTINATION lib/${PROJECT_NAME}
)
ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()
