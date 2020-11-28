#!/usr/bin/python

from rq import Queue
from dropbox import Dropbox
from dropbox.files import DeletedMetadata, FolderMetadata, WriteMode
from worker import conn
from config import params
from utils import yolo
import redis
import sys
import numpy as np
import cv2 as cv
import os

redis_client = redis.from_url(params.REDIS_URL, decode_responses=True)
q = Queue(connection=conn)

def get_token_cursor(accountID):
    if accountID is None:
        return None, None
    token = redis_client.hget('tokens', accountID)
    cursor = redis_client.hget('cursors', accountID)
    return token, cursor

def index_files(accountID):
    token, cursor = get_token_cursor(accountID)
    if token is None:
        return
    
    dbx = Dropbox(token)
    has_more = True
    entries = []

    while has_more:
        if cursor is None:
            result = dbx.files_list_folder(path=params.DROPBOX_INPUT_PATH)
        else:
            result = dbx.files_list_folder_continue(cursor)
        
        for entry in result.entries:
            # Ignore deleted files, folders, and non-markdown files
            if (isinstance(entry, DeletedMetadata) or
                isinstance(entry, FolderMetadata) or
                not entry.path_lower.endswith('.jpg') or
                not entry.path_lower.startswith(params.DROPBOX_INPUT_PATH)):
                continue

            # add to entries array
            entries.append(entry.path_lower)

        # Update cursor
        cursor = result.cursor
        redis_client.hset('cursors', accountID, cursor)

        # Repeat only if there's more to do
        has_more = result.has_more

    q.enqueue(process_new_images, accountID, entries, job_timeout = '1h') 

# called by the worker through rq
def process_new_images(accountID, entries):
    token, cursor = get_token_cursor(accountID)
    if token is None:
        return

    dbx = Dropbox(token)

    for entry in entries:
        _, resp = dbx.files_download(entry)
        image = np.asarray(bytearray(resp.content), dtype = 'uint8')
        image = cv.imdecode(image, cv.IMREAD_COLOR)

        boxes, idxs, labels = yolo.runYOLOBoundingBoxes(
            image, 
            params.COCO_NAMES_PATH,
            params.YOLO_WEIGHTS_PATH,
            params.YOLO_NETWORK_PATH,
            params.YOLO_CONFIDENCE,
            params.YOLO_THRESHOLD
        )

        for idx in idxs[0]:
            if (labels[idx] in params.YOLO_BLACKLISTED_NAMES):
                continue
            x = boxes[idx][0] if boxes[idx][0] > 0 else 0 
            y = boxes[idx][1] if boxes[idx][1] > 0 else 0
            w = boxes[idx][2] - (0 if boxes[idx][0] > 0 else abs(boxes[idx][0]))
            h = boxes[idx][3] - (0 if boxes[idx][1] > 0 else abs(boxes[idx][1]))
            print([x,y,w,h, boxes[idx], entry, labels[idx], os.path.sep.join([params.DROPBOX_OUTPUT_PATH, entry[:-3] + '_' + str(idx) + '.jpg'])], file = sys.stderr)
            cropped_image = image[y:y+h, x:x+w]
            is_success, buffer = cv.imencode('.jpg', cropped_image)
            dbx.files_upload(
                buffer.tobytes(),
                os.path.sep.join([
                    params.DROPBOX_OUTPUT_PATH, 
                    os.path.basename(entry)[:-3] + '_' + str(idx) + '.jpg',
                ]),
                mode = WriteMode('overwrite')
            )
