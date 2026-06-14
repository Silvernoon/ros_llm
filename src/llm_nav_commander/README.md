# LLM Navigation Commander

ROS 2 package that integrates Google Gemma-4-E2B vision-language model for intelligent robot navigation. Works with YOLOE for object detection and Nav2 for path planning.

## Features

- **Vision-Language Understanding**: Uses Gemma-4-E2B for scene understanding
- **YOLOE Integration**: Processes object detections from YOLOE for enhanced awareness
- **Navigation Commands**: Generates high-level navigation commands based on visual input
- **Nav2 Compatible**: Can work alongside Nav2 stack for complete navigation solution
- **Scene Analysis**: Provides detailed scene descriptions and safety assessments

## Architecture

```
Camera --> YOLOE --> Detections --|
                                   |
Camera --> Image ----------------->|--> LLM Nav Commander --> cmd_vel
                                   |
Goal Description ----------------->|
Odometry ------------------------->|
```

## Nodes

### 1. llm_nav_commander_node

Main navigation commander that integrates vision, detections, and goals to generate navigation commands.

**Subscribed Topics:**
- `/camera/image_raw` (sensor_msgs/Image): Camera feed
- `/yoloe/detections` (vision_msgs/Detection2DArray): Object detections
- `/navigation_goal` (std_msgs/String): Text-based navigation goal
- `/odom` (nav_msgs/Odometry): Robot odometry

**Published Topics:**
- `/cmd_vel` (geometry_msgs/Twist): Velocity commands
- `/scene_analysis` (std_msgs/String): Scene analysis JSON
- `/nav_command` (std_msgs/String): Navigation command JSON

**Parameters:**
- `model_name`: Hugging Face model ID (default: "google/gemma-4-E2B")
- `device`: Device for inference (default: "cuda")
- `enable_auto_navigation`: Enable autonomous control (default: false)
- `update_rate`: Analysis rate in Hz (default: 2.0)
- Speed parameters for slow/medium/fast modes

### 2. scene_analyzer_node

Provides scene analysis without autonomous control. Useful for testing and understanding.

**Subscribed Topics:**
- `/camera/image_raw` (sensor_msgs/Image): Camera feed
- `/yoloe/detections` (vision_msgs/Detection2DArray): Object detections
- `/scene_query` (std_msgs/String): Custom questions about the scene

**Published Topics:**
- `/scene_analysis` (std_msgs/String): Periodic scene analysis
- `/scene_response` (std_msgs/String): Responses to queries

**Parameters:**
- `model_name`: Hugging Face model ID
- `device`: Device for inference
- `analysis_rate`: Analysis frequency (default: 1.0 Hz)
- `auto_analyze`: Enable periodic analysis (default: true)

## Installation

### Prerequisites

```bash
# ROS 2 Jazzy
sudo apt update
sudo apt install ros-jazzy-desktop

# Python dependencies
pip install transformers torch pillow accelerate
```

### Build

```bash
cd ~/Repos/ros_llm
colcon build --packages-select llm_nav_commander
source install/setup.bash
```

## Usage

### 1. Scene Analysis Mode (Testing)

Analyze scenes without controlling the robot:

```bash
ros2 launch llm_nav_commander scene_analyzer.launch.py
```

Ask questions about the scene:

```bash
ros2 topic pub /scene_query std_msgs/String "data: 'What obstacles do you see?'"
```

View analysis:

```bash
ros2 topic echo /scene_analysis
ros2 topic echo /scene_response
```

### 2. Navigation Commander Mode

With manual control (monitoring only):

```bash
ros2 launch llm_nav_commander llm_nav_commander.launch.py \
    enable_auto_navigation:=false
```

With autonomous control:

```bash
ros2 launch llm_nav_commander llm_nav_commander.launch.py \
    enable_auto_navigation:=true
```

Send navigation goals:

```bash
ros2 topic pub /navigation_goal std_msgs/String \
    "data: 'Navigate to the kitchen avoiding obstacles'"
```

### 3. Full System (with YOLOE)

Launch complete system with YOLOE:

```bash
# Terminal 1: YOLOE
cd ~/Repos/yoloe/ros2_ws
source install/setup.bash
ros2 launch yoloe_ros yoloe_prompt_free.launch.py

# Terminal 2: LLM Commander
cd ~/Repos/ros_llm
source install/setup.bash
ros2 launch llm_nav_commander llm_nav_commander.launch.py
```

Or use the combined launch file (when yoloe_ros is in the same workspace):

```bash
ros2 launch llm_nav_commander full_system.launch.py
```

