import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Complete system launch: YOLOE + LLM Navigation Commander
    """
    
    # Arguments
    device_arg = DeclareLaunchArgument(
        'device',
        default_value='cuda',
        description='Device for inference (cuda/cpu)'
    )
    
    image_topic_arg = DeclareLaunchArgument(
        'image_topic',
        default_value='/camera/image_raw',
        description='Camera image topic'
    )
    
    enable_auto_nav_arg = DeclareLaunchArgument(
        'enable_auto_navigation',
        default_value='false',
        description='Enable autonomous navigation'
    )
    
    # YOLOE Node (assuming yoloe_ros is available)
    # Uncomment when yoloe_ros package is in workspace
    # yoloe_launch = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource([
    #         PathJoinSubstitution([
    #             FindPackageShare('yoloe_ros'),
    #             'launch',
    #             'yoloe_prompt_free.launch.py'
    #         ])
    #     ]),
    #     launch_arguments={
    #         'device': LaunchConfiguration('device'),
    #         'image_topic': LaunchConfiguration('image_topic'),
    #     }.items()
    # )
    
    # LLM Commander Launch
    llm_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('llm_nav_commander'),
                'launch',
                'llm_nav_commander.launch.py'
            ])
        ]),
        launch_arguments={
            'device': LaunchConfiguration('device'),
            'image_topic': LaunchConfiguration('image_topic'),
            'enable_auto_navigation': LaunchConfiguration('enable_auto_navigation'),
        }.items()
    )
    
    return LaunchDescription([
        device_arg,
        image_topic_arg,
        enable_auto_nav_arg,
        # yoloe_launch,  # Uncomment when yoloe_ros is available
        llm_launch,
    ])
