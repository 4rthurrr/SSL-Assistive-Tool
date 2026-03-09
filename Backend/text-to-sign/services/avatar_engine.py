import mediapipe as mp
import numpy as np
from moviepy import VideoFileClip
import cv2
import os
import math

# Initialize MediaPipe Solutions
mp_holistic = mp.solutions.holistic

class AvatarEngine:
    def __init__(self):
        self.holistic = mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )






    def close(self):
        self.holistic.close()



    def render_skeleton(self, frame):
        """
        Renders the MediaPipe skeleton (Pose, Face, Hands) on a black background.
        """
        results = self.holistic.process(frame)
        height, width, _ = frame.shape
        skeleton_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        mp_drawing = mp.solutions.drawing_utils
        mp_drawing_styles = mp.solutions.drawing_styles

        # Draw Pose
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                skeleton_image,
                results.pose_landmarks,
                mp_holistic.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

        # Draw Face Mesh (Tesellation)
        if results.face_landmarks:
            mp_drawing.draw_landmarks(
                skeleton_image,
                results.face_landmarks,
                mp_holistic.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())

        # Draw Hands
        if results.left_hand_landmarks:
            mp_drawing.draw_landmarks(
                skeleton_image,
                results.left_hand_landmarks,
                mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style(),
                connection_drawing_spec=mp_drawing_styles.get_default_hand_connections_style())

        if results.right_hand_landmarks:
            mp_drawing.draw_landmarks(
                skeleton_image,
                results.right_hand_landmarks,
                mp_holistic.HAND_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_hand_landmarks_style(),
                connection_drawing_spec=mp_drawing_styles.get_default_hand_connections_style())

        return skeleton_image

    def extract_landmarks_from_video(self, video_path):
        """
        Extracts MediaPipe Holistic landmarks from a video file.
        Returns a list of frames, where each frame is a dict of landmarks.
        """
        cap = cv2.VideoCapture(video_path)
        landmark_sequence = []
        
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break
                
            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.holistic.process(frame_rgb)
            
            frame_data = {}
            
            def serialize_landmarks(landmarks):
                if not landmarks: return None
                return [{'x': lm.x, 'y': lm.y, 'z': lm.z, 'visibility': lm.visibility} for lm in landmarks.landmark]

            if results.pose_landmarks:
                frame_data['pose'] = serialize_landmarks(results.pose_landmarks)
            if results.pose_world_landmarks:
                frame_data['pose_world'] = serialize_landmarks(results.pose_world_landmarks)
            if results.left_hand_landmarks:
                frame_data['left_hand'] = serialize_landmarks(results.left_hand_landmarks)
            if results.right_hand_landmarks:
                frame_data['right_hand'] = serialize_landmarks(results.right_hand_landmarks)
            if results.face_landmarks:
                 # Face has 468 landmarks, might be heavy. Optional? Keeping it for now.
                 frame_data['face'] = serialize_landmarks(results.face_landmarks)
            
            landmark_sequence.append(frame_data)
            
        cap.release()
        return landmark_sequence

def generate_avatar_video(input_path, output_path, style='skeleton'):
    engine = AvatarEngine()
    clip = None
    new_clip = None
    try:
        print(f"💀 generating skeleton video for {input_path}")
        clip = VideoFileClip(input_path)
        
        # Always use skeleton render
        new_clip = clip.fl_image(engine.render_skeleton)
            
        new_clip.write_videofile(output_path, codec="libx264", audio=False, logger=None)
        return True
    except Exception as e:
        print(f"Error generating avatar: {e}")
        return False
    finally:
        engine.close()
        if clip: clip.close()
        if new_clip: new_clip.close()
