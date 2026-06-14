# ROS LLM Workspace

基于Google Gemma-4-E2B的ROS 2导航指挥系统，集成YOLOE目标检测用于智能机器人导航。

## 概述

这个工作空间包含ROS 2包，将大语言模型（LLM）用于机器人导航决策。系统接收来自相机的图像和YOLOE的目标检测结果，使用Gemma-4-E2B生成自然语言导航指令和控制命令。

## 特性

- 🤖 **视觉-语言理解**: 使用Gemma-4-E2B理解场景
- 👁️ **YOLOE集成**: 处理目标检测结果增强感知
- 🧭 **导航指挥**: 基于视觉输入生成高级导航命令
- 🔗 **Nav2兼容**: 可与Nav2协同工作
- 🔍 **场景分析**: 提供详细的场景描述和安全评估

## 系统架构

```
相机 --> YOLOE --> 检测结果 --|
                               |
相机 --> 图像 ----------------->|--> LLM导航指挥器 --> cmd_vel
                               |
目标描述 --------------------->|
里程计 ----------------------->|
```

## 包含的包

### llm_nav_commander

主要的ROS 2包，提供两个节点：

1. **llm_nav_commander_node**: 完整的导航指挥器，可生成速度命令
2. **scene_analyzer_node**: 场景分析节点，用于测试和理解

## 快速开始

### 1. 安装依赖

```bash
# ROS 2 Jazzy
sudo apt update
sudo apt install ros-jazzy-desktop ros-jazzy-cv-bridge ros-jazzy-vision-msgs

# Python依赖
pip install transformers torch pillow accelerate
```

### 2. 构建工作空间

```bash
cd ros_llm
colcon build
source install/setup.bash
```

### 3. 测试安装

```bash
python3 src/llm_nav_commander/scripts/test_installation.py
```

### 4. 运行场景分析器（测试模式）

```bash
ros2 launch llm_nav_commander scene_analyzer.launch.py
```

### 5. 查看分析结果

```bash
# 终端1：查看场景分析
ros2 topic echo /scene_analysis

# 终端2：发送问题
ros2 topic pub /scene_query std_msgs/String "data: '前方有什么障碍物？'"
```

### 6. 运行导航指挥器

```bash
# 仅监控模式（不发送速度命令）
ros2 launch llm_nav_commander llm_nav_commander.launch.py \
    enable_auto_navigation:=false

# 自主导航模式（发送速度命令）
ros2 launch llm_nav_commander llm_nav_commander.launch.py \
    enable_auto_navigation:=true
```

### 7. 发送导航目标

```bash
ros2 topic pub /navigation_goal std_msgs/String \
    "data: '慢速向前移动，避开左边的椅子'"
```

## 与YOLOE集成

### 方式1：分别启动

```bash
# 终端1：启动YOLOE
cd yoloe/ros2_ws
source install/setup.bash
ros2 launch yoloe_ros yoloe_prompt_free.launch.py

# 终端2：启动LLM指挥器
cd ros_llm
source install/setup.bash
ros2 launch llm_nav_commander llm_nav_commander.launch.py
```

### 方式2：完整系统启动

```bash
ros2 launch llm_nav_commander full_system.launch.py \
    device:=cuda \
    enable_auto_navigation:=false
```

## 与Nav2集成

这个包可以与Nav2协同工作：

1. **LLM指挥器**: 提供战略级别的导航决策
2. **Nav2**: 处理路径规划和局部避障
3. **混合模式**: LLM提供方向，Nav2安全执行

## 主题说明

| 主题 | 类型 | 说明 |
|------|------|------|
| `/camera/image_raw` | sensor_msgs/Image | 输入相机图像 |
| `/yoloe/detections` | vision_msgs/Detection2DArray | 目标检测结果 |
| `/navigation_goal` | std_msgs/String | 文本形式的导航目标 |
| `/odom` | nav_msgs/Odometry | 机器人位置/速度 |
| `/cmd_vel` | geometry_msgs/Twist | 速度命令输出 |
| `/scene_analysis` | std_msgs/String | 场景分析（JSON格式） |
| `/nav_command` | std_msgs/String | 导航命令（JSON格式） |
| `/scene_query` | std_msgs/String | 关于场景的问题 |
| `/scene_response` | std_msgs/String | 回答（JSON格式） |

