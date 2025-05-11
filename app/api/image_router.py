from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Path, Depends, Form
from fastapi.responses import JSONResponse
from uuid import UUID
from .. import storage, image_ops
from ..models import ImageUploadResponse, ImageMetadata, ImageVersion
from io import BytesIO
from typing import List, Optional
from ..auth import Token, User, authenticate_user, create_access_token, get_current_active_user, fake_users_db, ACCESS_TOKEN_EXPIRE_MINUTES, timedelta
from ..batch_processor import BatchProcessor
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
import os

router = APIRouter(
    prefix="/images",
    tags=["images"],
    responses={404: {"description": "Image not found"}},
)

batch_processor = BatchProcessor()

@router.post("/upload", 
    response_model=ImageUploadResponse,
    summary="Upload a new image",
    description="Upload an image file to the server. The image will be stored and a unique ID will be generated.",
    responses={
        200: {
            "description": "Image uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "image_id": "123e4567-e89b-12d3-a456-426614174000",
                        "filename": "example.jpg",
                        "url": "/static/123e4567-e89b-12d3-a456-426614174000_example.jpg"
                    }
                }
            }
        }
    }
)
def upload_image(file: UploadFile = File(..., description="The image file to upload")):
    """
    Upload a new image to the server.
    
    - **file**: The image file to upload (supported formats: JPEG, PNG)
    
    Returns:
    - **image_id**: Unique identifier for the uploaded image
    - **filename**: Original filename
    - **url**: URL to access the uploaded image
    """
    image_id, version = storage.save_image(file)
    return ImageUploadResponse(image_id=image_id, filename=version['filename'], url=version['url'])

@router.get("/gallery", 
    response_model=List[ImageMetadata],
    summary="List all images",
    description="Retrieve a list of all uploaded images with their metadata and version history."
)
def list_images():
    """
    Get a list of all uploaded images.
    
    Returns:
    - List of image metadata including:
        - image_id
        - filename
        - versions (list of all versions)
        - created_at timestamp
    """
    metadata = storage._load_metadata()
    images = []
    for image_id, image_data in metadata.items():
        versions = storage.get_image_versions(image_id)
        images.append({
            "image_id": image_id,
            "filename": image_data["filename"],
            "versions": versions,
            "created_at": image_data["created_at"]
        })
    return images

@router.post("/process/{image_id}", 
    response_model=ImageVersion,
    summary="Process an image",
    description="Apply various transformations to an image. Creates a new version of the image.",
    responses={
        200: {"description": "Image processed successfully"},
        400: {"description": "Invalid operation or parameters"},
        404: {"description": "Image not found"}
    }
)
def process_image(
    image_id: str = Path(..., description="ID of the image to process"),
    operation: str = Query(
        ..., 
        enum=["resize", "rotate", "grayscale", "crop", "brightness_contrast", "flip"],
        description="Type of operation to perform"
    ),
    width: Optional[int] = Query(None, description="Width for resize operation"),
    height: Optional[int] = Query(None, description="Height for resize operation"),
    angle: Optional[float] = Query(None, description="Angle for rotate operation"),
    left: Optional[int] = Query(None, description="Left coordinate for crop operation"),
    top: Optional[int] = Query(None, description="Top coordinate for crop operation"),
    right: Optional[int] = Query(None, description="Right coordinate for crop operation"),
    bottom: Optional[int] = Query(None, description="Bottom coordinate for crop operation"),
    brightness: float = Query(1.0, description="Brightness adjustment factor (0.0 to 2.0)"),
    contrast: float = Query(1.0, description="Contrast adjustment factor (0.0 to 2.0)"),
    direction: str = Query(None, enum=["horizontal", "vertical"], description="Direction for flip operation"),
    version_id: str = Query(None, description="ID of the version to process")
):
    """
    Process an image with various transformations.
    """
    versions = storage.get_image_versions(image_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # If version_id is provided, use that version, otherwise use the latest
    if version_id:
        version_to_use = next((v for v in versions if v['version_id'] == version_id), None)
        if not version_to_use:
            raise HTTPException(status_code=404, detail="Version not found")
    else:
        version_to_use = versions[-1]  # Get the latest version
    
    # Use correct file path
    filepath = os.path.join(storage.STATIC_DIR, version_to_use['filename'])
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Image file not found")

    with open(filepath, 'rb') as f:
        image_bytes = f.read()

    processed = None
    transformation = None

    try:
        if operation == "resize":
            if not width or not height or width <= 0 or height <= 0:
                raise HTTPException(status_code=400, detail="Width and height must be positive")
            processed = image_ops.resize_image(image_bytes, width, height)
            transformation = f"Resized to {width}x{height}"

        elif operation == "rotate":
            if angle is None:
                raise HTTPException(status_code=400, detail="Angle is required for rotate operation")
            processed = image_ops.rotate_image(image_bytes, angle)
            transformation = f"Rotated by {angle} degrees"

        elif operation == "grayscale":
            processed = image_ops.grayscale_image(image_bytes)
            transformation = "Grayscale"

        elif operation == "crop":
            if any(x is None for x in [left, top, right, bottom]):
                raise HTTPException(status_code=400, detail="All crop coordinates are required")
            if left < 0 or top < 0 or right <= left or bottom <= top:
                raise HTTPException(status_code=400, detail="Invalid crop coordinates")
            processed = image_ops.crop_image(image_bytes, left, top, right, bottom)
            transformation = f"Cropped to coordinates ({left}, {top}, {right}, {bottom})"

        elif operation == "brightness_contrast":
            if brightness < 0 or contrast < 0:
                raise HTTPException(status_code=400, detail="Brightness and contrast must be positive")
            processed = image_ops.adjust_brightness_contrast(image_bytes, brightness, contrast)
            transformation = f"Adjusted brightness ({brightness}) and contrast ({contrast})"

        elif operation == "flip":
            if not direction or direction not in ["horizontal", "vertical"]:
                raise HTTPException(status_code=400, detail="Valid direction (horizontal/vertical) is required for flip operation")
            processed = image_ops.flip_image(image_bytes, direction)
            transformation = f"Flipped {direction}"

        else:
            raise HTTPException(status_code=400, detail="Invalid operation")

        if processed is None:
            raise HTTPException(status_code=500, detail="Image processing failed")

        # Save the processed image as a new version
        new_version = storage.save_version(image_id, processed, transformation)
        return new_version

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{image_id}/versions", 
    response_model=List[ImageVersion],
    summary="Get image version history",
    description="Retrieve the version history of a specific image.",
    responses={
        200: {"description": "List of image versions"},
        404: {"description": "Image not found"}
    }
)
def get_versions(image_id: str = Path(..., description="ID of the image")):
    """
    Get the version history of an image.
    
    Parameters:
    - **image_id**: ID of the image
    
    Returns:
    - List of version metadata including:
        - version_id
        - image_id
        - filename
        - url
        - transformation details
        - created_at timestamp
    """
    return storage.get_image_versions(image_id)

