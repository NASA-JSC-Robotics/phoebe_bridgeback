cmake_minimum_required(VERSION 3.8)
project(phoebe_mujoco_config)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    config
    description
    launch
    resources
    urdf
  DESTINATION
    share/${PROJECT_NAME}
)

# Install python tools
install(PROGRAMS
  scripts/wheel_code_gen.py
  scripts/post_process_mjcf.py
  scripts/post_process_mjcf_runtime.py
  scripts/mock_polled_camera.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
