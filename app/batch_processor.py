from typing import List, Dict, Any
from PIL import Image
import os
from datetime import datetime
import json
from .image_ops import process_image
from .auth import get_current_active_user
from fastapi import Depends, HTTPException

class BatchProcessor:
    def __init__(self, output_dir: str = "static/images"):
        self.output_dir = output_dir

    def extract_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract metadata from an image file."""
        try:
            with Image.open(image_path) as img:
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "filename": os.path.basename(image_path),
                    "created_at": datetime.fromtimestamp(os.path.getctime(image_path)).isoformat(),
                    "modified_at": datetime.fromtimestamp(os.path.getmtime(image_path)).isoformat(),
                }
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        metadata["exif"] = {
                            "make": exif.get(271, "Unknown"),
                            "model": exif.get(272, "Unknown"),
                            "datetime": exif.get(36867, "Unknown"),
                            "exposure_time": exif.get(33434, "Unknown"),
                            "f_number": exif.get(33437, "Unknown"),
                            "iso": exif.get(34855, "Unknown"),
                        }
                
                return metadata
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error extracting metadata: {str(e)}")

    async def process_batch(
        self,
        image_ids: List[str],
        operation: str,
        params: Dict[str, Any],
        current_user: Any = Depends(get_current_active_user)
    ) -> List[Dict[str, Any]]:
        """Process multiple images with the same operation and parameters."""
        results = []
        for image_id in image_ids:
            try:
                # Process each image
                result = await process_image(image_id, operation, params)
                results.append({
                    "image_id": image_id,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "image_id": image_id,
                    "status": "error",
                    "error": str(e)
                })
        return results

    def convert_format(
        self,
        image_path: str,
        target_format: str,
        quality: int = 95
    ) -> str:
        """Convert image to a different format."""
        try:
            with Image.open(image_path) as img:
                # Create new filename with target format
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                new_path = os.path.join(self.output_dir, f"{base_name}.{target_format.lower()}")
                
                # Convert and save
                if target_format.upper() in ['JPEG', 'JPG']:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA'):
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    img.save(new_path, format=target_format.upper(), quality=quality)
                else:
                    img.save(new_path, format=target_format.upper())
                
                return new_path
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error converting image: {str(e)}")

    def save_metadata(self, image_id: str, metadata: Dict[str, Any]) -> str:
        """Save image metadata to a JSON file."""
        metadata_path = os.path.join(self.output_dir, f"{image_id}_metadata.json")
        try:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            return metadata_path
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error saving metadata: {str(e)}") 