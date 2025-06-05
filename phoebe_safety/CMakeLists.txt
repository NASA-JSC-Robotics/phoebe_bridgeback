cmake_minimum_required(VERSION 3.5)
project(phoebe_safety)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(phoebe_interfaces REQUIRED)

ament_python_install_package(${PROJECT_NAME})

install(
  DIRECTORY launch
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
    phoebe_safety/mock_estop_publisher.py
    phoebe_safety/pb_safety_light_manager.py
    phoebe_safety/estop_manager.py
    DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  set(_pytest_tests
    test/estop_manager_test.py
    # Add other test files here
  )
  foreach(_test_path ${_pytest_tests})
    get_filename_component(_test_name ${_test_path} NAME_WE)
    ament_add_pytest_test(${_test_name} ${_test_path}
      APPEND_ENV PYTHONPATH=${CMAKE_CURRENT_BINARY_DIR}
      TIMEOUT 60
      WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    )
  endforeach()

  install(
    FILES test/mock_controllers.yaml
    DESTINATION share/${PROJECT_NAME}/test
  )

  # ament_add_pytest_test(test_safety_light_manager test/test_safety_light_manager.py)
endif()

ament_export_dependencies(${THIS_PACKAGE_INCLUDE_DEPENDS})
ament_package()
