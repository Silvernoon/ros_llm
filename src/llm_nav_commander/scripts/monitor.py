#!/usr/bin/env python3
"""
Monitor script - displays all LLM Nav Commander outputs in real-time
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import json
from datetime import datetime


class Monitor(Node):
    def __init__(self):
        super().__init__('llm_monitor')
        
        # Subscribers
        self.create_subscription(String, '/nav_command', self.command_callback, 10)
        self.create_subscription(String, '/scene_analysis', self.analysis_callback, 10)
        self.create_subscription(String, '/scene_response', self.response_callback, 10)
        self.create_subscription(Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        
        print("🔍 LLM Nav Commander Monitor Started")
        print("="*70)
        print("Listening to:")
        print("  - /nav_command")
        print("  - /scene_analysis")
        print("  - /scene_response")
        print("  - /cmd_vel")
        print("="*70 + "\n")
    
    def command_callback(self, msg):
        try:
            data = json.loads(msg.data)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{timestamp}] 📍 NAVIGATION COMMAND")
            print(f"  Direction : {data.get('direction', 'N/A').upper()}")
            print(f"  Speed     : {data.get('speed', 'N/A').upper()}")
            print(f"  Reason    : {data.get('reason', 'N/A')}")
            
            if data.get('warning'):
                print(f"  ⚠️  WARNING : {data.get('warning')}")
            
            print("-"*70)
        except Exception as e:
            print(f"Error parsing command: {e}")
    
    def analysis_callback(self, msg):
        try:
            data = json.loads(msg.data)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{timestamp}] 🔍 SCENE ANALYSIS")
            print(f"  Objects   : {data.get('detections_count', 0)} detected")
            
            analysis_text = data.get('analysis', 'N/A')
            # Print first 200 chars
            if len(analysis_text) > 200:
                print(f"  Analysis  : {analysis_text[:200]}...")
            else:
                print(f"  Analysis  : {analysis_text}")
            
            print("-"*70)
        except Exception as e:
            print(f"Error parsing analysis: {e}")
    
    def response_callback(self, msg):
        try:
            data = json.loads(msg.data)
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{timestamp}] 💬 QUERY RESPONSE")
            print(f"  Question  : {data.get('question', 'N/A')}")
            print(f"  Answer    : {data.get('answer', 'N/A')}")
            print("-"*70)
        except Exception as e:
            print(f"Error parsing response: {e}")
    
    def cmd_vel_callback(self, msg):
        # Only print non-zero commands
        if msg.linear.x != 0 or msg.angular.z != 0:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] 🚗 CMD_VEL")
            print(f"  Linear  : {msg.linear.x:.3f} m/s")
            print(f"  Angular : {msg.angular.z:.3f} rad/s")
            print("-"*70)


def main():
    rclpy.init()
    monitor = Monitor()
    
    try:
        rclpy.spin(monitor)
    except KeyboardInterrupt:
        print("\nMonitor stopped")
    finally:
        monitor.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
