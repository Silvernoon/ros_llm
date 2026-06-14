import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Launch Scene Analyzer - for testing and scene understanding"""
    
    # Declare arguments
    model_name_arg = DeclareLaunchArgument(
        'model_name',
        default_value='google/gemma-4-E2B',
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
    
    analysis_rate_arg = DeclareLaunchArgument(
        'analysis_rate',
        default_value='1.0',
        description='Analysis rate in Hz'
    )
    
    auto_analyze_arg = DeclareLaunchArgument(
        'auto_analyze',
        default_value='true',
        description='Automatically analyze scene periodically'
    )
    
    # Scene Analyzer Node
    scene_analyzer_node = Node(
        package='llm_nav_commander',
        executable='scene_analyzer_node',
        name='scene_analyzer',
        output='screen',
        parameters=[{
            'model_name': LaunchConfiguration('model_name'),
            'device': LaunchConfiguration('device'),
            'image_topic': LaunchConfiguration('image_topic'),
            'detections_topic': LaunchConfiguration('detections_topic'),
            'analysis_rate': LaunchConfiguration('analysis_rate'),
            'auto_analyze': LaunchConfiguration('auto_analyze'),
            'analysis_topic': '/scene_analysis',
            'query_topic': '/scene_query',
            'response_topic': '/scene_response',
        }]
    )
    
    return LaunchDescription([
        model_name_arg,
        device_arg,
        image_topic_arg,
        detections_topic_arg,
        analysis_rate_arg,
        auto_analyze_arg,
        scene_analyzer_node,
    ])
