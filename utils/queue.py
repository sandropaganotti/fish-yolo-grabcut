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

redis_client = redis.from_url(params.REDIS_URL, decode_responses=True)
q = Queue(connection=conn)

def get_token_cursor(accountID):
    if accountID is None:
        return
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
            result = dbx.files_list_folder(path='')
        else:
            result = dbx.files_list_folder_continue(cursor)
        
        for entry in result.entries:
            # Ignore deleted files, folders, and non-markdown files
            if (isinstance(entry, DeletedMetadata) or
                isinstance(entry, FolderMetadata) or
                not entry.path_lower.endswith('.jpg')):
                continue

            # add to entries array
            entries.append(entry.path_lower)

        # Update cursor
        cursor = result.cursor
        redis_client.hset('cursors', accountID, cursor)

        # Repeat only if there's more to do
        has_more = result.has_more

    print(entries, file = sys.stderr)
    q.enqueue(process_new_images, accountID, entries, job_timeout = '1h') 

# called by the worker through rq
def process_new_images(accountID, entries):
    token, cursor = get_token_cursor(accountID)
    if token is None:
        return

    dbx = Dropbox(token)

    for entry in entries:
        _, resp = dbx.files_download(entry)
        image = np.asarray(bytearray(resp.content), dtype="uint8")
        image = cv.imdecode(image, cv.IMREAD_COLOR)

        boxes, idxs, labels = yolo.runYOLOBoundingBoxes(
            image, 
            params.COCO_NAMES_PATH,
            params.YOLO_WEIGHTS_PATH,
            params.YOLO_NETWORK_PATH,
            params.YOLO_CONFIDENCE,
            params.YOLO_THRESHOLD
        )

        print(labels)
        print(entry)




    