"""
@Author: John T
@LinkedIn: www.linkedin.com/in/john-tavolacci
@Github: https://github.com/johnbikes/
@Date: 2025-06-07
@Description: A set of functions with a global InisghtFace FaceAnalysis instance for comparing faces from two URLs.
@License: Apache License 2.0
"""

import urllib
import logging

import cv2
import numpy as np
import insightface
from insightface.app import FaceAnalysis
from insightface.data import get_image as ins_get_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
app = FaceAnalysis(providers=providers, allowed_modules=['detection', 'recognition'])
app.prepare(ctx_id=0, det_size=(640, 640))

def grab_from_url(url):
    """
    Downloads and decodes an image from a URL into a numpy array.
    
    Args:
        url (str): URL of the image to download
        
    Returns:
        numpy.ndarray: Decoded image in BGR format (OpenCV default)
    """
    # so: https://stackoverflow.com/questions/21061814/how-can-i-read-an-image-from-an-internet-url-in-python-cv2-scikit-image-and-mah
    req = urllib.request.urlopen(url)
    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
    img = cv2.imdecode(arr, -1) # 'Load it as it is'
    return img

def get_feats(url):
    """
    Extracts face features from an image URL using InsightFace.
    
    Args:
        url (str): URL of the image containing a face
        
    Returns:
        numpy.ndarray: Normalized face embedding vector if a face is detected, None otherwise
    """
    try:
        img = grab_from_url(url)
        faces = app.get(img)
        if len(faces) < 1:
            logger.warning(f"No face detected in {url}")
            return None
        return faces[0].normed_embedding
    except Exception as e:
        logger.error(f"Error getting features from {url}: {e}")
        return None

def is_same(url1, url2):
    logger.info(f"Checking is_same for {url1 = }, {url2 = }")
    feats1 = get_feats(url1)
    feats2 = get_feats(url2)
    
    resp = [False, None, None]
    if feats1 is not None:
       resp[1] = (url1, feats1)
    if feats2 is not None:
        resp[2] = (url2, feats2)
    
    if None in resp:
        logger.warning(f"No face detected in {url1} or {url2}. Not comparing features")
    else:
        # actually do the comparison now
        resp[0] = np.dot(feats1, feats2) >= 0.5

    return resp

def main():
    logger.info(f"Comparing {url1} and {url2}")
    logger.info(f"Is same: {is_same(url1, url2)[0]}")

if __name__ == "__main__":
    # diff
    url1 = 'https://upload.wikimedia.org/wikipedia/commons/c/c1/Lionel_Messi_20180626.jpg'
    url2 = 'https://upload.wikimedia.org/wikipedia/commons/8/8c/Cristiano_Ronaldo_2018.jpg'
    main()

    # change to same
    url2 = 'https://upload.wikimedia.org/wikipedia/commons/2/26/Leo_messi_barce_2005.jpg'
    main()

    # neymar
    url1 = 'https://live.staticflickr.com/8778/17145642931_56ea3a6113_b.jpg'
    url2 = 'https://live.staticflickr.com/8778/17145642931_56ea3a6113_b.jpg'
    main()