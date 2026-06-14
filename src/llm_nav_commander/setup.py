from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'llm_nav_commander'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=[
        'setuptools',
        'transformers>=4.30.0',
        'torch>=2.0.0',
        'pillow>=9.0.0',
        'numpy',
    ],
    zip_safe=True,
    maintainer='sivn',
    maintainer_email='user@todo.todo',
    description='ROS 2 navigation commander using Google Gemma-4-E2B LLM',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'llm_nav_commander_node = llm_nav_commander.llm_nav_commander_node:main',
            'scene_analyzer_node = llm_nav_commander.scene_analyzer_node:main',
        ],
    },
)
