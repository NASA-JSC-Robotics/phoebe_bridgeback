from setuptools import find_packages, setup

package_name = "phoebe_status_handler_py"

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
    maintainer="er4-user",
    maintainer_email="mark.paterson@nasa.gov",
    description="Status handlers for the Phoebe Bridgeback robot",
    license="Apache License, Version 2.0",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["phoebe_status_terminal = phoebe_status_handler_py.phoebe_status_terminal:main"],
    },
)
