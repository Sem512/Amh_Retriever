"""Runs one photo through the lanes: clean -> read -> to_sentences -> translate (ARCHITECTURE.md section 3).

run() returns (image, segments): `image` is the array every box refers to, and each segment is
{"amharic": str, "english": str, "boxes": [(left, top, width, height), ...]} in pixels of `image`.
"""
import cv2

MAX_SIDE = 2500


def run(photo, mode):
    # shortcut: fixed sample so the frontend can build against the real contract; replace with
    # clean()/read_page()/to_sentences()/translate() once Kibreab's and Ferid's functions land (week 2)
    scale = min(1.0, MAX_SIDE / max(photo.shape[:2]))
    image = cv2.resize(photo, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else photo
    h, w = image.shape[:2]
    return image, [{
        "amharic": "ይህ የሙከራ ውጤት ነው።",
        "english": "This is a test result.",
        "boxes": [(w // 10, h // 10, w * 8 // 10, h // 20)],
    }]
