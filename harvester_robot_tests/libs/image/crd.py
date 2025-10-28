"""
Image CRD Implementation
Uses Kubernetes Custom Resources for VirtualMachineImage operations
"""
import time
from kubernetes import client
from kubernetes.client.rest import ApiException
from crd import (
    get_cr, create_cr, delete_cr, list_cr,
    wait_for_cr_deleted, wait_for_cr_condition
)
from constant import (
    HARVESTER_API_GROUP, HARVESTER_API_VERSION,
    VIRTUALMACHINEIMAGE_PLURAL, DEFAULT_NAMESPACE,
    IMAGE_STATE_ACTIVE, IMAGE_STATE_IMPORTING,
    LABEL_TEST, LABEL_TEST_VALUE,
    DEFAULT_TIMEOUT
)
from image.base import Base
from utility.utility import logging, get_retry_count_and_interval


class CRD(Base):
    """
    Image CRD implementation
    Uses harvesterhci.io/v1beta1 VirtualMachineImage CRD
    """

    def __init__(self):
        self.obj_api = client.CustomObjectsApi()
        self.retry_count, self.retry_interval = get_retry_count_and_interval()

    def create_from_url(self, image_name, image_url, checksum, **kwargs):
        """
        Create a VirtualMachineImage from URL

        CRD Structure:
        apiVersion: harvesterhci.io/v1beta1
        kind: VirtualMachineImage
        spec:
          displayName: "Display Name"
          sourceType: download
          url: "https://..."
        """
        namespace = kwargs.get('namespace', DEFAULT_NAMESPACE)
        display_name = kwargs.get('display_name', image_name)
        description = kwargs.get('description', f'Test image {image_name}')

        body = {
            "apiVersion": f"{HARVESTER_API_GROUP}/{HARVESTER_API_VERSION}",
            "kind": "VirtualMachineImage",
            "metadata": {
                "name": image_name,
                "namespace": namespace,
                "labels": {
                    LABEL_TEST: LABEL_TEST_VALUE
                },
                "annotations": {
                    "field.cattle.io/description": description
                }
            },
            "spec": {
                "displayName": display_name,
                "sourceType": "download",
                "url": image_url
            }
        }

        # Add checksum if provided
        if checksum:
            body["spec"]["checksum"] = checksum

        try:
            logging(f"Creating VirtualMachineImage {namespace}/{image_name}")
            result = create_cr(             # NOQA
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace=namespace,
                plural=VIRTUALMACHINEIMAGE_PLURAL,
                body=body
            )

            # Wait for image to be created
            self.wait_for_image_created(image_name, namespace)

            return f"{namespace}/{image_name}"

        except ApiException as e:
            logging(f"Failed to create image {image_name}: {e}")
            raise Exception(f"Failed to create image: {e.status}, {e.reason}")

    def delete(self, image_name, namespace=DEFAULT_NAMESPACE):
        """Delete a VirtualMachineImage"""
        try:
            logging(f"Deleting VirtualMachineImage {namespace}/{image_name}")
            delete_cr(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace=namespace,
                plural=VIRTUALMACHINEIMAGE_PLURAL,
                name=image_name
            )
        except ApiException as e:
            if e.status != 404:  # Ignore not found errors
                logging(f"Error deleting image {image_name}: {e}")
                raise

    def get(self, image_name, namespace=DEFAULT_NAMESPACE):
        """Get a VirtualMachineImage"""
        return get_cr(
            group=HARVESTER_API_GROUP,
            version=HARVESTER_API_VERSION,
            namespace=namespace,
            plural=VIRTUALMACHINEIMAGE_PLURAL,
            name=image_name
        )

    def list(self, namespace=DEFAULT_NAMESPACE, label_selector=None):
        """List VirtualMachineImages"""
        result = list_cr(
            group=HARVESTER_API_GROUP,
            version=HARVESTER_API_VERSION,
            namespace=namespace,
            plural=VIRTUALMACHINEIMAGE_PLURAL,
            label_selector=label_selector
        )
        return result.get("items", [])

    def wait_for_image_created(self, image_name, namespace=DEFAULT_NAMESPACE):
        """Wait for image CR to be created"""
        for i in range(self.retry_count):
            try:
                self.get(image_name, namespace)
                logging(f"VirtualMachineImage {namespace}/{image_name} created")
                return True
            except Exception:
                logging(f"Waiting for image to be created ({i})...")
                time.sleep(self.retry_interval)
        raise AssertionError(f"VirtualMachineImage {namespace}/{image_name} not created")

    def wait_for_downloaded(self, image_name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for image to be downloaded
        Check status.downloadPercent == 100 and condition Initialized=True
        """
        namespace = DEFAULT_NAMESPACE
        endtime = time.time() + timeout

        while time.time() < endtime:
            try:
                image = self.get(image_name, namespace)
                status = image.get("status", {})

                # Check download percent - Harvester uses 'progress' field
                download_percent = status.get("progress", 0)
                if download_percent == 100:
                    # Check Initialized condition
                    conditions = status.get("conditions", [])
                    for condition in conditions:
                        is_initialized = condition.get("type") == "Initialized"
                        is_true = condition.get("status") == "True"
                        if is_initialized and is_true:
                            logging(f"Image {namespace}/{image_name} downloaded successfully")
                            return True
                logging(f"Waiting for image download: {download_percent}%...")
            except Exception as e:
                logging(f"Error checking image status: {e}")
            time.sleep(self.retry_interval)
        raise AssertionError(f"Image {namespace}/{image_name} did not download within {timeout}s")

    def wait_for_ready(self, image_name, timeout=DEFAULT_TIMEOUT):
        """
        Wait for image to be ready
        Check for Ready condition
        """
        namespace = DEFAULT_NAMESPACE

        try:
            wait_for_cr_condition(
                group=HARVESTER_API_GROUP,
                version=HARVESTER_API_VERSION,
                namespace=namespace,
                plural=VIRTUALMACHINEIMAGE_PLURAL,
                name=image_name,
                condition_type="Ready",
                condition_status="True",
                timeout=timeout
            )
            logging(f"Image {namespace}/{image_name} is ready")
            return True
        except Exception as e:
            logging(f"Image did not become ready: {e}")
            raise

    def wait_for_deleted(self, image_name, timeout=DEFAULT_TIMEOUT):
        """Wait for image to be deleted"""
        namespace = DEFAULT_NAMESPACE

        wait_for_cr_deleted(
            group=HARVESTER_API_GROUP,
            version=HARVESTER_API_VERSION,
            namespace=namespace,
            plural=VIRTUALMACHINEIMAGE_PLURAL,
            name=image_name,
            timeout=timeout
        )

    def get_status(self, image_name, namespace=DEFAULT_NAMESPACE):
        """Get image status"""
        image = self.get(image_name, namespace)
        status = image.get("status", {})

        # Determine state from conditions
        conditions = status.get("conditions", [])
        state = "Unknown"

        for condition in conditions:
            if condition.get("type") == "Initialized":
                if condition.get("status") == "True":
                    state = IMAGE_STATE_ACTIVE
                else:
                    state = IMAGE_STATE_IMPORTING
            elif condition.get("type") == "Ready":
                if condition.get("status") == "True":
                    state = IMAGE_STATE_ACTIVE

        return {
            'state': state,
            'download_percent': status.get('progress', 0),
            'size': status.get('size', 0),
            'conditions': conditions
        }

    def exists(self, image_name, namespace=DEFAULT_NAMESPACE):
        """Check if image exists"""
        try:
            self.get(image_name, namespace)
            return True
        except Exception:
            return False

    def cleanup(self):
        """Clean up all test images"""
        logging('Cleaning up test images')

        try:
            # List all images with test label
            images = self.list(
                namespace=DEFAULT_NAMESPACE,
                label_selector=f"{LABEL_TEST}={LABEL_TEST_VALUE}"
            )

            for image in images:
                image_name = image['metadata']['name']
                namespace = image['metadata']['namespace']

                try:
                    logging(f'Deleting test image: {namespace}/{image_name}')
                    self.delete(image_name, namespace)
                except Exception as e:
                    logging(f'Error deleting image {image_name}: {e}', 'WARNING')
        except Exception as e:
            logging(f'Error during image cleanup: {e}', 'WARNING')
