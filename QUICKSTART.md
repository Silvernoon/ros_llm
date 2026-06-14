# Quick Start Guide

## 快速开始指南

### 1. 安装和构建

```bash
# 克隆或进入工作空间
cd ros_llm

# 安装依赖
./setup.sh

# 或手动安装
pip3 install -r requirements.txt
colcon build
source install/setup.bash
```

### 2. 测试安装

```bash
python3 src/llm_nav_commander/scripts/test_installation.py
```

### 3. 基础使用

#### 场景1：仅测试场景分析（推荐首次使用）

```bash
# 终端1：启动场景分析器
ros2 launch llm_nav_commander scene_analyzer.launch.py

# 终端2：查看分析结果
ros2 topic echo /scene_analysis

# 终端3：提问
ros2 topic pub /scene_query std_msgs/String "data: '你看到了什么？'"
```

#### 场景2：监控模式（不控制机器人）

```bash
# 终端1：启动指挥器（监控模式）
ros2 launch llm_nav_commander llm_nav_commander.launch.py \
    enable_auto_navigation:=false

# 终端2：发送目标
ros2 topic pub /navigation_goal std_msgs/String "data: '向前移动'"

# 终端3：查看命令
ros2 topic echo /nav_command
```

#### 场景3：完整系统 + YOLOE

```bash
# 终端1：启动YOLOE
cd ros2_ws
source install/setup.bash
ros2 launch yoloe_ros yoloe_prompt_free.launch.py

# 终端2：启动相机（如果需要）
ros2 run usb_cam usb_cam_node_exe

# 终端3：启动LLM指挥器
cd ros_llm
source install/setup.bash
ros2 launch llm_nav_commander llm_nav_commander.launch.py \
    image_topic:=/camera/image_raw \
    detections_topic:=/yoloe/detections

# 终端4：监控
python3 src/llm_nav_commander/scripts/monitor.py
```

#### 场景4：交互式演示

```bash
# 终端1：启动系统
ros2 launch llm_nav_commander llm_nav_commander.launch.py

# 终端2：交互式控制
python3 src/llm_nav_commander/scripts/interactive_demo.py
```

### 4. 常用命令

#### 发送导航目标

```bash
# 简单前进
ros2 topic pub /navigation_goal std_msgs/String "data: '前进'"

# 复杂任务
ros2 topic pub /navigation_goal std_msgs/String \
    "data: '慢速向前，避开左边的障碍物'"
```

#### 场景查询

```bash
# 询问障碍物
ros2 topic pub /scene_query std_msgs/String "data: '前方有障碍物吗？'"

# 询问路径
ros2 topic pub /scene_query std_msgs/String "data: '哪个方向可以通行？'"
```

#### 查看状态

```bash
# 查看所有话题
ros2 topic list

# 查看命令输出
ros2 topic echo /nav_command

# 查看场景分析
ros2 topic echo /scene_analysis

# 查看速度命令（自主模式）
ros2 topic echo /cmd_vel
```

### 5. 参数调整

编辑配置文件：

```bash
nano src/llm_nav_commander/config/default.yaml
```

关键参数：
- `device`: "cuda" 或 "cpu"
- `enable_auto_navigation`: true（自主）或 false（监控）
- `update_rate`: 更新频率（Hz）
- 速度参数：`linear_speed_*`, `angular_speed_*`

### 6. 故障排除

#### CUDA不可用

```bash
# 测试CUDA
python3 -c "import torch; print(torch.cuda.is_available())"

# 使用CPU
ros2 launch llm_nav_commander scene_analyzer.launch.py device:=cpu
```

#### 模型下载失败

```bash
# 设置HuggingFace镜像（中国）
export HF_ENDPOINT=https://hf-mirror.com

# 手动下载模型
huggingface-cli download google/gemma-4-E2B
```

#### 没有相机图像

```bash
# 检查话题
ros2 topic list | grep image

# 检查相机
ros2 topic hz /camera/image_raw

# 使用测试图像（如果有）
ros2 run image_publisher image_publisher_node test_image.jpg
```

### 7. 安全提示

⚠️ **重要**：
1. 首次使用时设置 `enable_auto_navigation:=false`
2. 在安全环境中测试
3. 准备紧急停止按钮
4. 监控 `/cmd_vel` 输出
5. 从低速开始调试

### 8. 性能优化

- **GPU**: 推荐RTX 3060或更好
- **更新率**: 2 Hz适合实时导航
- **图像分辨率**: 640x480足够（减少处理时间）
- **批处理**: 禁用（实时性优先）

### 9. 下一步

- 阅读完整 README: `cat README.md`
- 查看包文档: `cat src/llm_nav_commander/README.md`
- 集成Nav2进行完整导航
- 自定义提示和行为
- 记录和回放会话

### 10. 获取帮助

```bash
# 查看节点信息
ros2 node info /llm_nav_commander

# 查看参数
ros2 param list /llm_nav_commander

# 查看服务
ros2 service list
```

## 典型工作流程

### 开发和测试

```bash
# 1. 启动场景分析器
ros2 launch llm_nav_commander scene_analyzer.launch.py

# 2. 测试查询
python3 src/llm_nav_commander/scripts/interactive_demo.py

# 3. 调整提示和参数
# 编辑 llm_nav_commander/gemma_model.py

# 4. 重新构建
colcon build --packages-select llm_nav_commander
```

### 实际部署

```bash
# 1. 启动完整系统
ros2 launch llm_nav_commander full_system.launch.py

# 2. 启动监控
python3 src/llm_nav_commander/scripts/monitor.py

# 3. 发送任务
ros2 topic pub /navigation_goal std_msgs/String "data: '导航到目标位置'"

# 4. 观察和调整
```
