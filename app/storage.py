import os
import json
from uuid import uuid4, UUID
from datetime import datetime
from typing import List, Optional
from io import BytesIO

# Use absolute paths for Docker container
STATIC_DIR = '/app/static'
UPLOAD_DIR = STATIC_DIR
METADATA_FILE = os.path.join(STATIC_DIR, 'metadata.json')

# Ensure static directory exists
os.makedirs(STATIC_DIR, exist_ok=True)

def _load_metadata():
    if not os.path.exists(METADATA_FILE):
        return {}
    with open(METADATA_FILE, 'r') as f:
        return json.load(f)

def _save_metadata(metadata):
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def save_image(file, transformation=None, parent_id=None):
    metadata = _load_metadata()
    image_id = str(uuid4()) if not parent_id else parent_id
    version_id = str(uuid4())
    filename = f"{version_id}_{file.filename}"
    filepath = os.path.join(STATIC_DIR, filename)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'wb') as out_file:
        out_file.write(file.file.read())
    now = datetime.utcnow().isoformat()
    version = {
        'version_id': version_id,
        'image_id': image_id,
        'filename': filename,
        'url': f"/static/{filename}",
        'created_at': now,
        'transformation': transformation
    }
    if image_id not in metadata:
        metadata[image_id] = {
            'image_id': image_id,
            'filename': file.filename,
            'created_at': now,
            'versions': [version]
        }
    else:
        metadata[image_id]['versions'].append(version)
    _save_metadata(metadata)
    return image_id, version

def get_images():
    metadata = _load_metadata()
    return list(metadata.values())

def get_image_versions(image_id):
    metadata = _load_metadata()
    versions = metadata.get(image_id, {}).get('versions', [])
    # Sort versions by created_at in descending order (newest first)
    return sorted(versions, key=lambda x: x['created_at'], reverse=True)

def revert_to_version(image_id, version_id):
    metadata = _load_metadata()
    image = metadata.get(image_id)
    if not image:
        return False
    versions = image['versions']
    idx = next((i for i, v in enumerate(versions) if v['version_id'] == version_id), None)
    if idx is None:
        return False
    image['versions'] = versions[:idx+1]
    _save_metadata(metadata)
    return True

def delete_image(image_id):
    metadata = _load_metadata()
    image = metadata.pop(image_id, None)
    if image:
        for v in image['versions']:
            try:
                os.remove(os.path.join(STATIC_DIR, v['filename']))
            except Exception:
                pass
        _save_metadata(metadata)
        return True
    return False

def delete_version(image_id, version_id):
    metadata = _load_metadata()
    image = metadata.get(image_id)
    if not image:
        return False
    
    versions = image['versions']
    version_to_delete = None
    for version in versions:
        if version['version_id'] == version_id:
            version_to_delete = version
            break
    
    if not version_to_delete:
        return False
    
    # Remove the version from the list
    image['versions'] = [v for v in versions if v['version_id'] != version_id]
    _save_metadata(metadata)
    return True

def save_version(image_id, image_bytes, transformation=None):
    """
    Save a new version of an image.
    
    Args:
        image_id: The ID of the image
        image_bytes: The processed image data as bytes
        transformation: Description of the transformation applied
    
    Returns:
        The new version metadata
    """
    metadata = _load_metadata()
    if image_id not in metadata:
        raise ValueError("Image not found")
    
    version_id = str(uuid4())
    original_filename = metadata[image_id]['filename']
    filename = f"{version_id}_{original_filename}"
    filepath = os.path.join(STATIC_DIR, filename)
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'wb') as out_file:
        out_file.write(image_bytes)
    
    now = datetime.utcnow().isoformat()
    version = {
        'version_id': version_id,
        'image_id': image_id,
        'filename': filename,
        'url': f"/static/{filename}",
        'created_at': now,
        'transformation': transformation
    }
    
    metadata[image_id]['versions'].append(version)
    _save_metadata(metadata)
    return version 