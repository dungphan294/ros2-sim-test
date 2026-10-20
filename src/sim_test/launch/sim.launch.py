"""Start Gazebo with the wall world, bridge its topics to ROS 2, and start the safety_stop node.

    ros2 launch sim_test sim.launch.py            # headless, as in CI
    ros2 launch sim_test sim.launch.py gui:=true  # with the Gazebo window
"""

import os
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('sim_test')
    world = os.path.join(share, 'worlds', 'wall_world.sdf')
    gz_launch = os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
    gui = LaunchConfiguration('gui')

    # -r starts the simulation running; -s is server only (no window).
    gazebo_headless = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch),
        launch_arguments={'gz_args': f'-r -s --headless-rendering {world}', 'on_exit_shutdown': 'true'}.items(),
        condition=UnlessCondition(gui),
    )
    gazebo_gui = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gz_launch),
        launch_arguments={'gz_args': f'-r {world}', 'on_exit_shutdown': 'true'}.items(),
        condition=IfCondition(gui),
    )

    # ] = ROS 2 to Gazebo, [ = Gazebo to ROS 2.
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            '/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/ground_truth@nav_msgs/msg/Odometry[gz.msgs.Odometry',
            '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
        ],
        output='screen',
    )

    safety_stop = Node(
        package='sim_test',
        executable='safety_stop',
        parameters=[{
            'use_sim_time': True,
            'speed': LaunchConfiguration('speed'),
            'stop_distance': LaunchConfiguration('stop_distance'),
        }],
        output='screen',
    )

    # The gz sim server outlives the launch on Ctrl+C or test shutdown. A second run would then
    # read the old simulation's topics, so stop it explicitly.
    def kill_gazebo(event, context):
        subprocess.run(['pkill', '-f', world], check=False)
        return None  # launch accepts only None or a list of actions here

    stop_gazebo = RegisterEventHandler(OnShutdown(on_shutdown=kill_gazebo))

    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='false'),
        DeclareLaunchArgument('speed', default_value='0.3'),
        DeclareLaunchArgument('stop_distance', default_value='0.5'),
        gazebo_headless,
        gazebo_gui,
        bridge,
        safety_stop,
        stop_gazebo,
    ])
