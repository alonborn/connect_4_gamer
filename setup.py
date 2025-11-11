from setuptools import setup

package_name = 'connect_4_gamer'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Alon',
    maintainer_email='alon@example.com',
    description='Connect 4 gamer ROS node',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'connect_4_gamer = connect_4_gamer.connect_4_gamer:main',  # ✅ executable name maps to your file
        ],
    },
)
