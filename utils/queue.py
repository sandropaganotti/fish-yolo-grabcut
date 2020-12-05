#!/usr/bin/python

from rq import Queue
from dropbox import Dropbox
from dropbox.files import DeletedMetadata, FolderMetadata, WriteMode
from worker import conn
from config import params
from utils import yolo
from PIL import Image
from datetime import datetime
import redis
import sys
import numpy as np
import cv2 as cv
import os
import io

redis_client = redis.from_url(params.REDIS_URL, decode_responses=True)
q = Queue(connection=conn)

def get_token_cursor(accountID):
    if accountID is None:
        return None, None, None
    token = redis_client.hget('tokens', accountID)
    cursor = redis_client.hget('cursors', accountID)
    refresh_token = redis_client.hget('refresh_tokens', accountID)
    return token, cursor, refresh_token

def index_files(accountID):
    token, cursor, refresh_token = get_token_cursor(accountID)
    if token is None:
        return
    
    dbx = Dropbox(token, 
        oauth2_refresh_token = refresh_token, 
        app_key = params.DROPBOX_APP_KEY, 
        app_secret = params.DROPBOX_APP_SECRET,    
    )

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
    token, cursor, refresh_token = get_token_cursor(accountID)
    if token is None:
        return

    dbx = Dropbox(token, 
        oauth2_refresh_token = refresh_token, 
        app_key = params.DROPBOX_APP_KEY, 
        app_secret = params.DROPBOX_APP_SECRET,    
    )

    for entry in entries:
        _, resp = dbx.files_download(entry)
        image_bytes = bytearray(resp.content)

        # 36867 is the exif property for date time
        creation_time = Image.open(io.BytesIO(image_bytes)).getexif().get(36867)
        if creation_time is None:
            creation_time = datetime.now().strftime('%Y:%m:%d %H:%M:%S')

        image = np.asarray(image_bytes, dtype = 'uint8')
        image = cv.imdecode(image, cv.IMREAD_COLOR)

        boxes, idxs, labels = yolo.runYOLOBoundingBoxes(
            image, 
            params.COCO_NAMES_PATH,
            params.YOLO_WEIGHTS_PATH,
            params.YOLO_NETWORK_PATH,
            params.YOLO_CONFIDENCE,
            params.YOLO_THRESHOLD
        )

        if (idxs is None or len(idxs) == 0):
            continue

        for idx in idxs[0]:
            if (labels[idx] in params.YOLO_BLACKLISTED_NAMES):
                continue
            crop_upload_store(
                accountID, 
                dbx, 
                idx,
                entry,
                creation_time,
                image,
                boxes[idx], 
                labels[idx]
            )


def crop_upload_store(accountID, dbx, idx, entry, creation_time, image, box, label):
    x = box[0] if box[0] > 0 else 0 
    y = box[1] if box[1] > 0 else 0
    w = box[2] - (0 if box[0] > 0 else abs(box[0]))
    h = box[3] - (0 if box[1] > 0 else abs(box[1]))
    cropped_image = image[y:y+h, x:x+w]
    is_success, buffer = cv.imencode('.jpg', cropped_image)
    output_file = os.path.basename(entry)[:-3] + '_' + str(idx) + '.jpg'
    output_path = os.path.sep.join([
        params.DROPBOX_OUTPUT_PATH, 
        output_file,
    ])
    dbx.files_upload(
        buffer.tobytes(),
        output_path,               
        mode = WriteMode('overwrite')
    )
    redis_client.hmset(
        accountID + '_' + output_file, 
        {
            'x': x,
            'y': y,
            'creation_time': creation_time,
            'file_path': output_path,
            'label': label
        }
    )


