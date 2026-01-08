from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import boto3
from botocore.client import Config
import os
import uuid

from database import get_db
from models import User, Device, Route, RouteSegment
from schemas import UploadInitRequest, UploadInitResponse, UploadCompleteRequest
from auth import get_current_active_user

router = APIRouter()

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "comma-uploads")

# Initialize MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url=f'http://{MINIO_ENDPOINT}',
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

@router.post("/init", response_model=UploadInitResponse)
async def initialize_upload(
    upload_data: UploadInitRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Initialize a multipart upload session"""
    # Parse route name (format: dongle_id|timestamp)
    try:
        dongle_id, timestamp = upload_data.route_name.split('|')
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route name format"
        )

    # Verify device ownership
    device = db.query(Device).filter(
        Device.dongle_id == dongle_id,
        Device.owner_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Get or create route
    route = db.query(Route).filter(Route.fullname == upload_data.route_name).first()
    if not route:
        from datetime import datetime
        route = Route(
            device_id=device.id,
            fullname=upload_data.route_name,
            start_time=datetime.fromisoformat(timestamp.replace('--', ':'))
        )
        db.add(route)
        db.commit()
        db.refresh(route)

    # Get or create segment
    segment = db.query(RouteSegment).filter(
        RouteSegment.route_id == route.id,
        RouteSegment.segment_number == upload_data.segment_number
    ).first()

    if not segment:
        canonical_name = f"{upload_data.route_name}--{upload_data.segment_number}"
        segment = RouteSegment(
            route_id=route.id,
            segment_number=upload_data.segment_number,
            canonical_name=canonical_name
        )
        db.add(segment)
        db.commit()
        db.refresh(segment)

    # Generate upload ID and presigned URL
    upload_id = str(uuid.uuid4())
    object_key = f"{dongle_id}/{upload_data.route_name}/{upload_data.segment_number}/{upload_data.file_type}"

    # Create multipart upload
    try:
        multipart = s3_client.create_multipart_upload(
            Bucket=MINIO_BUCKET,
            Key=object_key
        )

        # Generate presigned URL for upload
        presigned_url = s3_client.generate_presigned_url(
            'upload_part',
            Params={
                'Bucket': MINIO_BUCKET,
                'Key': object_key,
                'UploadId': multipart['UploadId'],
                'PartNumber': 1
            },
            ExpiresIn=3600
        )

        return {
            "upload_id": multipart['UploadId'],
            "presigned_url": presigned_url,
            "chunk_size": 10485760  # 10MB
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize upload: {str(e)}"
        )

@router.post("/chunk")
async def upload_chunk(
    file: UploadFile = File(...),
    upload_id: str = None,
    part_number: int = None,
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file chunk"""
    # TODO: Implement chunk upload
    return {"message": "Chunk uploaded successfully"}

@router.post("/complete")
async def complete_upload(
    complete_data: UploadCompleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Complete multipart upload"""
    # TODO: Implement upload completion
    return {"message": "Upload completed successfully"}

@router.post("/cancel")
async def cancel_upload(
    upload_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Cancel an upload"""
    # TODO: Implement upload cancellation
    return {"message": "Upload cancelled"}

@router.get("/presigned")
async def get_presigned_url(
    route_name: str,
    segment_number: int,
    file_type: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a presigned URL for direct S3 upload"""
    # Parse route name
    try:
        dongle_id, timestamp = route_name.split('|')
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid route name format"
        )

    # Verify device ownership
    device = db.query(Device).filter(
        Device.dongle_id == dongle_id,
        Device.owner_id == current_user.id
    ).first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )

    # Generate presigned URL
    object_key = f"{dongle_id}/{route_name}/{segment_number}/{file_type}"

    try:
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': MINIO_BUCKET,
                'Key': object_key
            },
            ExpiresIn=3600
        )

        return {
            "presigned_url": presigned_url,
            "object_key": object_key
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )
