import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Launch LLM Navigation Commander with YOLOE integration"""
    
    # Declare arguments
    model_name_arg = DeclareLaunchArgument(
        'model_name',
        default_value='google/gemma-4-E2B-it',
        description='Hugging Face model name'
    )
    
    device_arg = DeclareLaunchArgument(
        'device',
        default_value='cuda',
        description='Device to run model on (cuda/cpu)'
    )
    
    image_topic_arg = DeclareLaunchArgument(
        'image_topic',
        default_value='/camera/image_raw',
        description='Image topic to subscribe to'
    )
    
    detections_topic_arg = DeclareLaunchArgument(
        'detections_topic',
        default_value='/yoloe/detections',
        description='YOLOE detections topic'
    )
    
    enable_auto_nav_arg = DeclareLaunchArgument(
        'enable_auto_navigation',
        default_value='false',
        description='Enable autonomous navigation (true/false)'
    )
    
    update_rate_arg = DeclareLaunchArgument(
        'update_rate',
        default_value='2.0',
        description='Update rate in Hz'
    )
    
    # LLM Navigation Commander Node
    llm_nav_commander_node = Node(
        package='llm_nav_commander',
        executable='llm_nav_commander_node',
        name='llm_nav_commander',
        output='screen',
        parameters=[{
            'model_name': LaunchConfiguration('model_name'),
            'device': LaunchConfiguration('device'),
            'image_topic': LaunchConfiguration('image_topic'),
            'detections_topic': LaunchConfiguration('detections_topic'),
            'enable_auto_navigation': LaunchConfiguration('enable_auto_navigation'),
            'update_rate': LaunchConfiguration('update_rate'),
            'cmd_vel_topic': '/cmd_vel',
            'odom_topic': '/odom',
            'goal_topic': '/navigation_goal',
            'analysis_topic': '/scene_analysis',
            'command_topic': '/nav_command',
            'linear_speed_slow': 0.2,
            'linear_speed_medium': 0.4,
            'linear_speed_fast': 0.6,
            'angular_speed_slow': 0.3,
            'angular_speed_medium': 0.6,
            'angular_speed_fast': 0.9,
        }]
    )
    
    return LaunchDescription([
        model_name_arg,
        device_arg,
        image_topic_arg,
        detections_topic_arg,
        enable_auto_nav_arg,
        update_rate_arg,
        llm_nav_commander_node,
    ])
