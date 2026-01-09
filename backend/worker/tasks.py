from celery import Celery
import os
import logging
from datetime import datetime
import boto3
from botocore.client import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import ffmpeg
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/2")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/3")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/4")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://comma:password@postgres:5432/commaconnect")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "comma-uploads")

# Initialize Celery
app = Celery(
    'comma_worker',
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
)

# Database setup
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url=f'http://{MINIO_ENDPOINT}',
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

@app.task(bind=True)
def process_video(self, route_id: str, segment_id: str, video_path: str):
    """Process uploaded video: transcode, generate thumbnail"""
    logger.info(f"Processing video for route {route_id}, segment {segment_id}")

    try:
        # Download video from MinIO
        local_video_path = f"/tmp/{segment_id}_input.hevc"
        output_video_path = f"/tmp/{segment_id}_output.mp4"
        thumbnail_path = f"/tmp/{segment_id}_thumb.jpg"

        logger.info(f"Downloading video from {video_path}")
        s3_client.download_file(MINIO_BUCKET, video_path, local_video_path)

        # Transcode video to web-compatible format
        logger.info("Transcoding video...")
        try:
            (
                ffmpeg
                .input(local_video_path)
                .output(
                    output_video_path,
                    vcodec='libx264',
                    acodec='aac',
                    video_bitrate='2M',
                    audio_bitrate='128k',
                    preset='medium',
                    movflags='faststart'
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.info("Video transcoded successfully")
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr.decode()}")
            raise

        # Generate thumbnail
        logger.info("Generating thumbnail...")
        try:
            (
                ffmpeg
                .input(output_video_path, ss=1)
                .filter('scale', 320, -1)
                .output(thumbnail_path, vframes=1)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            logger.info("Thumbnail generated successfully")
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error generating thumbnail: {e.stderr.decode()}")
            # Continue even if thumbnail fails

        # Upload processed video back to MinIO
        processed_video_path = video_path.replace('comma-uploads', 'comma-processed')
        logger.info(f"Uploading processed video to {processed_video_path}")
        s3_client.upload_file(output_video_path, MINIO_BUCKET, processed_video_path)

        # Upload thumbnail
        if os.path.exists(thumbnail_path):
            thumbnail_s3_path = video_path.replace('.hevc', '_thumb.jpg').replace('comma-uploads', 'comma-thumbnails')
            logger.info(f"Uploading thumbnail to {thumbnail_s3_path}")
            s3_client.upload_file(thumbnail_path, MINIO_BUCKET, thumbnail_s3_path)

        # Update database
        # TODO: Update segment with processed video path and thumbnail path

        # Cleanup
        for path in [local_video_path, output_video_path, thumbnail_path]:
            if os.path.exists(path):
                os.remove(path)

        logger.info(f"Video processing completed for segment {segment_id}")
        return {
            "status": "success",
            "processed_video_path": processed_video_path,
            "thumbnail_path": thumbnail_s3_path if os.path.exists(thumbnail_path) else None
        }

    except Exception as e:
        logger.error(f"Error processing video: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)

@app.task(bind=True)
def parse_log_file(self, route_id: str, segment_id: str, log_path: str):
    """Parse openpilot log file and extract metadata"""
    logger.info(f"Parsing log for route {route_id}, segment {segment_id}")

    try:
        # Download log from MinIO
        local_log_path = f"/tmp/{segment_id}_log.rlog"
        s3_client.download_file(MINIO_BUCKET, log_path, local_log_path)

        # TODO: Implement log parsing using capnproto
        # This would extract:
        # - GPS coordinates
        # - Speed data
        # - Events (disengagements, alerts)
        # - System metrics

        # For now, just mark as processed
        logger.info(f"Log parsing completed for segment {segment_id}")

        # Cleanup
        if os.path.exists(local_log_path):
            os.remove(local_log_path)

        return {
            "status": "success",
            "segment_id": segment_id
        }

    except Exception as e:
        logger.error(f"Error parsing log: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)

@app.task(bind=True)
def extract_route_metadata(self, route_id: str):
    """Extract and aggregate route metadata from all segments"""
    logger.info(f"Extracting metadata for route {route_id}")

    try:
        # TODO: Implement route metadata extraction
        # This would:
        # - Calculate total distance
        # - Calculate total duration
        # - Extract start/end locations
        # - Build route path
        # - Identify events

        logger.info(f"Metadata extraction completed for route {route_id}")

        return {
            "status": "success",
            "route_id": route_id
        }

    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)

@app.task
def cleanup_old_data(days: int = 90):
    """Cleanup old data based on retention policy"""
    logger.info(f"Running cleanup for data older than {days} days")

    try:
        # TODO: Implement cleanup logic
        # - Delete old routes based on retention policy
        # - Clean up orphaned files in MinIO
        # - Archive old data

        logger.info("Cleanup completed")

        return {
            "status": "success",
            "days": days
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise

@app.task
def generate_statistics(route_id: str):
    """Generate statistics for a route"""
    logger.info(f"Generating statistics for route {route_id}")

    try:
        # TODO: Implement statistics generation
        # - Average speed
        # - Max speed
        # - Distance covered
        # - Number of events
        # - Driving score

        logger.info(f"Statistics generated for route {route_id}")

        return {
            "status": "success",
            "route_id": route_id
        }

    except Exception as e:
        logger.error(f"Error generating statistics: {e}")
        raise

# Periodic tasks
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Setup periodic tasks"""
    # Run cleanup daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_data.s(),
        name='daily-cleanup'
    )

if __name__ == '__main__':
    app.start()
