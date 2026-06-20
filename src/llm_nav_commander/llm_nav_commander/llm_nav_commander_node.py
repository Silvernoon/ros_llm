"""
LLM Navigation Commander Node
Main node that integrates Gemma-4-E2B with YOLOE detections for navigation
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray
from geometry_msgs.msg import Twist, PoseStamped
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from cv_bridge import CvBridge
import numpy as np
import json
from typing import Optional, Dict, Any

from .gemma_model import GemmaVisionModel


class LLMNavCommanderNode(Node):
    """
    ROS 2 node that uses Gemma-4-E2B LLM for vision-based navigation
    Subscribes to camera images and YOLOE detections, publishes navigation commands
    """

    def __init__(self):
        super().__init__("llm_nav_commander")

        # Declare parameters
        self.declare_parameter("model_name", "google/gemma-4-E2B-it")
        self.declare_parameter("device", "cuda")
        self.declare_parameter("image_topic", "/camera/image_raw")
        self.declare_parameter("detections_topic", "/yoloe/detections")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("odom_topic", "/odom")
        self.declare_parameter("goal_topic", "/navigation_goal")
        self.declare_parameter("analysis_topic", "/scene_analysis")
        self.declare_parameter("command_topic", "/nav_command")
        self.declare_parameter("update_rate", 2.0)  # Hz
        self.declare_parameter("enable_auto_navigation", False)
        self.declare_parameter("linear_speed_slow", 0.2)
        self.declare_parameter("linear_speed_medium", 0.4)
        self.declare_parameter("linear_speed_fast", 0.6)
        self.declare_parameter("angular_speed_slow", 0.3)
        self.declare_parameter("angular_speed_medium", 0.6)
        self.declare_parameter("angular_speed_fast", 0.9)

        # Get parameters
        model_name = self.get_parameter("model_name").value
        device = self.get_parameter("device").value
        self.image_topic = self.get_parameter("image_topic").value
        self.detections_topic = self.get_parameter("detections_topic").value
        self.cmd_vel_topic = self.get_parameter("cmd_vel_topic").value
        self.odom_topic = self.get_parameter("odom_topic").value
        self.goal_topic = self.get_parameter("goal_topic").value
        self.analysis_topic = self.get_parameter("analysis_topic").value
        self.command_topic = self.get_parameter("command_topic").value
        self.update_rate = self.get_parameter("update_rate").value
        self.enable_auto_nav = self.get_parameter("enable_auto_navigation").value

        # Speed parameters
        self.speed_config = {
            "slow": {
                "linear": self.get_parameter("linear_speed_slow").value,
                "angular": self.get_parameter("angular_speed_slow").value,
            },
            "medium": {
                "linear": self.get_parameter("linear_speed_medium").value,
                "angular": self.get_parameter("angular_speed_medium").value,
            },
            "fast": {
                "linear": self.get_parameter("linear_speed_fast").value,
                "angular": self.get_parameter("angular_speed_fast").value,
            },
        }

        self.get_logger().info("Initializing LLM Navigation Commander")
        self.get_logger().info(f"Model: {model_name}")
        self.get_logger().info(f"Device: {device}")
        self.get_logger().info(f"Auto navigation: {self.enable_auto_nav}")

        # Initialize CV Bridge
        self.bridge = CvBridge()

        # State variables
        self.latest_image: Optional[np.ndarray] = None
        self.latest_detections: Optional[Detection2DArray] = None
        self.current_goal: Optional[str] = None
        self.current_odom: Optional[Odometry] = None
        self.last_command_time = self.get_clock().now()

        # QoS profiles
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # Subscribers
        self.image_sub = self.create_subscription(
            Image, self.image_topic, self.image_callback, sensor_qos
        )

        self.detections_sub = self.create_subscription(
            Detection2DArray,
            self.detections_topic,
            self.detections_callback,
            reliable_qos,
        )

        self.goal_sub = self.create_subscription(
            String, self.goal_topic, self.goal_callback, reliable_qos
        )

        self.odom_sub = self.create_subscription(
            Odometry, self.odom_topic, self.odom_callback, sensor_qos
        )

        # Publishers
        self.cmd_vel_pub = self.create_publisher(
            Twist, self.cmd_vel_topic, reliable_qos
        )

        self.analysis_pub = self.create_publisher(
            String, self.analysis_topic, reliable_qos
        )

        self.command_pub = self.create_publisher(
            String, self.command_topic, reliable_qos
        )

        # Initialize Gemma model
        try:
            self.get_logger().info("Loading Gemma model...")
            self.model = GemmaVisionModel(model_name=model_name, device=device)
            self.get_logger().info("Gemma model loaded successfully")
        except Exception as e:
            self.get_logger().error(f"Failed to load Gemma model: {e}")
            self.model = None
            return

        # Timer for periodic analysis
        self.timer = self.create_timer(1.0 / self.update_rate, self.process_navigation)

        self.get_logger().info("LLM Navigation Commander initialized")

    def image_callback(self, msg: Image):
        """Store latest image"""
        try:
            self.latest_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")

    def detections_callback(self, msg: Detection2DArray):
        """Store latest detections"""
        self.latest_detections = msg

    def goal_callback(self, msg: String):
        """Update navigation goal"""
        self.current_goal = msg.data
        self.get_logger().info(f"New navigation goal: {self.current_goal}")

    def odom_callback(self, msg: Odometry):
        """Store current odometry"""
        self.current_odom = msg

    def process_navigation(self):
        """Main processing loop - analyze scene and generate commands"""
        if self.model is None:
            return

        if self.latest_image is None:
            self.get_logger().debug("Waiting for image...", throttle_duration_sec=5.0)
            return

        if not self.enable_auto_nav and self.current_goal is None:
            return

        try:
            # Parse detections
            detections_list = self._parse_detections(self.latest_detections)

            # Generate navigation command using LLM
            goal = self.current_goal or "Navigate safely forward"

            current_state = self._get_current_state()

            command = self.model.generate_navigation_command(
                image=self.latest_image,
                goal=goal,
                detections=detections_list,
                current_state=current_state,
            )

            # Publish command analysis
            command_msg = String()
            command_msg.data = json.dumps(command, indent=2)
            self.command_pub.publish(command_msg)

            self.get_logger().info(
                f"Command: {command['direction']} at {command['speed']} - {command['reason']}"
            )

            # Execute command if auto navigation is enabled
            if self.enable_auto_nav:
                self._execute_command(command)

        except Exception as e:
            self.get_logger().error(f"Error processing navigation: {e}")

    def _parse_detections(self, detections_msg: Optional[Detection2DArray]) -> list:
        """Convert Detection2DArray to list of dicts"""
        if detections_msg is None:
            return []

        detections = []
        for detection in detections_msg.detections:
            if len(detection.results) > 0:
                result = detection.results[0]
                detections.append(
                    {
                        "class_id": result.hypothesis.class_id,
                        "class_name": result.hypothesis.class_id,  # Would need class names lookup
                        "score": result.hypothesis.score,
                        "bbox": {
                            "x": detection.bbox.center.position.x,
                            "y": detection.bbox.center.position.y,
                            "width": detection.bbox.size_x,
                            "height": detection.bbox.size_y,
                        },
                    }
                )

        return detections

    def _get_current_state(self) -> str:
        """Get current robot state description"""
        if self.current_odom is None:
            return "Position unknown"

        pos = self.current_odom.pose.pose.position
        vel = self.current_odom.twist.twist.linear

        return f"Position: ({pos.x:.2f}, {pos.y:.2f}), Velocity: {vel.x:.2f} m/s"

    def _execute_command(self, command: Dict[str, Any]):
        """Convert LLM command to Twist message and publish"""
        twist = Twist()

        direction = command.get("direction", "stop")
        speed = command.get("speed", "slow")

        # Get speed values
        speed_vals = self.speed_config.get(speed, self.speed_config["slow"])

        # Set velocities based on direction
        if direction == "forward":
            twist.linear.x = speed_vals["linear"]
        elif direction == "backward":
            twist.linear.x = -speed_vals["linear"]
        elif direction == "left":
            twist.angular.z = speed_vals["angular"]
        elif direction == "right":
            twist.angular.z = -speed_vals["angular"]
        elif direction == "stop":
            pass  # All zeros

        # Publish command
        self.cmd_vel_pub.publish(twist)

        # Warn if there are safety concerns
        if command.get("warning"):
            self.get_logger().warn(f"Safety warning: {command['warning']}")


def main(args=None):
    rclpy.init(args=args)
    node = LLMNavCommanderNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the robot
        if node.enable_auto_nav:
            twist = Twist()
            node.cmd_vel_pub.publish(twist)

        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
