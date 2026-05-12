import socket
import numpy as np
import cv2
import threading
import tkinter as tk
import pyaudio
from utils import *

class RTSPClient:
    def __init__(self, master, ip="127.0.0.1"):
        self.master = master
        self.ip = ip
        self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtsp_socket.connect((self.ip, PORTA_RTSP))
        self.stop_rtp = False
        
        # Setup Áudio
        self.p = pyaudio.PyAudio()
        self.audio_stream = self.p.open(format=pyaudio.paInt16, channels=2, rate=44100, output=True, frames_per_buffer=4096)
        
        self.setup_gui()

    def setup_gui(self):
        self.master.title("Cliente Redes II")
        for cmd in ["SETUP", "PLAY", "PAUSE", "TEARDOWN"]:
            tk.Button(self.master, text=cmd, command=getattr(self, f"send_{cmd.lower()}"), width=15).pack(pady=5)

    def send_setup(self):
        self.rtsp_socket.send(b"SETUP rtsp://server/video RTSP/1.0")
        print(self.rtsp_socket.recv(1024).decode())
        threading.Thread(target=self.receive_video, daemon=True).start()
        threading.Thread(target=self.receive_audio, daemon=True).start()

    def receive_video(self):
        video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        video_socket.bind(('0.0.0.0', PORTA_RTP_VIDEO))
        while not self.stop_rtp:
            try:
                data, _ = video_socket.recvfrom(65535)
                payload = fernet.decrypt(data[12:])
                frame = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow('Video', frame)
                    cv2.waitKey(1)
            except: continue

    def receive_audio(self):
        audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        audio_socket.bind(('0.0.0.0', PORTA_RTP_AUDIO))
        while not self.stop_rtp:
            try:
                data, _ = audio_socket.recvfrom(8192)
                self.audio_stream.write(fernet.decrypt(data))
            except: continue

    def send_play(self): self.rtsp_socket.send(b"PLAY RTSP/1.0")
    def send_pause(self): self.rtsp_socket.send(b"PAUSE RTSP/1.0")
    def send_teardown(self):
        self.rtsp_socket.send(b"TEARDOWN RTSP/1.0")
        self.stop_rtp = True
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    client = RTSPClient(root)
    root.mainloop()