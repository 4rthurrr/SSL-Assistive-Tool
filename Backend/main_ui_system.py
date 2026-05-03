import sys
import numpy as np
from feture_extract import get_detels
from Predict_realtime import predict_video
import cv2
import time
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QImage
import imutils


# ==========================================
# THREAD 1: LIVE CAMERA (Webcam)
# ==========================================
class LiveCamThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    trigger_received = pyqtSignal()
    prediction_ready_signal = pyqtSignal(object)  # Signal to send prediction to UI

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.trigger_received.connect(self.print_triggered)
        self.recode_video = False
        self.frames_recorded = 0
        self.out = None

    def print_triggered(self):
        print("Live recording triggered!")
        self.frames_recorded = 0  # Reset counter for a fresh recording
        self.recode_video = True

    def cancel_recording(self):
        """Immediately stops recording and discards progress."""
        self.recode_video = False
        self.frames_recorded = 0
        if self.out is not None:
            self.out.release()
            self.out = None

    def run(self):
        # Capture from the first webcam (Index 0)
        cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)

        duration_frames = 135
        output_name = "output.mp4"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        while self._run_flag:
            ret, cv_img = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            org_image, cv_img, feture_cordinate = get_detels(cv_img, anotation=True)

            # --- Recording Logic ---
            if self.recode_video:
                # Initialize VideoWriter only when recording starts
                if self.frames_recorded == 0:
                    self.out = cv2.VideoWriter(output_name, fourcc, fps, (width, height))
                    print(f"Recording {duration_frames} frames to {output_name}...")

                if self.frames_recorded < duration_frames:
                    self.out.write(org_image)
                    self.frames_recorded += 1

                    cv2.putText(cv_img, f"REC: {self.frames_recorded}/{duration_frames}",
                                (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                else:
                    self.out.release()
                    self.out = None
                    self.recode_video = False
                    print("Recording saved successfully. Analyzing...")

                    # Call Prediction
                    ss = predict_video('output.mp4')
                    confidnt_array = ss[3][0]

                    print(f"Prediction Result:\n{confidnt_array}")

                    # Emit the result to the main UI
                    self.prediction_ready_signal.emit(ss)

            # --- Qt Display Logic ---
            rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = qt_image.scaled(480, 270, Qt.KeepAspectRatio)
            self.change_pixmap_signal.emit(p)

        cap.release()

    def stop(self):
        self._run_flag = False
        self.wait()


# ==========================================
# THREAD 2: PRACTICE FEED (Second Cam / Video)
# ==========================================
class PracticeCamThread(QThread):
    change_pixmap_signal = pyqtSignal(QImage)
    Select_Letter_and_show = pyqtSignal(str)
    student_turn = pyqtSignal()

    def __init__(self, source):
        super().__init__()
        self._run_flag = True
        self.no_video = True
        self.video_path = "practis_letters/L1.mp4"
        self._new_video_requested = False
        self.video_loop_count = 0

        self.Select_Letter_and_show.connect(self.Select_Letter_video)

    def Select_Letter_video(self, letter_name):
        print(f"Switching to: {letter_name}")
        mapping = {
            'Letter A': "practis_letters/L1.mp4",
            'Letter B': "practis_letters/L2.mp4",
            'Letter C': "practis_letters/L3.mp4",
            'Letter D': "practis_letters/L4.mp4",
            'Letter E': "practis_letters/L5.mp4",
            'Letter F': "practis_letters/L6.mp4"
        }

        if letter_name in mapping:
            self.video_path = mapping[letter_name]
            self._new_video_requested = True
            self.no_video = False
            self.video_loop_count = 0  # Start loop count fresh for the new letter

    def stop_practice(self):
        """Immediately stops the practice video and returns to standby."""
        self.no_video = True
        self.video_loop_count = 0
        self._new_video_requested = False

    def run(self):
        cap = cv2.VideoCapture(self.video_path)

        while self._run_flag:
            if self._new_video_requested:
                cap.release()
                cap = cv2.VideoCapture(self.video_path)
                self._new_video_requested = False
                print(f"Thread: Now playing {self.video_path}")

            if self.no_video:
                cv_img = cv2.imread('face.jpeg')
                if cv_img is not None:
                    self._emit_image(cv_img)
                time.sleep(0.1)
                continue

            ret, cv_img = cap.read()

            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.video_loop_count += 1
                if self.video_loop_count >= 3:  # Train 3 times
                    self.no_video = True
                    self.student_turn.emit()
                    self.video_loop_count = 0
                continue

            self._emit_image(cv_img)
            time.sleep(0.03)

        cap.release()

    def _emit_image(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = qt_image.scaled(480, 270, Qt.KeepAspectRatio)
        self.change_pixmap_signal.emit(p)

    def stop(self):
        self._run_flag = False
        self.wait()


# ==========================================
# MAIN APPLICATION
# ==========================================
class BlindTrainingSystem(QtWidgets.QDialog):
    def __init__(self):
        super(BlindTrainingSystem, self).__init__()

        try:
            uic.loadUi('dissignerUI.ui', self)
        except FileNotFoundError:
            print("❌ Error: 'dissignerUI.ui' file not found!")
            sys.exit()

        self.live_label = self.findChild(QtWidgets.QLabel, 'Live_video')
        self.practice_label = self.findChild(QtWidgets.QLabel, 'practis_vid')
        self.status_label = self.findChild(QtWidgets.QLabel, 'Display_status')
        self.start_button = self.findChild(QtWidgets.QPushButton, 'pushButton')
        self.stop_button = self.findChild(QtWidgets.QPushButton, 'stopBtn')
        self.letter_list = self.findChild(QtWidgets.QListWidget, 'letter_list')

        self.countdown_timer = QtCore.QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown_label)
        self.counter = 5

        self.start_button.clicked.connect(self.start_training)
        self.stop_button.clicked.connect(self.stop_training)
        self.letter_list.itemClicked.connect(self.handle_letter_selection)

        self.letter = 'no'

        # --- START THREAD 1: LIVE CAM ---
        self.live_thread = LiveCamThread()
        self.live_thread.change_pixmap_signal.connect(self.update_live_feed)
        self.live_thread.prediction_ready_signal.connect(self.display_prediction)  # Connect prediction to UI
        self.live_thread.start()

        # --- START THREAD 2: PRACTICE CAM ---
        self.practice_thread = PracticeCamThread(source=1)
        self.practice_thread.change_pixmap_signal.connect(self.update_practice_feed)
        self.practice_thread.student_turn.connect(self.manage_student_turn)
        self.practice_thread.start()

    def update_live_feed(self, image):
        self.live_label.setPixmap(QPixmap.fromImage(image))

    def update_practice_feed(self, image):
        self.practice_label.setPixmap(QPixmap.fromImage(image))

    def manage_student_turn(self):
        print("Student Turn Started")
        self.counter = 5
        self.status_label.setText(f"Now your turn... {self.counter}")
        self.status_label.setStyleSheet("color: #fab387; font-weight: bold; background-color: #313244; padding: 5px;")
        self.countdown_timer.start(1000)

    def update_countdown_label(self):
        self.counter -= 1

        if self.counter > 0:
            self.status_label.setText(f"Now your turn... {self.counter}")
        else:
            self.status_label.setText("START!")
            self.status_label.setStyleSheet(
                "color: #a6e3a1; font-weight: bold; background-color: #313244; padding: 5px;")
            self.countdown_timer.stop()
            self.live_thread.trigger_received.emit()

    def display_prediction(self, result_object):

        confidnt_array = result_object[3][0]

        class_index = np.argmax(confidnt_array)

        if self.letter == "Letter A":
            confidance = round(confidnt_array[0]*100 , 2)

        elif self.letter == "Letter B":
            confidance = round(confidnt_array[1]*100 , 2)

        elif self.letter == "Letter C":
            confidance = round(confidnt_array[2]*100 , 2)

        elif self.letter == "Letter D":
            confidance = round(confidnt_array[3]*100 , 2)

        elif self.letter == "Letter E":
            confidance = round(confidnt_array[4]*100 , 2)

        elif self.letter == "Letter F":
            confidance = round(confidnt_array[5]*100 , 2)

        elif self.letter == "Letter G":
            confidance = round(confidnt_array[6]*100 , 2)

        elif self.letter == "Letter H":
            confidance = round(confidnt_array[7]*100 , 2)

        elif self.letter == "Letter I":
            confidance = round(confidnt_array[8]*100 , 2)

        #-----------------------------------------------------------------

        if (confidance > 30):
            status_speach = "GOOD JOB ( "
        else:
            status_speach = "Train Again ( "


        # self.status_label.setText(status_speach + str(confidance)+" % )" + str(class_index))
        self.status_label.setText(status_speach + str(confidance) + " % )")
        self.status_label.setStyleSheet(
            "color: #a6e3a1; font-size: 14pt; font-weight: bold; background-color: #313244; padding: 10px; border-radius: 8px;"
        )

    def start_training(self):
        if self.letter == 'no':
            self.status_label.setText("Please select a letter first!")
            return

        # Always ensure systems are reset before starting a fresh run
        self.countdown_timer.stop()
        self.live_thread.cancel_recording()

        self.practice_thread.Select_Letter_and_show.emit(self.letter)
        self.status_label.setText(f"Watch practice video carefully... ({self.letter})")
        self.status_label.setStyleSheet("color: #a6e3a1; font-weight: bold; background-color: #313244; padding: 5px;")

    def stop_training(self):
        print('System reset triggered by Stop button.')

        # 1. Stop the countdown timer
        self.countdown_timer.stop()

        # 2. Cancel active live recording
        self.live_thread.cancel_recording()

        # 3. Stop the practice video and revert to standby image
        self.practice_thread.stop_practice()

        # 4. Reset the UI status
        self.status_label.setText("System Ready... Select Letter and Press Start.")
        self.status_label.setStyleSheet("color: #a6adc8; font-weight: bold; background-color: #313244; padding: 5px;")

        # 5. Reset the selected letter so the user must select again (optional)
        self.letter = 'no'
        self.letter_list.clearSelection()

    def handle_letter_selection(self, item):

        # self.letter = item.text()

        mapper = {
            "Letter - අ": "Letter A",
            "Letter - ඉ": "Letter B",
            "Letter - උ": "Letter C",
            "Letter - ම": "Letter D",
            "Letter - ඔ": "Letter E",
            "Letter - ච": "Letter F",
            "Word - අම්මා": "Letter G",
            "Word - ගස": "Letter H",
            "Word - මල": "Letter I"
        }

        ui_text = item.text()
        self.letter = mapper.get(ui_text, ui_text)

        print("ui_text: " + ui_text + ' - '+ "Maper Text - " + self.letter)

        self.status_label.setText(f"Training Mode: {self.letter}")
        self.status_label.setStyleSheet("color: #89b4fa; font-weight: bold; background-color: #313244; padding: 5px;")

    def closeEvent(self, event):
        print("Stopping threads...")
        self.live_thread.stop()
        self.practice_thread.stop()
        event.accept()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = BlindTrainingSystem()
    window.show()
    sys.exit(app.exec_())