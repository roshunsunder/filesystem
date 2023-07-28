from pathlib import Path
from typing import Dict, Any, Set
import requests
from .base import BaseFileProcessor

class ImageProcessor(BaseFileProcessor):
    """Processor for handling image files"""
    
    def __init__(self, hf_bearer_token: str):
        super().__init__()
        self.hf_bearer_token = hf_bearer_token
        self.supported_extensions: Set[str] = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
        self.api_url = "https://api-inference.huggingface.co/models/nlpconnect/vit-gpt2-image-captioning"
        
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self.supported_extensions
    
    def process(self, file_path: Path) -> Dict[str, Any]:
        """Process an image file using VIT-GPT2 for captioning"""
        try:
            # Generate caption using Hugging Face API
            headers = {"Authorization": f"Bearer {self.hf_bearer_token}"}
            with open(file_path, "rb") as f:
                data = f.read()
            
            response = requests.post(self.api_url, headers=headers, data=data)
            caption = response.json()[0]['generated_text']
            
            # Enhance caption for better searchability
            caption = f"A picture of {caption}"
            
            return {
                "content": caption,
                "file_type": "image",
                "image_type": file_path.suffix.lower()[1:],  # Remove the dot
                "metadata": {
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": file_path.stat().st_mtime,
                }
            }
        except Exception as e:
            self.logger.error(f"Error processing image file {file_path}: {str(e)}")
            raise 