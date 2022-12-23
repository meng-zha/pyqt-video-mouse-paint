import logging
import random
import numpy as np
import cv2

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter, QPixmap, QImage, QPen, QPalette, QPolygon

from src.video import VideoTimer
from src.label import MyLabel
from filterpy.kalman import KalmanFilter

class KalmanFilterTracker(QWidget):
    STATUS_INIT = 0
    STATUS_PLAYING = 1
    STATUS_PAUSE = 2
    def __init__(self, title='', image=None, video_url=''):
        super().__init__()
        self.title = title

        self.status = self.STATUS_INIT
        # video setting
        self.player = cv2.VideoCapture()
        self.video_url = video_url
        self.timer = VideoTimer()
        self.timer.timeSignal.signal[str].connect(self.show_video_images)
        self.set_timer_fps()

        self.playButton = QPushButton()
        self.playButton.setEnabled(True)
        self.playButton.clicked.connect(self.switch_video)

        # drawing setting
        self._drawing = False
        self._image = image
        # init
        self.init_ui()

    def _ndarray_to_qimage(self, arr):
        h, w = arr.shape[:2]
        return QImage(arr.data, w, h, w*3, QImage.Format_RGB888).rgbSwapped()
    
    def _qimage_to_qpixmap(self, qimg):
        return QPixmap.fromImage(qimg)

    def set_timer_fps(self):
        self.player.open(self.video_url)
        fps = self.player.get(cv2.CAP_PROP_FPS)
        self._w = int(self.player.get(cv2.CAP_PROP_FRAME_WIDTH))
        self._h = int(self.player.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self._c = 3
        self.timer.set_fps(fps)
        self.player.release()
    
    def init_ui(self):
        # set windows
        self.setWindowTitle(self.title)
        self.picture = QLabel(self)
        self.panel = MyLabel(parent=self,image=self._image, size=(self._w, self._h, self._c))
        self.panel.resize(self._w, self._h)

        self.resize(self._w, self._h)
        self.picture.resize(self._w, self._h)
        # set image
        if self._image is None:
            self._image = np.zeros((self._w, self._h, self._c), dtype='float32')
        else:
            self._image = cv2.resize(self._image, (self._w, self._h))
        self._image = self._ndarray_to_qimage(self._image)
        self._pixmap = self._qimage_to_qpixmap(self._image)
        self.picture.setPixmap(self._pixmap)

        control_box = QHBoxLayout()
        control_box.setContentsMargins(0, 0, 0, 0)
        control_box.addWidget(self.playButton)
        layout = QVBoxLayout()
        layout.addWidget(self.picture)
        layout.addLayout(control_box)
        self.setLayout(layout)
        self.show()

    def switch_video(self):
        if self.video_url == "" or self.video_url is None:
            return
        if self.status is self.STATUS_INIT:
            self.player.open(self.video_url)
            self.timer.start()
        elif self.status is self.STATUS_PLAYING:
            self.timer.stop()
        elif self.status is self.STATUS_PAUSE:
            self.timer.start()

        self.status = (self.STATUS_PLAYING,
                       self.STATUS_PAUSE,
                       self.STATUS_PLAYING)[self.status]
    def reset(self):
        self.timer.stop()
        self.player.release()
        self.status = self.STATUS_INIT

    def play(self):
        if self.video_url == "" or self.video_url is None:
            return
        if not self.player.isOpened():
            self.player.open(self.video_url)
        self.timer.start()
        self.status = self.STATUS_PLAYING

    def stop(self):
        if self.video_url == "" or self.video_url is None:
            return
        if self.player.isOpened():
            self.timer.stop()
        self.status = self.STATUS_PAUSE

    def show_video_images(self):
        if self.player.isOpened():
            success, frame = self.player.read()
            if success:
                height, width = frame.shape[:2]
                if frame.ndim == 3:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                elif frame.ndim == 2:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

                temp_image = QImage(rgb.flatten(), width, height, QImage.Format_RGB888)
                temp_pixmap = QPixmap.fromImage(temp_image)
                self.picture.setPixmap(temp_pixmap)
            else:
                print("read failed, no frame data")
                success, frame = self.player.read()
                if not success:
                    print("play finished")  # 判断本地文件播放完毕
                    self.reset()
                return
        else:
            print("open file or capturing device error, init again")
            self.reset()



if __name__ == '__main__':
    import sys
    from utils import log_handler
    app = QApplication(sys.argv)
    viewer = KalmanFilterTracker()
    log_handler(viewer.logger)
    app.exec()
