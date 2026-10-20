"""Regression test: in simulation, the robot drives towards the wall and stops before hitting it.

Fails if the robot never moves, hits the wall, or is still moving at the end.
"""

import os
import time
import unittest

import launch
import launch_testing
import launch_testing.actions
import launch_testing.asserts
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from nav_msgs.msg import Odometry
from rclpy.parameter import Parameter

WALL_FACE_X = 2.9          # from wall_world.sdf
ROBOT_FRONT_FROM_CENTER = 0.2
SIM_SECONDS = 15.0         # long enough to reach the wall at 0.3 m/s
WALL_CLOCK_TIMEOUT = 180.0


@pytest.mark.launch_test
def generate_test_description():
    sim = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(get_package_share_directory('sim_test'), 'launch', 'sim.launch.py')))
    return launch.LaunchDescription([sim, launch_testing.actions.ReadyToTest()])


class TestStopsBeforeWall(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def test_robot_stops_before_wall(self):
        node = rclpy.create_node(
            'stop_checker', parameter_overrides=[Parameter('use_sim_time', value=True)])
        # ground_truth is the simulator's real pose; wheel odometry would keep counting
        # if the wheels spun against the wall.
        odom = []
        node.create_subscription(Odometry, 'ground_truth', odom.append, 10)

        start = time.monotonic()
        while time.monotonic() - start < WALL_CLOCK_TIMEOUT:
            rclpy.spin_once(node, timeout_sec=0.1)
            if odom and odom[-1].header.stamp.sec >= SIM_SECONDS:
                break
        node.destroy_node()

        self.assertTrue(odom, 'no ground truth received from the simulation')
        last = odom[-1]
        sim_time = last.header.stamp.sec + last.header.stamp.nanosec * 1e-9
        self.assertGreaterEqual(sim_time, SIM_SECONDS, f'simulation only reached {sim_time:.1f} s')

        x = last.pose.pose.position.x
        front = x + ROBOT_FRONT_FROM_CENTER
        speed = abs(last.twist.twist.linear.x)
        print(f'final x={x:.3f} m, gap to wall={WALL_FACE_X - front:.3f} m, speed={speed:.3f} m/s')

        self.assertGreater(x, 1.0, 'robot barely moved')
        self.assertLess(front, WALL_FACE_X - 0.1, 'robot got within 10 cm of the wall')
        self.assertLess(speed, 0.02, 'robot is still moving')


@launch_testing.post_shutdown_test()
class TestShutdown(unittest.TestCase):

    def test_processes_exited(self, proc_info):
        # Gazebo is killed at shutdown, so only check that nothing crashed with an error code
        # other than the usual SIGINT/SIGTERM ones.
        launch_testing.asserts.assertExitCodes(proc_info, allowable_exit_codes=[0, -2, -15, 130, 143])
