"""Drive forward, and stop when the lidar sees something closer than stop_distance."""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class SafetyStop(Node):

    def __init__(self):
        super().__init__('safety_stop')
        self.speed = self.declare_parameter('speed', 0.3).value
        self.stop_distance = self.declare_parameter('stop_distance', 0.5).value
        # Only look at the beams within this angle of straight ahead.
        self.front_half_angle = self.declare_parameter('front_half_angle', 0.3).value
        self.get_logger().info(f'speed={self.speed} m/s, stop_distance={self.stop_distance} m')

        self.latest_scan = None
        self.create_subscription(LaserScan, 'scan', self.on_scan, 10)
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.create_timer(0.1, self.on_timer)

    def on_scan(self, msg):
        self.latest_scan = msg

    def closest_ahead(self, scan):
        closest = math.inf
        for i, r in enumerate(scan.ranges):
            angle = scan.angle_min + i * scan.angle_increment
            if abs(angle) <= self.front_half_angle and scan.range_min <= r <= scan.range_max:
                closest = min(closest, r)
        return closest

    def on_timer(self):
        cmd = Twist()
        # No scan yet means we cannot see, so we do not move.
        if self.latest_scan is not None and self.closest_ahead(self.latest_scan) > self.stop_distance:
            cmd.linear.x = self.speed
        self.cmd_pub.publish(cmd)


def main():
    rclpy.init()
    node = SafetyStop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
