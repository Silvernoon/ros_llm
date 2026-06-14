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
            from transformers import AutoProcessor, AutoModelForMultimodalLM
            import torch

            self.torch = torch
            self.AutoProcessor = AutoProcessor
            self.AutoModelForMultimodalLM = AutoModelForMultimodalLM

            # Load model and processor
            self._load_model()

        except ImportError as e:
            raise ImportError(
                f"Failed to import required libraries: {e}\n"
                "Please install: pip install transformers torch pillow torchvision accelerate"
            )

    def _load_model(self):
        """Load the model and processor"""
        print(f"Loading {self.model_name}...")

        # Load processor
        self.processor = self.AutoProcessor.from_pretrained(self.model_name)

        # Load model with proper dtype and device mapping
        self.model = self.AutoModelForMultimodalLM.from_pretrained(
            self.model_name,
            dtype="auto",
            device_map="auto" if self.device == "cuda" else None,
        )

        if self.device == "cpu":
            self.model = self.model.to("cpu")

        self.model.eval()
        print(f"Model loaded successfully on {self.device}")

    def generate_response(
        self,
        image: Optional[np.ndarray],
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 1.0,
        top_p: float = 0.95,
        top_k: int = 64,
        enable_thinking: bool = False,
    ) -> str:
        """
        Generate text response based on image and prompt

        Args:
            image: Input image as numpy array (RGB), or None for text-only mode
            prompt: Text prompt/question
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature (default 1.0 as per best practices)
            top_p: Nucleus sampling parameter (default 0.95 as per best practices)
            top_k: Top-k sampling (default 64 as per best practices)
            enable_thinking: Enable reasoning mode

        Returns:
            Generated text response
        """
        # Build message content. Image is optional so the model can be tested
        # with text-only input (no camera feed required).
        text_only = image is None
        content: List[Dict[str, Any]] = []
        if not text_only:
            # Convert numpy array to PIL Image
            if isinstance(image, np.ndarray):
                pil_image = Image.fromarray(image)
            else:
                pil_image = image
            # Image should come before text as per best practices
            content.append({"type": "image", "image": pil_image})
        content.append({"type": "text", "text": prompt})

        # Prepare messages in the format expected by Gemma 4
        messages = [
            {
                "role": "user",
                "content": content,
            }
        ]

        # The multimodal processor has no chat template for text-only input,
        # so fall back to the underlying tokenizer in that case.
        if text_only:
            tokenizer = getattr(self.processor, "tokenizer", None)
            if tokenizer is None:
                raise RuntimeError(
                    "Text-only inference requires a tokenizer, but the processor "
                    "does not expose one."
                )
            text_messages = [{"role": "user", "content": prompt}]
            inputs = tokenizer.apply_chat_template(
                text_messages,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
                add_generation_prompt=True,
            )
        else:
            # Process input using chat template
            inputs = self.processor.apply_chat_template(
                messages,
                tokenize=True,
                return_dict=True,
                return_tensors="pt",
                add_generation_prompt=True,
                enable_thinking=enable_thinking,
            )

        # Move to device
        inputs = inputs.to(self.model.device)
        input_len = inputs["input_ids"].shape[-1]

        # Generate
        with self.torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                do_sample=True,
            )

        # Decode. Text-only uses the tokenizer; multimodal uses the processor.
        if text_only:
            response = self.processor.tokenizer.decode(
                outputs[0][input_len:], skip_special_tokens=True
            )
            return response.strip()

        response = self.processor.decode(
            outputs[0][input_len:], skip_special_tokens=False
        )

        # Parse response to extract final answer
        parsed = self.processor.parse_response(response)

        return parsed

    def analyze_scene(
        self, image: np.ndarray, detections: Optional[List[Dict[str, Any]]] = None
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
            objects_list = [d["class_name"] for d in detections]
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
            "detections_count": len(detections) if detections else 0,
        }

    def generate_navigation_command(
        self,
        image: np.ndarray,
        goal: str,
        detections: Optional[List[Dict[str, Any]]] = None,
        current_state: Optional[str] = None,
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
            objects_list = [d["class_name"] for d in detections]
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
        response = self.generate_response(image, prompt, temperature=1.0)

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
            "warning": "",
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
                        "warning": parts[3].strip() if len(parts) > 3 else "",
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
                "warning": "",
            }

        except Exception:
            return default_command

    def ask_question(self, image: Optional[np.ndarray], question: str) -> str:
        """
        Ask a question about the image

        Args:
            image: Input image, or None for text-only questions
            question: Question to ask

        Returns:
            Answer string
        """
        return self.generate_response(image, question)
