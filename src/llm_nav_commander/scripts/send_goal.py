#!/usr/bin/env python3
"""
Example script: Send navigation goals to the LLM commander
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import sys


class GoalPublisher(Node):
    def __init__(self):
        super().__init__('goal_publisher')
        self.publisher = self.create_publisher(String, '/navigation_goal', 10)
    
    def send_goal(self, goal_text):
        msg = String()
        msg.data = goal_text
        self.publisher.publish(msg)
        self.get_logger().info(f'Sent goal: {goal_text}')


def main():
    rclpy.init()
    node = GoalPublisher()
    
    # Example goals
    goals = [
        "Navigate forward slowly and avoid any obstacles",
        "Find a clear path to move forward",
        "Turn right to go around the obstacle",
        "Stop if there are any safety concerns",
    ]
    
    if len(sys.argv) > 1:
        # Use command line argument
        goal = ' '.join(sys.argv[1:])
        node.send_goal(goal)
    else:
        # Send example goals
        print("Sending example goals...")
        for goal in goals:
            node.send_goal(goal)
            rclpy.spin_once(node, timeout_sec=0.5)
    
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
