#!/usr/bin/env python3
"""
Interactive demo script for LLM Nav Commander
Allows real-time interaction with the system
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import json
import sys
import threading


class InteractiveDemo(Node):
    def __init__(self):
        super().__init__('interactive_demo')
        
        # Publishers
        self.goal_pub = self.create_publisher(String, '/navigation_goal', 10)
        self.query_pub = self.create_publisher(String, '/scene_query', 10)
        
        # Subscribers
        self.command_sub = self.create_subscription(
            String,
            '/nav_command',
            self.command_callback,
            10
        )
        
        self.analysis_sub = self.create_subscription(
            String,
            '/scene_analysis',
            self.analysis_callback,
            10
        )
        
        self.response_sub = self.create_subscription(
            String,
            '/scene_response',
            self.response_callback,
            10
        )
        
        self.latest_command = None
        self.latest_analysis = None
        self.latest_response = None
    
    def command_callback(self, msg):
        try:
            self.latest_command = json.loads(msg.data)
            print("\n" + "="*60)
            print("📍 Navigation Command:")
            print(f"  Direction: {self.latest_command.get('direction', 'N/A')}")
            print(f"  Speed: {self.latest_command.get('speed', 'N/A')}")
            print(f"  Reason: {self.latest_command.get('reason', 'N/A')}")
            if self.latest_command.get('warning'):
                print(f"  ⚠️  Warning: {self.latest_command.get('warning')}")
            print("="*60)
        except:
            pass
    
    def analysis_callback(self, msg):
        try:
            self.latest_analysis = json.loads(msg.data)
            print("\n" + "="*60)
            print("🔍 Scene Analysis:")
            print(f"  Objects detected: {self.latest_analysis.get('detections_count', 0)}")
            print(f"  Analysis:\n    {self.latest_analysis.get('analysis', 'N/A')[:200]}...")
            print("="*60)
        except:
            pass
    
    def response_callback(self, msg):
        try:
            self.latest_response = json.loads(msg.data)
            print("\n" + "="*60)
            print("💬 Query Response:")
            print(f"  Q: {self.latest_response.get('question', 'N/A')}")
            print(f"  A: {self.latest_response.get('answer', 'N/A')}")
            print("="*60)
        except:
            pass
    
    def send_goal(self, goal_text):
        msg = String()
        msg.data = goal_text
        self.goal_pub.publish(msg)
        print(f"✅ Sent goal: {goal_text}")
    
    def send_query(self, query_text):
        msg = String()
        msg.data = query_text
        self.query_pub.publish(msg)
        print(f"✅ Sent query: {query_text}")


def print_menu():
    print("\n" + "="*60)
    print("🤖 LLM Navigation Commander - Interactive Demo")
    print("="*60)
    print("Commands:")
    print("  g <text>  - Send navigation goal")
    print("  q <text>  - Ask question about scene")
    print("  1-5       - Quick commands")
    print("  h         - Show this help")
    print("  x         - Exit")
    print("\nQuick commands:")
    print("  1 - Move forward slowly")
    print("  2 - Turn left")
    print("  3 - Turn right")
    print("  4 - Stop")
    print("  5 - Analyze scene")
    print("="*60)


def input_thread(demo_node):
    """Thread for handling user input"""
    print_menu()
    
    quick_goals = {
        '1': "Move forward slowly and avoid obstacles",
        '2': "Turn left carefully",
        '3': "Turn right carefully",
        '4': "Stop immediately",
    }
    
    quick_queries = {
        '5': "What do you see in this scene? Describe obstacles and clear paths.",
    }
    
    while rclpy.ok():
        try:
            cmd = input("\n> ").strip()
            
            if not cmd:
                continue
            
            if cmd == 'x':
                print("Exiting...")
                rclpy.shutdown()
                break
            
            elif cmd == 'h':
                print_menu()
            
            elif cmd in quick_goals:
                demo_node.send_goal(quick_goals[cmd])
            
            elif cmd in quick_queries:
                demo_node.send_query(quick_queries[cmd])
            
            elif cmd.startswith('g '):
                goal_text = cmd[2:].strip()
                if goal_text:
                    demo_node.send_goal(goal_text)
                else:
                    print("❌ Empty goal")
            
            elif cmd.startswith('q '):
                query_text = cmd[2:].strip()
                if query_text:
                    demo_node.send_query(query_text)
                else:
                    print("❌ Empty query")
            
            else:
                print(f"❌ Unknown command: {cmd}")
                print("Type 'h' for help")
        
        except EOFError:
            break
        except KeyboardInterrupt:
            break


def main():
    rclpy.init()
    demo_node = InteractiveDemo()
    
    # Start input thread
    input_t = threading.Thread(target=input_thread, args=(demo_node,), daemon=True)
    input_t.start()
    
    # Spin node
    try:
        rclpy.spin(demo_node)
    except KeyboardInterrupt:
        pass
    finally:
        demo_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
