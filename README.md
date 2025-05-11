# Image Processing Application

A web-based image processing application that allows users to upload, transform, and manage images with version control capabilities.

## Features

- Image upload and management
- Server-side image processing
- Version control system
- RESTful API

### Image Transformations
- Resize
- Crop
- Rotate
- Brightness/Contrast adjustment
- Grayscale filter
- Flip (horizontal/vertical)

## Setup and Run Instructions

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd image_app
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Access the application:
- Frontend: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Architecture Decisions

1. **Backend Framework**: FastAPI
   - Chosen for its high performance, automatic API documentation, and modern Python features
   - Built-in support for async operations and type hints

2. **Image Processing**: Python Imaging Library (PIL)
   - Industry-standard library for image processing
   - Provides comprehensive image manipulation capabilities
   - Efficient memory usage and processing

3. **Storage System**:
   - File-based storage for simplicity and easy deployment
   - Organized directory structure for images and versions
   - Unique identifiers for each image and version

4. **Frontend**:
   - Minimal HTML/CSS/JavaScript implementation
   - Focus on functionality over aesthetics
   - Responsive design for basic usability

## Assumptions and Limitations

1. **Storage**:
   - Assumes sufficient disk space for image storage
   - No automatic cleanup of old versions
   - No file size limits implemented

2. **Security**:
   - No authentication system
   - Basic CORS configuration
   - No rate limiting

3. **Performance**:
   - No image optimization
   - No caching system
   - Synchronous image processing

4. **Browser Support**:
   - Modern browser required
   - No fallback for older browsers

## Future Improvements

1. **Security Enhancements**:
   - Implement user authentication
   - Add rate limiting
   - Implement file type validation
   - Add size limits for uploads

2. **Performance Optimizations**:
   - Add image compression
   - Implement caching
   - Add async processing for large images
   - Implement load balancing

3. **Additional Features**:
   - Batch processing
   - Image metadata extraction
   - Format conversion
   - More filter options
   - Version comparison view

4. **User Experience**:
   - Add loading indicators
   - Improve error handling
   - Add success notifications
   - Enhance mobile responsiveness

5. **Testing**:
   - Add unit tests
   - Add integration tests
   - Add API endpoint tests
   - Add performance tests

## Time Spent
- Total development time: ~2.5 hours
- Focus on core functionality and clean code structure
- Prioritized essential features over stretch goals

## Technical Details

### Frontend
- HTML5, CSS3, and JavaScript
- Responsive design
- Modal view for enlarged images
- Interactive crop selection

### Backend
- FastAPI Python framework
- PIL (Python Imaging Library) for image processing
- RESTful API endpoints
- Version control system

### API Endpoints

#### Image Management
- `POST /images/upload` - Upload new image
- `GET /images/gallery` - Get all images
- `DELETE /images/{image_id}` - Delete image

#### Image Processing
- `POST /images/process/{image_id}` - Apply transformation
  - Parameters vary by operation type
  - Returns new version ID

#### Version Control
- `GET /images/{image_id}/versions` - Get version history
- `POST /images/{image_id}/revert/{version_id}` - Revert to version
- `DELETE /images/{image_id}/versions/{version_id}` - Delete version

## Development

### Prerequisites
- Python 3.11+
- Node.js (for frontend development)
- Docker (optional)

### Setup
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run backend: `uvicorn app.main:app --reload`
4. Access frontend at `http://localhost:8000`

### Docker Setup
1. Build images: `docker-compose build`
2. Run services: `docker-compose up`
3. Access application at `http://localhost:80` 