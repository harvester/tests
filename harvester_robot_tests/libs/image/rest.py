"""
Image Rest Implementation - makes actual API calls using get_harvester_api_client()
"""
import time
from datetime import datetime, timedelta
from utility.utility import get_harvester_api_client
from utility.utility import get_retry_count_and_interval
from utility.utility import logging
from image.base import Base


class Rest(Base):
    """Image Rest implementation - makes actual API calls"""

    def __init__(self):
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    def create_from_url(self, image_name, image_url, checksum, **kwargs):
        """Create image from URL"""
        api = get_harvester_api_client()

        code, data = api.images.create_by_url(image_name, image_url)
        assert code == 201, f"Failed to create image: {code}, {data}"

        return data['metadata']['namespace'] + '/' + image_name

    def wait_for_downloaded(self, image_name, timeout):
        """Wait for image to be downloaded"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        last_percent = -1

        while endtime > datetime.now():
            code, data = api.images.get(image_name)
            if code == 200:
                status = data.get('status', {})
                # Harvester uses 'progress' field, not 'downloadPercent'
                download_percent = status.get('progress', 0)

                # Log progress if it changed
                if download_percent != last_percent:
                    logging(f"Image {image_name} download progress: {download_percent}%")
                    last_percent = download_percent

                if download_percent == 100:
                    conditions = status.get('conditions', [])
                    for condition in conditions:
                        if (
                            condition.get('type') == 'Initialized' and
                            condition.get('status') == 'True'
                        ):
                            logging(f"Image {image_name} downloaded successfully")
                            return True
                    # If 100% but not initialized, log that
                    logging("Image at 100% but waiting for Initialized condition...")
            elif code == 404:
                logging(f"Image {image_name} not found yet, waiting...")
            else:
                logging(f"Got status code {code} while checking image: {data}")

            time.sleep(self.retry_interval)

        raise AssertionError(f"Image {image_name} did not download within {timeout}s")

    def wait_for_ready(self, image_name, timeout):
        """Wait for image to be ready"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.images.get(image_name)
            if code == 200:
                conditions = data.get('status', {}).get('conditions', [])
                for condition in conditions:
                    if condition.get('type') == 'Ready' and condition.get('status') == 'True':
                        return True
            time.sleep(3)

        raise AssertionError(f"Image {image_name} was not ready within {timeout}s")

    def delete(self, image_name, namespace):
        """Delete an image"""
        api = get_harvester_api_client()
        code, data = api.images.delete(image_name, namespace)
        assert code == 200, f"Failed to delete image: {code}, {data}"

    def wait_for_deleted(self, image_name, timeout):
        """Wait for image to be deleted"""
        api = get_harvester_api_client()

        endtime = datetime.now() + timedelta(seconds=timeout)
        while endtime > datetime.now():
            code, data = api.images.get(image_name)
            if code == 404:
                return True
            time.sleep(3)

        raise AssertionError(f"Image {image_name} was not deleted within {timeout}s")

    def get_status(self, image_name, namespace):
        """Get image status"""
        api = get_harvester_api_client()
        code, data = api.images.get(image_name, namespace)
        assert code == 200, f"Failed to get image status: {code}, {data}"

        status = data.get('status', {})
        # Harvester uses 'progress' field, not 'downloadPercent'
        progress = status.get('progress', 0)
        return {
            'state': 'Ready' if progress == 100 else 'Downloading',
            'download_percent': progress,
            'progress': progress,
            'size': status.get('size', 0),
            'conditions': status.get('conditions', [])
        }

    def list(self, namespace):
        """List all images"""
        api = get_harvester_api_client()
        code, data = api.images.list(namespace)
        assert code == 200, f"Failed to list images: {code}, {data}"

        images = []
        for item in data.get('items', []):
            images.append({
                'name': item['metadata']['name'],
                'namespace': item['metadata']['namespace'],
                'creation_time': item['metadata']['creationTimestamp'],
                'status': item.get('status', {})
            })

        return images

    def exists(self, image_name, namespace):
        """Check if image exists"""
        api = get_harvester_api_client()
        code, data = api.images.get(image_name, namespace)
        return code == 200

    def cleanup(self):
        """Clean up all test images"""
        logging('Cleaning up test images')
