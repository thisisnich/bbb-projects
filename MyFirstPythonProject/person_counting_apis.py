"""
Person Counting API Integration Examples
Choose one API service and integrate it with your video stream
"""

import requests
import base64
import json
from typing import Optional, Tuple

class PersonCounterAPI:
    """Base class for person counting APIs"""
    
    def count_people(self, image_bytes: bytes) -> Tuple[int, dict]:
        """
        Count people in image
        Returns: (count, metadata)
        """
        raise NotImplementedError


class AWSRekognitionCounter(PersonCounterAPI):
    """AWS Rekognition API for person detection"""
    
    def __init__(self, access_key: str, secret_key: str, region: str = 'us-east-1'):
        import boto3
        self.client = boto3.client(
            'rekognition',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
    
    def count_people(self, image_bytes: bytes) -> Tuple[int, dict]:
        """Count people using AWS Rekognition"""
        try:
            response = self.client.detect_labels(
                Image={'Bytes': image_bytes},
                MaxLabels=10,
                MinConfidence=70
            )
            
            # Count person labels
            person_count = 0
            for label in response.get('Labels', []):
                if label['Name'].lower() in ['person', 'people', 'human']:
                    # Rekognition doesn't give exact count, but we can estimate
                    # based on instances if available
                    if 'Instances' in label:
                        person_count = len(label['Instances'])
                    else:
                        # If no instances, assume at least 1 if confidence is high
                        if label['Confidence'] > 80:
                            person_count = max(person_count, 1)
            
            return person_count, {
                'labels': response.get('Labels', []),
                'raw_response': response
            }
        except Exception as e:
            print(f"[ERROR] AWS Rekognition error: {e}")
            return 0, {'error': str(e)}


class GoogleVisionCounter(PersonCounterAPI):
    """Google Cloud Vision API for person detection"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = 'https://vision.googleapis.com/v1/images:annotate'
    
    def count_people(self, image_bytes: bytes) -> Tuple[int, dict]:
        """Count people using Google Vision API"""
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            payload = {
                'requests': [{
                    'image': {
                        'content': image_base64
                    },
                    'features': [{
                        'type': 'OBJECT_LOCALIZATION',
                        'maxResults': 50
                    }]
                }]
            }
            
            response = requests.post(
                f'{self.endpoint}?key={self.api_key}',
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            objects = data.get('responses', [{}])[0].get('localizedObjectAnnotations', [])
            
            # Count person objects
            person_count = sum(1 for obj in objects if obj['name'].lower() == 'person')
            
            return person_count, {
                'objects': objects,
                'raw_response': data
            }
        except Exception as e:
            print(f"[ERROR] Google Vision error: {e}")
            return 0, {'error': str(e)}


class AzureVisionCounter(PersonCounterAPI):
    """Azure Computer Vision API for person detection"""
    
    def __init__(self, endpoint: str, subscription_key: str):
        self.endpoint = endpoint.rstrip('/')
        self.subscription_key = subscription_key
    
    def count_people(self, image_bytes: bytes) -> Tuple[int, dict]:
        """Count people using Azure Computer Vision"""
        try:
            url = f"{self.endpoint}/vision/v3.2/detect"
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.subscription_key,
                'Content-Type': 'application/octet-stream'
            }
            
            response = requests.post(url, headers=headers, data=image_bytes)
            response.raise_for_status()
            
            data = response.json()
            objects = data.get('objects', [])
            
            # Count person objects
            person_count = sum(1 for obj in objects if obj.get('object', '').lower() == 'person')
            
            return person_count, {
                'objects': objects,
                'raw_response': data
            }
        except Exception as e:
            print(f"[ERROR] Azure Vision error: {e}")
            return 0, {'error': str(e)}


class HuggingFaceCounter(PersonCounterAPI):
    """Hugging Face Inference API for person detection"""
    
    def __init__(self, api_token: str, model: str = "facebook/detr-resnet-50"):
        self.api_token = api_token
        self.model = model
        self.endpoint = f"https://api-inference.huggingface.co/models/{model}"
    
    def count_people(self, image_bytes: bytes) -> Tuple[int, dict]:
        """Count people using Hugging Face API"""
        try:
            headers = {"Authorization": f"Bearer {self.api_token}"}
            
            response = requests.post(
                self.endpoint,
                headers=headers,
                data=image_bytes
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Count person detections (label usually "person")
            person_count = sum(
                1 for item in data 
                if isinstance(item, dict) and 
                item.get('label', '').lower() in ['person', 'people']
            )
            
            return person_count, {
                'detections': data,
                'raw_response': data
            }
        except Exception as e:
            print(f"[ERROR] Hugging Face error: {e}")
            return 0, {'error': str(e)}


# Example usage with your video stream
def integrate_with_stream(counter: PersonCounterAPI, frame_bytes: bytes, frame_interval: int = 30):
    """
    Example function showing how to integrate with your video stream
    
    Args:
        counter: PersonCounterAPI instance
        frame_bytes: JPEG frame bytes from capture_frame()
        frame_interval: Analyze every Nth frame (to reduce API calls)
    """
    # This would be called periodically in your generate_stream() function
    count, metadata = counter.count_people(frame_bytes)
    print(f"[INFO] People detected: {count}")
    return count, metadata


# Configuration example
"""
# AWS Rekognition
counter = AWSRekognitionCounter(
    access_key='YOUR_ACCESS_KEY',
    secret_key='YOUR_SECRET_KEY',
    region='us-east-1'
)

# Google Vision
counter = GoogleVisionCounter(api_key='YOUR_API_KEY')

# Azure Vision
counter = AzureVisionCounter(
    endpoint='https://YOUR_REGION.api.cognitive.microsoft.com',
    subscription_key='YOUR_SUBSCRIPTION_KEY'
)

# Hugging Face (free tier available)
counter = HuggingFaceCounter(api_token='YOUR_HF_TOKEN')
"""

