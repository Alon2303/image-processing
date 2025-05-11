from PIL import Image, ImageOps, ImageEnhance
from io import BytesIO
import os
from typing import Dict, Any, Optional
from datetime import datetime

def resize_image(image_bytes, width, height):
    with Image.open(BytesIO(image_bytes)) as img:
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        # Perform the resize
        img = img.resize((int(width), int(height)), Image.Resampling.LANCZOS)
        
        # Save with original format
        output = BytesIO()
        save_format = img.format if img.format else 'JPEG'
        if save_format == 'JPEG':
            img.save(output, format=save_format, quality=95, optimize=True)
        else:
            img.save(output, format=save_format)
        return output.getvalue()

def rotate_image(image_bytes, angle):
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        output = BytesIO()
        if img.format == 'JPEG':
            img.save(output, format='JPEG', quality=95, optimize=True)
        elif img.format == 'PNG':
            img.save(output, format='PNG', optimize=True)
        else:
            img.save(output, format=img.format or 'JPEG', quality=95)
        return output.getvalue()

def grayscale_image(image_bytes):
    with Image.open(BytesIO(image_bytes)) as img:
        img = ImageOps.grayscale(img)
        output = BytesIO()
        if img.format == 'JPEG':
            img.save(output, format='JPEG', quality=95, optimize=True)
        elif img.format == 'PNG':
            img.save(output, format='PNG', optimize=True)
        else:
            img.save(output, format=img.format or 'JPEG', quality=95)
        return output.getvalue()

def crop_image(image_bytes, left, top, right, bottom):
    with Image.open(BytesIO(image_bytes)) as img:
        # Validate crop coordinates
        if left < 0 or top < 0 or right > img.width or bottom > img.height:
            raise ValueError(f"Crop coordinates out of bounds. Image size: {img.width}x{img.height}")
        if right <= left or bottom <= top:
            raise ValueError("Invalid crop coordinates: right must be greater than left, bottom must be greater than top")
        
        # Ensure coordinates are within image bounds
        left = max(0, min(left, img.width - 1))
        top = max(0, min(top, img.height - 1))
        right = max(left + 1, min(right, img.width))
        bottom = max(top + 1, min(bottom, img.height))
        
        # Perform the crop
        img = img.crop((left, top, right, bottom))
        
        # Save the cropped image
        output = BytesIO()
        if img.format == 'JPEG':
            img.save(output, format='JPEG', quality=95, optimize=True)
        elif img.format == 'PNG':
            img.save(output, format='PNG', optimize=True)
        else:
            img.save(output, format=img.format or 'JPEG', quality=95)
        return output.getvalue()

def adjust_brightness_contrast(image_bytes, brightness=1.0, contrast=1.0):
    with Image.open(BytesIO(image_bytes)) as img:
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        # Convert to RGB mode if not already
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Apply brightness adjustment
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(float(brightness))
        
        # Apply contrast adjustment
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(float(contrast))
        
        # Save with original format
        output = BytesIO()
        save_format = img.format if img.format else 'JPEG'
        if save_format == 'JPEG':
            img.save(output, format=save_format, quality=95, optimize=True)
        else:
            img.save(output, format=save_format)
        return output.getvalue()

def flip_image(image_bytes, direction):
    with Image.open(BytesIO(image_bytes)) as img:
        if direction == 'horizontal':
            img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        elif direction == 'vertical':
            img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        
        output = BytesIO()
        if img.format == 'JPEG':
            img.save(output, format='JPEG', quality=95, optimize=True)
        elif img.format == 'PNG':
            img.save(output, format='PNG', optimize=True)
        else:
            img.save(output, format=img.format or 'JPEG', quality=95)
        return output.getvalue()

def process_image(
    image_path: str,
    operation: str,
    params: Dict[str, Any],
    output_dir: str
) -> Dict[str, Any]:
    """
    Process an image with the specified operation and parameters.
    
    Args:
        image_path: Path to the input image
        operation: Name of the operation to perform
        params: Dictionary of parameters for the operation
        output_dir: Directory to save the processed image
    
    Returns:
        Dictionary containing the result information
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Apply the requested operation
            if operation == 'resize':
                width = int(params.get('width', img.width))
                height = int(params.get('height', img.height))
                img = img.resize((width, height), Image.Resampling.LANCZOS)
            
            elif operation == 'rotate':
                angle = float(params.get('angle', 0))
                img = img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
            
            elif operation == 'grayscale':
                img = img.convert('L').convert('RGB')
            
            elif operation == 'crop':
                left = int(params.get('left', 0))
                top = int(params.get('top', 0))
                right = int(params.get('right', img.width))
                bottom = int(params.get('bottom', img.height))
                img = img.crop((left, top, right, bottom))
            
            elif operation == 'brightness_contrast':
                brightness = float(params.get('brightness', 1.0))
                contrast = float(params.get('contrast', 1.0))
                
                if brightness != 1.0:
                    enhancer = ImageEnhance.Brightness(img)
                    img = enhancer.enhance(brightness)
                
                if contrast != 1.0:
                    enhancer = ImageEnhance.Contrast(img)
                    img = enhancer.enhance(contrast)
            
            elif operation == 'flip':
                direction = params.get('direction', 'horizontal')
                if direction == 'horizontal':
                    img = img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                else:  # vertical
                    img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

            # Generate output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{os.path.splitext(os.path.basename(image_path))[0]}_{operation}_{timestamp}.jpg"
            output_path = os.path.join(output_dir, filename)

            # Save the processed image
            img.save(output_path, 'JPEG', quality=95)

            return {
                'success': True,
                'output_path': output_path,
                'filename': filename,
                'operation': operation,
                'params': params
            }

    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'operation': operation,
            'params': params
        } 