import math
from pathlib import Path
from urllib.request import urlretrieve

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision




_FACE_LANDMARKER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/latest/face_landmarker.task"
)
_FACE_LANDMARKER_MODEL_PATH = Path(__file__).resolve().with_name("assets") / "face_landmarker.task"
_FACE_LANDMARKER = None


def _get_face_landmarker():
    global _FACE_LANDMARKER

    if _FACE_LANDMARKER is not None:
        return _FACE_LANDMARKER

    if not _FACE_LANDMARKER_MODEL_PATH.exists():
        _FACE_LANDMARKER_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(_FACE_LANDMARKER_MODEL_URL, _FACE_LANDMARKER_MODEL_PATH)

    options = vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=str(_FACE_LANDMARKER_MODEL_PATH)
        ),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    _FACE_LANDMARKER = vision.FaceLandmarker.create_from_options(options)
    return _FACE_LANDMARKER

# 2. Start Video Capture
# cap = cv2.VideoCapture(0)

print("Press 'q' to exit.")

def get_detels(image , anotation=True):


    # Get image dimensions to convert normalized coordinates to pixels
    img_h, img_w, _ = image.shape

    # Flip for selfie-view
    # image = cv2.flip(image, 1)

    # 3. Convert Color (BGR -> RGB)
    image.flags.writeable = False
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # 4. Process the image (Inference)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
    results = _get_face_landmarker().detect(mp_image)

    # 5. Draw the Mesh
    image.flags.writeable = True
    # Note: We draw on the original BGR 'image', not the RGB one

    calc_img = image.copy()
    orginal_img = image.copy()

    try:
        def eyesMid(p33, p133, p362, p263):
            """
            Calculates the middle point (x, y) for both eyes based on corner landmarks.

            Args:
                p33  (tuple/array): Right Eye Outer Corner (x, y)
                p133 (tuple/array): Right Eye Inner Corner (x, y)
                p362 (tuple/array): Left Eye Inner Corner (x, y)
                p263 (tuple/array): Left Eye Outer Corner (x, y)

            Returns:
                tuple: ((right_eye_mid_x, right_eye_mid_y), (left_eye_mid_x, left_eye_mid_y))
            """

            # 1. Calculate Right Eye Midpoint (Average of 33 and 133)
            # Using integer division // to ensure pixel coordinates are integers
            right_mid_x = int((p33[0] + p133[0]) / 2)
            right_mid_y = int((p33[1] + p133[1]) / 2)

            # 2. Calculate Left Eye Midpoint (Average of 362 and 263)
            left_mid_x = int((p362[0] + p263[0]) / 2)
            left_mid_y = int((p362[1] + p263[1]) / 2)

            eyes_distance = math.dist((right_mid_x, right_mid_y), (left_mid_x, left_mid_y))

            return ((right_mid_x, right_mid_y), (left_mid_x, left_mid_y) , eyes_distance)


        def nozMid(p8 ,p2 , p0 , p17):

            # print('awaa')

            mouth_mid_x = int((p0[0] + p17[0]) / 2)
            mouth_mid_y = int((p0[1] + p17[1]) / 2)

            # in this case i got noz length as standed unit length Y
            noz_y = math.dist(p8,p2)

            return mouth_mid_x, mouth_mid_y , noz_y



        def calculate_distance_matrix(landmarks_np,mouth_mid_x, mouth_mid_y ,eyes_distance_x, noz_distance_y,anotation):

            OUTER_LIP = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 146, 91, 181, 84, 17, 314, 405, 321, 375]
            INNER_LIP = [78, 191, 80, 81, 82, 13, 312, 311, 310, 415, 308, 95, 88, 178, 87, 14, 317, 402, 318, 324]

            data_matrix = []

            for x in OUTER_LIP:

                if anotation:
                    cv2.circle(calc_img, landmarks_np[x], 3, (255, 0, 0), -1)

                x1 , y1 = landmarks_np[x]
                X = ((x1 - mouth_mid_x)/eyes_distance_x)
                Y = ((y1 - mouth_mid_y)/noz_distance_y)
                distance  = math.sqrt((X**2) + (Y**2))

                data_matrix.append(distance)


            for x in INNER_LIP:

                if anotation:
                    cv2.circle(calc_img, landmarks_np[x], 3, (0, 255, 0), -1)

                x1, y1 = landmarks_np[x]
                X = ((x1 - mouth_mid_x) / eyes_distance_x)
                Y = ((y1 - mouth_mid_y) / noz_distance_y)
                distance = math.sqrt(X ** 2 + Y ** 2)

                data_matrix.append(distance)

            return data_matrix


        if results.face_landmarks:
            face_landmarks = results.face_landmarks[0]

            landmark_points = []
            for landmark in face_landmarks:
                x = int(landmark.x * img_w)
                y = int(landmark.y * img_h)
                landmark_points.append([x, y])

            # Convert list to NumPy array (Shape: [478, 2])
            landmarks_np = np.array(landmark_points)

            # print(f"Array Shape: {landmarks_np.shape} \n\n")
            # print(landmarks_np)
            # print('===============================================')

            p33 = landmarks_np[33]
            p133 = landmarks_np[133]
            p362 = landmarks_np[362]
            p263 = landmarks_np[263]

            right_mid, left_mid , eyes_distance_x = eyesMid(p33, p133, p362, p263)

            p2 = landmarks_np[2]
            p8 = landmarks_np[8]
            p0 = landmarks_np[0]
            p17 = landmarks_np[17]

            mouth_x , mouth_y , noz_distance_y = nozMid(p8 ,p2 , p0 , p17)


            # i tested all calculation both reference x and y QA pass
            # print("y======= ",noz_distance_y)
            # print("x======= ", eyes_distance_x)

            feture_destance_matrix = calculate_distance_matrix(landmarks_np ,mouth_x, mouth_y ,eyes_distance_x, noz_distance_y, anotation)


            if anotation:
                # ====================== test anotations ===============================

                for point in landmarks_np:
                    cv2.circle(calc_img, tuple(point), 1, (255, 0, 0), -1)

                cv2.circle(calc_img, tuple(landmarks_np[33]), 3, (255, 0, 0), -1)
                cv2.circle(calc_img, tuple(landmarks_np[133]), 3, (255, 0, 0), -1)
                cv2.circle(calc_img, tuple(landmarks_np[362]), 3, (255, 0, 0), -1)
                cv2.circle(calc_img, tuple(landmarks_np[263]), 3, (255, 0, 0), -1)

                cv2.circle(calc_img, right_mid, 3, (0, 0, 255), -1)
                cv2.circle(calc_img, left_mid, 3, (0, 0, 255), -1)

                cv2.line(calc_img, right_mid, left_mid, (0, 255, 0), 1)

                cv2.circle(calc_img, tuple(landmarks_np[17]), 3, (255, 0, 0), -1)
                cv2.circle(calc_img, tuple(landmarks_np[0]), 3, (255, 0, 0), -1)

                cv2.circle(calc_img, tuple(landmarks_np[2]), 3, (0, 0, 255), -1)
                cv2.circle(calc_img, (mouth_x , mouth_y), 3, (0, 0, 255), -1)

                # cv2.line(calc_img, (mouth_x , mouth_y), landmarks_np[2], (0, 255, 0), 1)

                cv2.circle(calc_img, tuple(landmarks_np[8]), 3, (0, 0, 255), -1)
                cv2.line(calc_img, tuple(landmarks_np[2]), tuple(landmarks_np[8]), (0, 255, 0), 1)

                # cv2.imshow('MediaPipe Face Mesh', image)

                cv2.waitKey(1)
            # ====================== test anotations ===============================

        return orginal_img, calc_img, [1, eyes_distance_x , noz_distance_y ,mouth_x , mouth_y, feture_destance_matrix]

    except:
        return orginal_img, calc_img, [-1]
