#!/usr/bin/env python3
"""
Test installation script for LLM Nav Commander
Verifies all dependencies are available
"""

import sys


def test_ros2():
    """Test ROS 2 imports"""
    try:
        import rclpy
        from sensor_msgs.msg import Image
        from vision_msgs.msg import Detection2DArray
        from geometry_msgs.msg import Twist
        from std_msgs.msg import String
        print("✓ ROS 2 dependencies OK")
        return True
    except ImportError as e:
        print(f"✗ ROS 2 import failed: {e}")
        return False


def test_cv():
    """Test OpenCV and CV Bridge"""
    try:
        import cv2
        from cv_bridge import CvBridge
        print("✓ OpenCV and CV Bridge OK")
        return True
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False


def test_ml():
    """Test ML dependencies"""
    try:
        import torch
        import transformers
        from PIL import Image
        print(f"✓ PyTorch {torch.__version__} OK")
        print(f"✓ Transformers {transformers.__version__} OK")
        
        if torch.cuda.is_available():
            print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
        else:
            print("⚠ CUDA not available, will use CPU")
        
        return True
    except ImportError as e:
        print(f"✗ ML library import failed: {e}")
        return False


def test_package():
    """Test package imports"""
    try:
        from llm_nav_commander.gemma_model import GemmaVisionModel
        print("✓ Package imports OK")
        return True
    except ImportError as e:
        print(f"✗ Package import failed: {e}")
        print("  Make sure to source the workspace: source install/setup.bash")
        return False


def main():
    print("Testing LLM Nav Commander Installation")
    print("=" * 50)
    
    results = {
        "ROS 2": test_ros2(),
        "OpenCV": test_cv(),
        "ML Libraries": test_ml(),
        "Package": test_package(),
    }
    
    print("\n" + "=" * 50)
    print("Summary:")
    for name, status in results.items():
        status_str = "✓ PASS" if status else "✗ FAIL"
        print(f"  {name}: {status_str}")
    
    if all(results.values()):
        print("\n✓ All tests passed! Ready to use.")
        return 0
    else:
        print("\n✗ Some tests failed. Please install missing dependencies.")
        print("\nInstallation commands:")
        print("  pip install transformers torch pillow accelerate")
        print("  sudo apt install ros-jazzy-cv-bridge ros-jazzy-vision-msgs")
        return 1


if __name__ == '__main__':
    sys.exit(main())
