"""
Quick standalone test to verify Google Vision service-account credentials.
Runs outside the Flask app so you can debug the credentials independently.
"""
import os
import sys
import argparse

try:
    from google.cloud import vision
    from google.oauth2 import service_account
except ImportError:
    print("Missing google-cloud-vision. Install with: pip install google-cloud-vision google-auth")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SA_PATH = os.path.join(PROJECT_ROOT, "keys", "sa-key.json")


def load_image_bytes(image_path: str) -> bytes:
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image path not found: {image_path}")
    with open(image_path, "rb") as f:
        return f.read()


def capture_frame_via_fswebcam() -> bytes:
    """
    Captures a frame using fswebcam. Requires /dev/video0 to exist.
    Useful when you don't have a saved JPEG to test with.
    """
    import subprocess

    result = subprocess.run(
        [
            "fswebcam",
            "-d", "/dev/video0",
            "-r", "640x480",
            "--no-banner",
            "--skip", "2",
            "--jpeg", "85",
            "-"
        ],
        capture_output=True,
        timeout=5
    )

    if result.returncode != 0 or len(result.stdout) == 0:
        raise RuntimeError(f"fswebcam failed: {result.stderr.decode(errors='ignore')}")
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="Test Google Vision service account integration.")
    parser.add_argument(
        "--credentials",
        default=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", DEFAULT_SA_PATH),
        help="Path to the service account JSON file."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", help="Path to a JPEG/PNG image to analyze.")
    group.add_argument(
        "--capture",
        action="store_true",
        help="Capture one frame using fswebcam (/dev/video0 required)."
    )
    args = parser.parse_args()

    if not args.credentials or not os.path.exists(args.credentials):
        print("Service account JSON not found.")
        print("Provide --credentials path or set GOOGLE_APPLICATION_CREDENTIALS.")
        sys.exit(1)

    print(f"[INFO] Using credentials: {args.credentials}")
    credentials = service_account.Credentials.from_service_account_file(args.credentials)
    client = vision.ImageAnnotatorClient(credentials=credentials)

    if args.capture:
        print("[INFO] Capturing frame via fswebcam...")
        image_bytes = capture_frame_via_fswebcam()
    else:
        print(f"[INFO] Loading image from {args.image}")
        image_bytes = load_image_bytes(args.image)

    image = vision.Image(content=image_bytes)
    print("[INFO] Sending request to Google Vision (OBJECT_LOCALIZATION)...")
    response = client.object_localization(image=image)

    if response.error.message:
        print("[ERROR] API returned error:", response.error.message)
        sys.exit(1)

    objects = response.localized_object_annotations
    print(f"[SUCCESS] Detected {len(objects)} objects, {sum(1 for obj in objects if obj.name.lower() == 'person')} persons.")
    for obj in objects:
        print(f" - {obj.name:10s} ({obj.score:.2f})")


if __name__ == "__main__":
    main()

