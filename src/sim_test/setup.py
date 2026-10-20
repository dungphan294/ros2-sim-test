from glob import glob

from setuptools import find_packages, setup

package_name = 'sim_test'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/worlds', glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Van Dung Phan',
    maintainer_email='dungpv.294@gmail.com',
    description='A small robot in Gazebo that must stop before a wall, checked by a regression test.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'safety_stop = sim_test.safety_stop:main',
        ],
    },
)
