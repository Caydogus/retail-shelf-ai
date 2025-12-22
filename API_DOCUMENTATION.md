# API Documentation

## Base URL
\\\
http://localhost:8000
\\\

## Authentication
Currently no authentication required (TODO: Add JWT tokens)

## Response Format

### Success Response
\\\json
{
  "status": "success",
  "data": {...}
}
\\\

### Error Response
\\\json
{
  "detail": "Error message"
}
\\\

## Endpoints

### 1. Companies

#### Create Company
\\\http
POST /api/companies/
Content-Type: application/json

{
  "name": "Company Name",
  "description": "Description"
}
\\\

#### List Companies
\\\http
GET /api/companies/?skip=0&limit=100
\\\

#### Get Company
\\\http
GET /api/companies/{company_id}
\\\

#### Update Company
\\\http
PUT /api/companies/{company_id}
Content-Type: application/json

{
  "name": "Updated Name",
  "description": "Updated Description"
}
\\\

#### Delete Company
\\\http
DELETE /api/companies/{company_id}
\\\

#### Upload Logo
\\\http
POST /api/companies/{company_id}/logo
Content-Type: multipart/form-data

file: <image_file>
\\\

### 2. Products

#### Create Product
\\\http
POST /api/products/
Content-Type: application/json

{
  "company_id": 1,
  "name": "Product Name",
  "sku": "SKU123",
  "barcode": "1234567890",
  "category": "Beverages",
  "brand": "Brand Name",
  "package_type": "bottle",
  "reference_colors": {
    "primary": "#FF0000",
    "secondary": "#00FF00"
  },
  "dimensions": {
    "width": 100,
    "height": 200,
    "depth": 50
  }
}
\\\

### 3. Datasets

#### Create Dataset
\\\http
POST /api/datasets/
Content-Type: application/json

{
  "company_id": 1,
  "name": "Dataset Name",
  "description": "Description"
}
\\\

#### Upload Image
\\\http
POST /api/datasets/{dataset_id}/upload-image
Content-Type: multipart/form-data

file: <image_file>
\\\

#### Annotate Image
\\\http
POST /api/datasets/{dataset_id}/annotate/{filename}
Content-Type: application/json

{
  "annotations": [
    {
      "class_id": 0,
      "class_name": "Product A",
      "x_center": 0.5,
      "y_center": 0.5,
      "width": 0.2,
      "height": 0.3
    }
  ]
}
\\\

#### Prepare Dataset
\\\http
POST /api/datasets/{dataset_id}/prepare
Content-Type: application/json

{
  "classes": ["Product A", "Product B", "Product C"],
  "train_ratio": 0.8
}
\\\

### 4. Training

#### Start Training
\\\http
POST /api/training/start
Content-Type: application/json

{
  "company_id": 1,
  "dataset_id": 1,
  "model_name": "My Model v1",
  "epochs": 50,
  "batch_size": 16,
  "image_size": 640
}

Response:
{
  "task_id": "abc-123",
  "model_id": 1,
  "status": "started",
  "message": "Training started successfully"
}
\\\

#### Get Training Status
\\\http
GET /api/training/status/{task_id}

Response:
{
  "task_id": "abc-123",
  "state": "PROGRESS",
  "status": "Training epoch 25/50",
  "result": {
    "current": 25,
    "total": 50
  }
}
\\\

### 5. Analysis

#### Upload and Analyze
\\\http
POST /api/analysis/upload?company_id=1&model_id=1
Content-Type: multipart/form-data

file: <shelf_image>

Response:
{
  "task_id": "xyz-789",
  "message": "Analysis started successfully"
}
\\\

#### Get Analysis Status
\\\http
GET /api/analysis/status/{task_id}

Response:
{
  "task_id": "xyz-789",
  "state": "SUCCESS",
  "result": {
    "analysis_id": 1,
    "total_products": 15,
    "product_counts": {
      "Product A": 5,
      "Product B": 10
    },
    "shelf_coverage": 72.5,
    "total_score": 85.3
  }
}
\\\

### 6. Scoring

#### Calculate Score
\\\http
POST /api/scoring/calculate
Content-Type: application/json

{
  "shelf_coverage": 75.0,
  "visibility_score": 80.0,
  "expected_distribution": {"left": 33, "center": 34, "right": 33},
  "actual_distribution": {"left": 5, "center": 8, "right": 2},
  "color_matches": {"Product A": 85.5, "Product B": 92.3}
}

Response:
{
  "total_score": 82.5,
  "component_scores": {
    "shelf_coverage": 95.0,
    "product_visibility": 80.0,
    "planogram_compliance": 75.0,
    "color_match": 88.9
  },
  "weights_used": {
    "shelf_coverage": 0.25,
    "product_visibility": 0.30,
    "planogram_compliance": 0.25,
    "color_match": 0.20
  }
}
\\\

## Status Codes

- \200 OK\: Success
- \201 Created\: Resource created
- \400 Bad Request\: Invalid input
- \404 Not Found\: Resource not found
- \500 Internal Server Error\: Server error

## Rate Limiting
Currently no rate limiting (TODO)

## Pagination
List endpoints support \skip\ and \limit\ parameters:
- \skip\: Number of records to skip (default: 0)
- \limit\: Maximum records to return (default: 100)