### 4. With Camera

```bash
# USB camera
ros2 run usb_cam usb_cam_node_exe

# Realsense
ros2 launch realsense2_camera rs_launch.py

# Then launch commander
ros2 launch llm_nav_commander llm_nav_commander.launch.py \
    image_topic:=/camera/color/image_raw
```

## Configuration

Edit `config/default.yaml` to customize:

- Model selection
- Topic names
- Speed profiles
- Update rates
- Auto-navigation enable/disable

## Examples

### Send a Navigation Goal

```bash
ros2 topic pub /navigation_goal std_msgs/String \
    "data: 'Go forward slowly, avoid the chair on the left'"
```

### Monitor Commands

```bash
# See raw command JSON
ros2 topic echo /nav_command

# See scene analysis
ros2 topic echo /scene_analysis
```

### Interactive Scene Queries

```bash
# Ask about specific objects
ros2 topic pub /scene_query std_msgs/String \
    "data: 'Is there a clear path ahead?'"

# Ask about safety
ros2 topic pub /scene_query std_msgs/String \
    "data: 'What are the safety concerns in this scene?'"
```

## Integration with Nav2

This package can work alongside Nav2:

1. **High-level planner**: LLM Commander generates strategic goals
2. **Local obstacle avoidance**: Nav2 handles low-level control
3. **Hybrid mode**: LLM provides direction, Nav2 executes safely

Example integration:

```python
# LLM suggests: "Turn right to avoid obstacle"
# Nav2 executes the turn with proper collision avoidance
```

## Model Information

**Gemma-4-E2B** is Google's vision-language model that combines:
- Vision understanding
- Language generation
- Multi-modal reasoning

The model can:
- Describe scenes
- Answer questions about images
- Reason about spatial relationships
- Generate contextual instructions

## Topics Reference

| Topic | Type | Description |
|-------|------|-------------|
| `/camera/image_raw` | sensor_msgs/Image | Input camera feed |
| `/yoloe/detections` | vision_msgs/Detection2DArray | Object detections |
| `/navigation_goal` | std_msgs/String | Text goal description |
| `/odom` | nav_msgs/Odometry | Robot position/velocity |
| `/cmd_vel` | geometry_msgs/Twist | Velocity commands |
| `/scene_analysis` | std_msgs/String | Scene analysis (JSON) |
| `/nav_command` | std_msgs/String | Navigation command (JSON) |
| `/scene_query` | std_msgs/String | Questions about scene |
| `/scene_response` | std_msgs/String | Answers (JSON) |

## Command Format

Navigation commands are JSON with:

```json
{
  "direction": "forward|backward|left|right|stop",
  "speed": "slow|medium|fast",
  "reason": "Explanation of decision",
  "warning": "Safety concerns if any",
  "raw_response": "Full LLM response",
  "prompt": "Prompt sent to LLM"
}
```

## Troubleshooting

### Model not loading

```bash
# Check CUDA availability
python3 -c "import torch; print(torch.cuda.is_available())"

# Try CPU mode
ros2 launch llm_nav_commander llm_nav_commander.launch.py device:=cpu
```

### No detections from YOLOE

```bash
# Check YOLOE is running
ros2 topic list | grep yoloe

# Check topic connection
ros2 topic info /yoloe/detections
```

### Image not updating

```bash
# Check camera feed
ros2 topic hz /camera/image_raw
ros2 topic echo /camera/image_raw --no-arr
```

## Safety

⚠️ **Important Safety Notes:**

- Start with `enable_auto_navigation:=false` for testing
- Monitor `/nav_command` topic before enabling auto mode
- Adjust speed parameters conservatively
- Always have emergency stop available
- Test in safe, controlled environments first

## Performance

- **Update Rate**: 2 Hz recommended for real-time navigation
- **GPU Memory**: ~4-8 GB VRAM for Gemma-4-E2B
- **Latency**: ~500ms per inference on RTX 3060
- **CPU Mode**: Significantly slower, 2-5s per inference

## License

MIT

## Contributing

Contributions welcome! Areas for improvement:

- Integration with Nav2 action servers
- Multi-camera support
- Historical context tracking
- Fine-tuning for specific environments
- RViz visualization plugins

## References

- [Gemma Models](https://huggingface.co/google/gemma-4-E2B)
- [YOLOE](https://github.com/Q-Future/Q-Align/tree/main/yoloe)
- [ROS 2 Nav2](https://navigation.ros.org/)
- [Vision Messages](http://wiki.ros.org/vision_msgs)