## 配置

编辑 `src/llm_nav_commander/config/default.yaml` 来自定义：

- 模型选择
- 主题名称
- 速度配置
- 更新频率
- 自主导航开关

## 使用示例

### 场景查询

```bash
# 询问清晰路径
ros2 topic pub /scene_query std_msgs/String \
    "data: '前方的路径是否畅通？'"

# 询问安全问题
ros2 topic pub /scene_query std_msgs/String \
    "data: '这个场景中有什么安全隐患？'"

# 询问特定物体
ros2 topic pub /scene_query std_msgs/String \
    "data: '你看到桌子了吗？它在哪里？'"
```

### 发送导航目标

```bash
# 基本前进
ros2 topic pub /navigation_goal std_msgs/String \
    "data: '向前移动'"

# 复杂任务
ros2 topic pub /navigation_goal std_msgs/String \
    "data: '找到通往厨房的路径，避开所有障碍物'"

# 带安全约束
ros2 topic pub /navigation_goal std_msgs/String \
    "data: '慢速右转，注意不要碰到墙壁'"
```

### 监控命令

```bash
# 查看原始命令
ros2 topic echo /nav_command

# 查看场景分析
ros2 topic echo /scene_analysis

# 监控速度输出
ros2 topic echo /cmd_vel
```

## 性能

- **更新频率**: 实时导航推荐2 Hz
- **GPU内存**: Gemma-4-E2B需要约4-8 GB显存
- **延迟**: RTX 3060上约500ms每次推理
- **CPU模式**: 显著较慢，2-5秒每次推理

## 安全注意事项

⚠️ **重要安全提示：**

- 首次使用时设置 `enable_auto_navigation:=false` 进行测试
- 启用自主模式前监控 `/nav_command` 主题
- 保守调整速度参数
- 始终准备好紧急停止
- 在安全可控的环境中进行测试

## 故障排除

### 模型加载失败

```bash
# 检查CUDA可用性
python3 -c "import torch; print(torch.cuda.is_available())"

# 尝试CPU模式
ros2 launch llm_nav_commander llm_nav_commander.launch.py device:=cpu
```

### YOLOE无检测结果

```bash
# 检查YOLOE是否运行
ros2 topic list | grep yoloe

# 检查主题连接
ros2 topic info /yoloe/detections
```

### 图像未更新

```bash
# 检查相机feed
ros2 topic hz /camera/image_raw
ros2 topic echo /camera/image_raw --no-arr
```

## 开发

### 添加自定义提示

编辑 `llm_nav_commander/gemma_model.py` 中的提示模板。

### 调整速度配置

修改 `config/default.yaml` 中的速度参数。

### 扩展功能

可以添加的功能：
- 与Nav2 action服务器集成
- 多相机支持
- 历史上下文跟踪
- 特定环境微调
- RViz可视化插件

## 目录结构

```
ros_llm/
├── src/
│   └── llm_nav_commander/
│       ├── llm_nav_commander/
│       │   ├── __init__.py
│       │   ├── gemma_model.py              # Gemma模型封装
│       │   ├── llm_nav_commander_node.py    # 主导航节点
│       │   └── scene_analyzer_node.py       # 场景分析节点
│       ├── launch/
│       │   ├── llm_nav_commander.launch.py
│       │   ├── scene_analyzer.launch.py
│       │   └── full_system.launch.py
│       ├── config/
│       │   └── default.yaml
│       ├── scripts/
│       │   ├── send_goal.py
│       │   └── test_installation.py
│       ├── package.xml
│       ├── setup.py
│       ├── setup.cfg
│       └── README.md
└── README.md                                # 本文件
```

## 相关项目

- [YOLOE](https://github.com/ultralytics/yoloe) - 开放词汇目标检测
- [Nav2](https://navigation.ros.org/) - ROS 2导航框架
- [Gemma](https://huggingface.co/google/gemma-4-E2B) - Google视觉-语言模型

## 支持

遇到问题？
1. 运行测试脚本：`python3 scripts/test_installation.py`
2. 检查ROS 2日志：`ros2 topic list`, `ros2 node info`
3. 查看README中的故障排除部分
