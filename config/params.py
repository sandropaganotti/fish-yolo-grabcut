#!/usr/bin/python

import os

REDIS_URL = os.getenv('REDISTOGO_URL', 'redis://redis:6379')

COCO_NAMES_PATH = os.path.sep.join(['./config', 'coco.names'])
YOLO_WEIGHTS_PATH = os.path.sep.join(['./config', "yolov3.weights"])
YOLO_NETWORK_PATH = os.path.sep.join(['./config', "yolov3.cfg"]) 

SAMPLE_IMAGE_NAME = 'sample.jpg'
SAMPLE_IMAGE_PATH = os.path.sep.join(["./static", SAMPLE_IMAGE_NAME])

FLASK_PORT = int(os.environ.get('PORT', 5000))
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')

DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')

YOLO_CONFIDENCE = 0.25
YOLO_THRESHOLD = 0.45