#!/usr/bin/env python3
"""
Gemma-4-E2B Wrapper for ROS 2
Provides interface to Google's Gemma-4-E2B model for vision and language understanding
"""

import os
from typing import Optional, List, Dict, Any
import base64
import io
from PIL import Image
import numpy as np


class GemmaVisionModel:
    """Wrapper for Google Gemma-4-E2B vision-language model"""
    
    def __init__(self, model_name: str = "google/gemma-4-E2B", device: str = "cuda"):
        """
        Initialize Gemma model
        
        Args:
            model_name: Hugging Face model identifier
            device: Device to run model on ('cuda' or 'cpu')
        """
        self.model_name = model_name
        self.device = device
        self.model = None
        self.processor = None
        
        try:
            from transformers import AutoProcessor, AutoModelForVision2Seq
            import torch
            
            self.torch = torch
            self.AutoProcessor = AutoProcessor
            self.AutoModelForVision2Seq = AutoModelForVision2Seq
            
            # Load model and processor
            self._load_model()
            
        except ImportError as e:
            raise ImportError(
                f"Failed to import required libraries: {e}\n"
                "Please install: pip install transformers torch pillow"
            )
    
    def _load_model(self):
        """Load the model and processor"""
        print(f"Loading {self.model_name}...")
        
        self.processor = self.AutoProcessor.from_pretrained(
            self.model_name,
            trust_remote_code=True
        )
        
        self.model = self.AutoModelForVision2Seq.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            torch_dtype=self.torch.float16 if self.device == "cuda" else self.torch.float32,
            device_map=self.device if self.device == "cuda" else None
        )
        
        if self.device == "cpu":
            self.model = self.model.to("cpu")
        
        self.model.eval()
        print(f"Model loaded successfully on {self.device}")
    
    def generate_response(
        self,
        image: np.ndarray,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> str:
        """
        Generate text response based on image and prompt
        
        Args:
            image: Input image as numpy array (RGB)
            prompt: Text prompt/question
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            
        Returns:
            Generated text response
        """
        # Convert numpy array to PIL Image
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # Prepare inputs
        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        )
        
        # Move to device
        if self.device == "cuda":
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
        
        # Generate
        with self.torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True if temperature > 0 else False,
            )
        
        # Decode
        response = self.processor.decode(outputs[0], skip_special_tokens=True)
        
        # Remove the prompt from response if it's included
        if response.startswith(prompt):
            response = response[len(prompt):].strip()
        
        return response
    
    def analyze_scene(
        self,
        image: np.ndarray,
        detections: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Analyze scene for navigation
        
        Args:
            image: Input image
            detections: Optional list of detected objects from YOLOE
            
        Returns:
            Dictionary with scene analysis
        """
        # Build prompt based on detections
        if detections:
            objects_list = [d['class_name'] for d in detections]
            objects_str = ", ".join(set(objects_list))
            prompt = (
                f"Detected objects: {objects_str}\n\n"
                "Analyze this scene for robot navigation. Describe:\n"
                "1. Obstacles and their locations (left, right, center, distance)\n"
                "2. Navigable spaces and clear paths\n"
                "3. Recommended navigation direction\n"
                "4. Safety concerns\n"
                "Provide a concise analysis."
            )
        else:
            prompt = (
                "Analyze this scene for robot navigation. Describe:\n"
                "1. Obstacles and their locations\n"
                "2. Navigable spaces and clear paths\n"
                "3. Recommended navigation direction\n"
                "Provide a concise analysis."
            )
        
        response = self.generate_response(image, prompt)
        
        return {
            "analysis": response,
            "prompt": prompt,
            "detections_count": len(detections) if detections else 0
        }
    
    def generate_navigation_command(
        self,
        image: np.ndarray,
        goal: str,
        detections: Optional[List[Dict[str, Any]]] = None,
        current_state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate navigation command based on scene understanding
        
        Args:
            image: Current camera view
            goal: Navigation goal description
            detections: Object detections from YOLOE
            current_state: Current robot state description
            
        Returns:
            Navigation command dictionary
        """
        # Build comprehensive prompt
        prompt_parts = [f"Navigation goal: {goal}\n"]
        
        if detections:
            objects_list = [d['class_name'] for d in detections]
            prompt_parts.append(f"Detected objects: {', '.join(set(objects_list))}\n")
        
        if current_state:
            prompt_parts.append(f"Current state: {current_state}\n")
        
        prompt_parts.append(
            "\nProvide navigation command:\n"
            "- Direction: forward/backward/left/right/stop\n"
            "- Speed: slow/medium/fast\n"
            "- Reason: brief explanation\n"
            "- Warning: any safety concerns\n"
            "Format: DIRECTION|SPEED|REASON|WARNING"
        )
        
        prompt = "".join(prompt_parts)
        response = self.generate_response(image, prompt, temperature=0.3)
        
        # Parse response
        command = self._parse_navigation_command(response)
        command["raw_response"] = response
        command["prompt"] = prompt
        
        return command
    
    def _parse_navigation_command(self, response: str) -> Dict[str, Any]:
        """Parse navigation command from model response"""
        default_command = {
            "direction": "stop",
            "speed": "slow",
            "reason": "Unable to parse command",
            "warning": ""
        }
        
        try:
            # Try to parse structured format
            if "|" in response:
                parts = response.split("|")
                if len(parts) >= 3:
                    return {
                        "direction": parts[0].strip().lower(),
                        "speed": parts[1].strip().lower(),
                        "reason": parts[2].strip() if len(parts) > 2 else "",
                        "warning": parts[3].strip() if len(parts) > 3 else ""
                    }
            
            # Fallback: extract from natural language
            response_lower = response.lower()
            
            # Extract direction
            direction = "stop"
            for d in ["forward", "backward", "left", "right", "stop"]:
                if d in response_lower:
                    direction = d
                    break
            
            # Extract speed
            speed = "slow"
            for s in ["fast", "medium", "slow"]:
                if s in response_lower:
                    speed = s
                    break
            
            return {
                "direction": direction,
                "speed": speed,
                "reason": response[:100],  # First 100 chars as reason
                "warning": ""
            }
            
        except Exception:
            return default_command
    
    def ask_question(self, image: np.ndarray, question: str) -> str:
        """
        Ask a question about the image
        
        Args:
            image: Input image
            question: Question to ask
            
        Returns:
            Answer string
        """
        return self.generate_response(image, question)