@router.post("/{image_id}/revert/{version_id}", 
    summary="Revert to previous version",
    description="Revert an image to a specific previous version.",
    responses={
        200: {"description": "Successfully reverted to version"},
        404: {"description": "Image or version not found"}
    }
)
def revert_version(
    image_id: str = Path(..., description="ID of the image"),
    version_id: str = Path(..., description="ID of the version to revert to")
):
    """
    Revert an image to a specific previous version.
    
    Parameters:
    - **image_id**: ID of the image
    - **version_id**: ID of the version to revert to
    
    Returns:
    - Success status
    """
    ok = storage.revert_to_version(image_id, version_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"success": True}

@router.delete("/{image_id}", 
    summary="Delete an image",
    description="Delete an image and all its versions.",
    responses={
        200: {"description": "Image deleted successfully"},
        404: {"description": "Image not found"}
    }
)
def delete_image(image_id: str = Path(..., description="ID of the image to delete")):
    """
    Delete an image and all its versions.
    
    Parameters:
    - **image_id**: ID of the image to delete
    
    Returns:
    - Success status
    """
    ok = storage.delete_image(image_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Image not found")
    return {"success": True} 

@router.delete("/{image_id}/versions/{version_id}")
async def delete_version(
    image_id: str = Path(..., description="ID of the image"),
    version_id: str = Path(..., description="ID of the version to delete"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a specific version of an image.
    
    This endpoint allows you to remove a specific version from the image's version history.
    The version will be permanently deleted and cannot be recovered.
    
    Parameters:
    - image_id: The unique identifier of the image
    - version_id: The unique identifier of the version to delete
    
    Returns:
    - 200 OK: Version successfully deleted
    - 404 Not Found: If image or version doesn't exist
    - 400 Bad Request: If trying to delete the only version
    """
    versions = storage.get_image_versions(image_id)
    if not versions:
        raise HTTPException(status_code=404, detail="Image not found")
    
    if len(versions) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete the only version of an image"
        )
    
    version_to_delete = None
    for version in versions:
        if version['version_id'] == version_id:
            version_to_delete = version
            break
    
    if not version_to_delete:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # Delete the file
    filepath = os.path.join(storage.STATIC_DIR, version_to_delete['filename'])
    try:
        os.remove(filepath)
    except FileNotFoundError:
        pass  # File might already be deleted
    
    # Update the versions list in storage
    storage.delete_version(image_id, version_id)
    
    return {"message": "Version deleted successfully"}

@router.get("/gallery")
async def get_gallery():
    """
    Get all images in the gallery with their latest versions.
    """
    metadata = storage._load_metadata()
    images = []
    for image_id, image_data in metadata.items():
        versions = storage.get_image_versions(image_id)
        images.append({
            "image_id": image_id,
            "filename": image_data["filename"],
            "versions": versions
        })
    return images

# Authentication endpoints
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Batch processing endpoint
@router.post("/batch/process")
async def batch_process_images(
    image_ids: List[str],
    operation: str,
    params: dict,
    current_user: User = Depends(get_current_active_user)
):
    """
    Process multiple images with the same operation and parameters.
    
    Parameters:
    - image_ids: List of image IDs to process
    - operation: Operation to apply (resize, crop, rotate, etc.)
    - params: Parameters for the operation
    """
    return await batch_processor.process_batch(image_ids, operation, params, current_user)

# Metadata extraction endpoint
@router.get("/images/{image_id}/metadata")
async def get_image_metadata(
    image_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract and return metadata for an image.
    
    Parameters:
    - image_id: ID of the image to extract metadata from
    """
    image_path = os.path.join(storage.STATIC_DIR, f"images/{image_id}")
    metadata = batch_processor.extract_metadata(image_path)
    metadata_path = batch_processor.save_metadata(image_id, metadata)
    return {
        "metadata": metadata,
        "metadata_file": metadata_path
    }

# Format conversion endpoint
@router.post("/images/{image_id}/convert")
async def convert_image_format(
    image_id: str,
    target_format: str = Form(...),
    quality: int = Form(95),
    current_user: User = Depends(get_current_active_user)
):
    """
    Convert an image to a different format.
    
    Parameters:
    - image_id: ID of the image to convert
    - target_format: Target format (JPEG, PNG, etc.)
    - quality: Quality for lossy formats (1-100)
    """
    image_path = os.path.join(storage.STATIC_DIR, f"images/{image_id}")
    new_path = batch_processor.convert_format(image_path, target_format, quality)
    return {
        "message": "Image converted successfully",
        "new_path": new_path
    } 