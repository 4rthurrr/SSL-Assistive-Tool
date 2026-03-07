import cv2
import mediapipe as mp
import numpy as np
import os

class SkeletonGenerator:
    def __init__(self):
        self.mp_holistic = mp.solutions.holistic
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def create_skeleton_video(self, input_video_paths, output_path="skeleton_output.mp4"):
        """
        Reads a list of video clips, extracts landmarks, and draws them on a black canvas.
        Returns the path to the generated skeleton video (Driving Video).
        """
        
        # Initialize MediaPipe Holistic
        holistic = self.mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            refine_face_landmarks=True
        )

        # Output Video Writer Setup
        writer = None
        
        for video_path in input_video_paths:
            if not os.path.exists(video_path):
                print(f"Warning: Video not found {video_path}")
                continue

            cap = cv2.VideoCapture(video_path)
            
            while cap.isOpened():
                success, frame = cap.read()
                if not success:
                    break

                # Convert to RGB for MediaPipe
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = holistic.process(image)

                # Create Black Canvas
                height, width, _ = frame.shape
                black_canvas = np.zeros((height, width, 3), dtype=np.uint8)

                # --- MANNEQUIN DRAWING LOGIC ---
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    
                    # Helper to get coords
                    def get_coords(idx):
                        lm = landmarks[idx]
                        return (int(lm.x * width), int(lm.y * height))

                    # RESEARCH CONTRIBUTION
                    # Custom mannequin avatar rendering from MediaPipe holistic landmarks
                    # Polygon torso fill, dynamic head radius from shoulder width
                    # Color mapping: dark-blue shirt (upper arm) + skin-tone (forearm/head/hands)
                    # Makes skeleton output human-readable for Deaf sign language users
                    # 1. Draw Torso (Shirt)
                    # Shoulders: 11, 12 | Hips: 24, 23
                    s_l, s_r = get_coords(11), get_coords(12)
                    h_r, h_l = get_coords(24), get_coords(23)
                    
                    # Polygon points: Left Shoulder -> Right Shoulder -> Right Hip -> Left Hip
                    torso_pts = np.array([s_l, s_r, h_r, h_l], np.int32)
                    
                    # Color: Dark Blue Shirt (BGR: 139, 0, 0)
                    shirt_color = (139, 0, 0)
                    cv2.fillPoly(black_canvas, [torso_pts], shirt_color)
                    
                    # 2. Draw Head (Neutral Mannequin)
                    nose = get_coords(0)
                    shoulder_width = np.linalg.norm(np.array(s_l) - np.array(s_r))
                    head_radius = int(shoulder_width * 0.35)
                    
                    # Color: Neutral Mannequin Beige (BGR: 195, 176, 145)
                    # Less saturated than the previous pinkish skin
                    skin_color = (195, 176, 145)
                    
                    # Neck (Thick Line connecting Nose area to Mid-Shoulders)
                    mid_shoulder = ((s_l[0] + s_r[0])//2, (s_l[1] + s_r[1])//2)
                    cv2.line(black_canvas, nose, mid_shoulder, skin_color, int(head_radius*0.8), cv2.LINE_AA)
                    
                    # Draw Head Circle (Solid)
                    cv2.circle(black_canvas, nose, head_radius, skin_color, -1) 
                    
                    # (REMOVED CARTOON EYES/MOUTH for Realism)

                    # 3. Draw Limbs (Arms)
                    def draw_limb(p1_idx, p2_idx, color, thickness=15):
                        p1 = get_coords(p1_idx)
                        p2 = get_coords(p2_idx)
                        cv2.line(black_canvas, p1, p2, color, thickness, cv2.LINE_AA)
                        # Joints matching limb color for smooth look
                        cv2.circle(black_canvas, p1, int(thickness/1.6), color, -1)

                    # Arms = Shirt Color (Same as Torso)
                    draw_limb(11, 13, color=shirt_color, thickness=20) 
                    draw_limb(12, 14, color=shirt_color, thickness=20)
                    
                    # Forearms = Skin (Exposed Arms)
                    draw_limb(13, 15, color=skin_color, thickness=16) 
                    draw_limb(14, 16, color=skin_color, thickness=16)

                    # Draw Hands (Realistic Skin Tone)
                    # Removed Neon colors. Using same 'skin_color' as head/forearms.
                    
                    hand_spec = self.mp_drawing.DrawingSpec(color=skin_color, thickness=2, circle_radius=2)
                    conn_spec = self.mp_drawing.DrawingSpec(color=skin_color, thickness=2)

                    self.mp_drawing.draw_landmarks(
                        black_canvas, results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                        landmark_drawing_spec=hand_spec, connection_drawing_spec=conn_spec
                    )
                    self.mp_drawing.draw_landmarks(
                        black_canvas, results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                        landmark_drawing_spec=hand_spec, connection_drawing_spec=conn_spec
                    )

                # Initialize Writer if first frame
                # MOVED OUTSIDE of 'if results.pose_landmarks' to prevent crashes on empty frames
                if writer is None:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    # Sync with app.py FPS (24) to ensure word highlighting matches
                    writer = cv2.VideoWriter(output_path, fourcc, 24.0, (width, height))

                writer.write(black_canvas)

            cap.release()

        if writer:
            writer.release()
            print(f"Skeleton Generation Complete: {output_path}")
            return output_path
        else:
            print("Failed to generate skeleton video.")
            return None

if __name__ == "__main__":
    # Test
    gen = SkeletonGenerator()
    # Dummy paths for testing (User needs to provide real paths)
    # gen.create_skeleton_video(["test.mp4"])
