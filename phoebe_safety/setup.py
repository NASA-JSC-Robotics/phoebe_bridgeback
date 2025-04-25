from setuptools import find_packages, setup

package_name = "phoebe_safety"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="zbashir",
    maintainer_email="zarrin.t.bashir@nasa.gov",
    description="TODO: Package description",
    license="Apache-2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "pb_safety_light_manager = phoebe_safety.pb_safety_light_manager:main",
            "mock_estop_publisher = phoebe_safety.mock_estop_publisher:main",
            "mock_lights = phoebe_safety.mock_lights:main",
        ],
    },
)
