#!/usr/bin/env python3
"""
Scene Analyzer Node
Provides scene analysis service without autonomous navigation
Useful for testing and understanding what the LLM sees
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray
from std_msgs.msg import String
from cv_bridge import CvBridge
import numpy as np
import json
from typing import Optional

from .gemma_model import GemmaVisionModel


class SceneAnalyzerNode(Node):
    """
    Scene analysis node - analyzes images with LLM but doesn't command navigation
    """
    
    def __init__(self):
        super().__init__('scene_analyzer')
        
        # Declare parameters
        self.declare_parameter('model_name', 'google/gemma-4-E2B-it')
        self.declare_parameter('device', 'cuda')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('detections_topic', '/yoloe/detections')
        self.declare_parameter('analysis_topic', '/scene_analysis')
        self.declare_parameter('query_topic', '/scene_query')
        self.declare_parameter('response_topic', '/scene_response')
        self.declare_parameter('analysis_rate', 1.0)  # Hz
        self.declare_parameter('auto_analyze', True)
        
        # Get parameters
        model_name = self.get_parameter('model_name').value
        device = self.get_parameter('device').value
        self.image_topic = self.get_parameter('image_topic').value
        self.detections_topic = self.get_parameter('detections_topic').value
        self.analysis_topic = self.get_parameter('analysis_topic').value
        self.query_topic = self.get_parameter('query_topic').value
        self.response_topic = self.get_parameter('response_topic').value
        self.analysis_rate = self.get_parameter('analysis_rate').value
        self.auto_analyze = self.get_parameter('auto_analyze').value
        
        self.get_logger().info('Initializing Scene Analyzer')
        self.get_logger().info(f'Model: {model_name}')
        self.get_logger().info(f'Device: {device}')
        
        # Initialize CV Bridge
        self.bridge = CvBridge()
        
        # State variables
        self.latest_image: Optional[np.ndarray] = None
        self.latest_detections: Optional[Detection2DArray] = None
        
        # QoS profiles
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        reliable_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10
        )
        
        # Subscribers
        self.image_sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            sensor_qos
        )
        
        self.detections_sub = self.create_subscription(
            Detection2DArray,
            self.detections_topic,
            self.detections_callback,
            reliable_qos
        )
        
        self.query_sub = self.create_subscription(
            String,
            self.query_topic,
            self.query_callback,
            reliable_qos
        )
        
        # Publishers
        self.analysis_pub = self.create_publisher(
            String,
            self.analysis_topic,
            reliable_qos
        )
        
        self.response_pub = self.create_publisher(
            String,
            self.response_topic,
            reliable_qos
        )
        
        # Initialize Gemma model
        try:
            self.get_logger().info('Loading Gemma model...')
            self.model = GemmaVisionModel(model_name=model_name, device=device)
            self.get_logger().info('Gemma model loaded successfully')
        except Exception as e:
            self.get_logger().error(f'Failed to load Gemma model: {e}')
            self.model = None
            return
        
        # Timer for periodic analysis
        if self.auto_analyze:
            self.timer = self.create_timer(
                1.0 / self.analysis_rate,
                self.analyze_scene
            )
        
        self.get_logger().info('Scene Analyzer initialized')
        self.get_logger().info(f'Publish questions to: {self.query_topic}')
        self.get_logger().info(f'Responses on: {self.response_topic}')
    
    def image_callback(self, msg: Image):
        """Store latest image"""
        try:
            self.latest_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
        except Exception as e:
            self.get_logger().error(f'Failed to convert image: {e}')
    
    def detections_callback(self, msg: Detection2DArray):
        """Store latest detections"""
        self.latest_detections = msg
    
    def query_callback(self, msg: String):
        """Handle custom queries about the scene"""
        if self.model is None:
            self.get_logger().error('Model not loaded')
            return

        try:
            question = msg.data
            if self.latest_image is None:
                self.get_logger().info(
                    'No image available, answering query in text-only mode'
                )
            self.get_logger().info(f'Processing query: {question}')

            # latest_image may be None -> text-only inference
            answer = self.model.ask_question(self.latest_image, question)

            response_msg = String()
            response_msg.data = json.dumps({
                'question': question,
                'answer': answer,
                'text_only': self.latest_image is None,
                'timestamp': self.get_clock().now().to_msg().sec
            }, indent=2)

            self.response_pub.publish(response_msg)
            self.get_logger().info(f'Answer: {answer[:100]}...')

        except Exception as e:
            self.get_logger().error(f'Error processing query: {e}')
    
    def analyze_scene(self):
        """Periodic scene analysis"""
        if self.model is None or self.latest_image is None:
            return
        
        try:
            # Parse detections
            detections_list = self._parse_detections(self.latest_detections)
            
            # Analyze scene
            analysis = self.model.analyze_scene(
                image=self.latest_image,
                detections=detections_list
            )
            
            # Publish analysis
            analysis_msg = String()
            analysis_msg.data = json.dumps(analysis, indent=2)
            self.analysis_pub.publish(analysis_msg)
            
            self.get_logger().info(
                f"Scene analyzed: {len(detections_list)} objects detected",
                throttle_duration_sec=5.0
            )
            
        except Exception as e:
            self.get_logger().error(f'Error analyzing scene: {e}')
    
    def _parse_detections(self, detections_msg: Optional[Detection2DArray]) -> list:
        """Convert Detection2DArray to list of dicts"""
        if detections_msg is None:
            return []
        
        detections = []
        for detection in detections_msg.detections:
            if len(detection.results) > 0:
                result = detection.results[0]
                detections.append({
                    'class_id': result.hypothesis.class_id,
                    'class_name': result.hypothesis.class_id,
                    'score': result.hypothesis.score,
                    'bbox': {
                        'x': detection.bbox.center.position.x,
                        'y': detection.bbox.center.position.y,
                        'width': detection.bbox.size_x,
                        'height': detection.bbox.size_y
                    }
                })
        
        return detections


def main(args=None):
    rclpy.init(args=args)
    node = SceneAnalyzerNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
