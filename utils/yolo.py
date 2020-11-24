#!/usr/bin/python

import numpy as np
import argparse
import time
import cv2 as cv
import os
import requests

def count_words_at_url(url):
    resp = requests.get(url)
    return len(resp.text.split())

def runYOLOBoundingBoxes(image, yolopath, _confidence, _threshold):
    # load all paths
    labelsPath = os.path.sep.join([yolopath, "coco.names"])
    weightsPath = os.path.sep.join([yolopath, "yolov3-tiny.weights"])
    configPath = os.path.sep.join([yolopath, "yolov3-tiny.cfg"])

    # fetch all labels
    LABELS = open(labelsPath).read().strip().split("\n")
    np.random.seed(0)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
        dtype="uint8")

    # load my YOLO object detector trained on my fish dataset (1 class)
    net = cv.dnn.readNetFromDarknet(configPath, weightsPath)

    # grab input image's spatial dimensions
    (H, W) = image.shape[:2]

    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    # NOTE: (608, 608) is my YOLO input image size. However, using 
    # (416, 416) results in much accutate result. Pretty interesting.
    blob = cv.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
        swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    end = time.time()

    # initialize out lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []
    labels = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater then the minimum probability
            if confidence > _confidence:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update out list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                labels.append(LABELS[classID])

    # apply non-maxima suppression to suppress weark and overlapping bounding
    # boxes
    idxs = cv.dnn.NMSBoxes(boxes, confidences, _confidence,
        _threshold)

    return boxes, idxs, labels
