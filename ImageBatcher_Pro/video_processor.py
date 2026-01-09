#影片截圖
import cv2
from PIL import Image

class VideoProcessor:
    """使用 OpenCV 處理影片載入和畫面擷取。"""
    
    def __init__(self):
        self.cap = None
        self.total_frames = 0
        self.fps = 0
        self.duration = 0
        
    def load_video(self, file_path):
        """載入影片檔案。"""
        if self.cap:
            self.cap.release()
            
        self.cap = cv2.VideoCapture(file_path)
        if not self.cap.isOpened():
            raise ValueError("Could not open video file")
            
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        if self.fps > 0:
            self.duration = self.total_frames / self.fps
        else:
            self.duration = 0
            
        return {
            "total_frames": self.total_frames,
            "fps": self.fps,
            "duration": self.duration
        }

    def get_frame(self, frame_index):
        """擷取特定影格並轉換為 PIL 圖片。"""
        if not self.cap or not self.cap.isOpened():
            return None
            
        # Set position
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = self.cap.read()
        
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        return None

    def get_next_frame(self):
        """擷取下一個影格而不重新搜尋（用於迴圈）。"""
        if not self.cap or not self.cap.isOpened():
            return None, -1
            
        ret, frame = self.cap.read()
        if ret:
            # Get current frame index
            idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) - 1
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb), idx
        return None, -1


    def release(self):
        """釋放影片資源。"""
        if self.cap:
            self.cap.release()
