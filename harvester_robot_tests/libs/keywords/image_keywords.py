
"""
Image Keywords - creates Image() instance and delegates - NO direct API calls!
"""

from utility.utility import logging
from image import Image
from constant import DEFAULT_TIMEOUT


class image_keywords:
    """Layer 3: Image keyword wrapper - creates Image component and delegates"""

    def __init__(self):
        self.image = Image()

    def cleanup_images(self):
        """Clean up all test images"""
        self.image.cleanup()

    def create_image_from_url(self, image_name, image_url, checksum="", **kwargs):
        """Create image from URL"""
        logging(f'Creating image {image_name}')
        self.image.create_from_url(image_name, image_url, checksum, **kwargs)

    def wait_for_image_downloaded(self, image_name, timeout=DEFAULT_TIMEOUT):
        """Wait for image to be downloaded"""
        logging(f'Waiting for image {image_name} to be downloaded')
        self.image.wait_for_downloaded(image_name, timeout)

    def wait_for_image_ready(self, image_name, timeout=DEFAULT_TIMEOUT):
        """Wait for image to be ready"""
        logging(f'Waiting for image {image_name} to be ready')
        self.image.wait_for_ready(image_name, timeout)

    def delete_image(self, image_name, namespace='default'):
        """Delete an image"""
        logging(f'Deleting image {image_name}')
        self.image.delete(image_name, namespace)

    def wait_for_image_deleted(self, image_name, timeout=DEFAULT_TIMEOUT):
        """Wait for image to be deleted"""
        logging(f'Waiting for image {image_name} to be deleted')
        self.image.wait_for_deleted(image_name, timeout)

    def get_image_status(self, image_name, namespace='default'):
        """Get image status"""
        logging(f'Getting status for image {image_name}')
        return self.image.get_status(image_name, namespace)

    def list_images(self, namespace='default'):
        """List all images"""
        logging('Listing all images')
        return self.image.list(namespace)

    def image_exists(self, image_name, namespace='default'):
        """Check if image exists"""
        return self.image.exists(image_name, namespace)
