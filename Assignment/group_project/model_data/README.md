# MobileNet SSD Model Files

This directory contains the MobileNet SSD model files used for OpenCV-based people detection.

## Required Files

1. **ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt** - Model configuration file
2. **frozen_inference_graph.pb** - Model weights file
3. **coco.names** - Class names file (COCO dataset class labels)

## Download Instructions

### Option 1: Download from OpenCV Zoo (Recommended)

The MobileNet SSD model is available from the OpenCV Model Zoo:

1. **Config file (pbtxt):**
   - Download from: https://github.com/opencv/opencv_extra/blob/master/testdata/dnn/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt
   - Or search for "ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt" in OpenCV repository

2. **Model weights (pb):**
   - Download from: http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v3_large_coco_2020_01_14.tar.gz
   - Extract the `frozen_inference_graph.pb` file from the archive

3. **Class names (coco.names):**
   - Download from: https://github.com/opencv/opencv/blob/master/samples/data/dnn/object_detection_classes_coco.txt
   - Rename to `coco.names` or copy the content

### Option 2: Use TensorFlow Model Zoo

1. Visit: https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/tf2_detection_zoo.md
2. Download "SSD MobileNet V3 Large 320x320" model
3. Extract the model files

### Option 3: Quick Download Script

```bash
cd /home/server/Desktop/bbbw-project/bbb-projects/Assignment/group_project/model_data

# Download config file
wget https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt

# Download model weights (requires extracting from tar.gz)
wget http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v3_large_coco_2020_01_14.tar.gz
tar -xzf ssd_mobilenet_v3_large_coco_2020_01_14.tar.gz
mv ssd_mobilenet_v3_large_coco_2020_01_14/frozen_inference_graph.pb .
rm -rf ssd_mobilenet_v3_large_coco_2020_01_14 ssd_mobilenet_v3_large_coco_2020_01_14.tar.gz

# Download class names
wget https://raw.githubusercontent.com/opencv/opencv/master/samples/data/dnn/object_detection_classes_coco.txt -O coco.names
```

## File Structure

After downloading, the directory should look like:

```
model_data/
├── README.md
├── ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt
├── frozen_inference_graph.pb
└── coco.names
```

## Verification

The server will automatically check for these files on startup. If files are missing, the server will:
- Log a warning
- Fall back to Claude AI detection (if API key is available)
- Or disable automatic detection

## Model Information

- **Model**: SSD MobileNet V3 Large
- **Input Size**: 320x320 pixels
- **Dataset**: COCO (Common Objects in Context)
- **Classes**: 80 object classes (including "person")
- **Framework**: TensorFlow

## Notes

- The model files are large (~25-30 MB total)
- Ensure sufficient disk space before downloading
- The model is optimized for speed and works well on CPU
- Detection threshold is set to 0.4 (configurable in code)
