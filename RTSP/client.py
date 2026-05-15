import sys
import socket
import numpy as np
import cv2
import threading
import tkinter as tk
import pyaudio
from utils import *

class RTSPClient:
    def __init__(self, master, ip="127.0.0.1", porta_video=PORTA_RTP_VIDEO, porta_audio=PORTA_RTP_AUDIO):
        self.master = master
        self.ip = ip
        self.porta_video = porta_video
        self.porta_audio = porta_audio

        self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtsp_socket.connect((self.ip, PORTA_RTSP))
        self.stop_rtp = False
        self.is_setup = False
        
        # Setup Áudio
        self.p = pyaudio.PyAudio()
        self.audio_stream = self.p.open(format=pyaudio.paInt16, channels=2, rate=44100, output=True, frames_per_buffer=4096)
        
        self.setup_gui()

    def setup_gui(self):
        self.master.title(f"Cliente ({self.porta_video}/{self.porta_audio})")
        for cmd in ["SETUP", "PLAY", "PAUSE", "TEARDOWN"]:
            tk.Button(self.master, text=cmd, command=getattr(self, f"send_{cmd.lower()}"), width=15).pack(pady=5)

    def send_setup(self):
        if self.is_setup:
            print("Setup já foi realizado.")
            return
            
        self.is_setup = True

        mensagem = f"SETUP {self.porta_video} {self.porta_audio}"

        self.rtsp_socket.send(mensagem.encode())
        print(self.rtsp_socket.recv(1024).decode())
        threading.Thread(target=self.receive_video, daemon=True).start()
        threading.Thread(target=self.receive_audio, daemon=True).start()

    def receive_video(self):
        video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        video_socket.bind(('0.0.0.0', self.porta_video))
        while not self.stop_rtp:
            try:
                data, _ = video_socket.recvfrom(65535)
                payload = fernet.decrypt(data[12:])
                frame = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    cv2.imshow(f'Video - Porta {self.porta_video}', frame)
                    cv2.waitKey(1)
            except: continue

    def receive_audio(self):
        audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        audio_socket.bind(('0.0.0.0', self.porta_audio))
        while not self.stop_rtp:
            try:
                data, _ = audio_socket.recvfrom(8192)
                self.audio_stream.write(fernet.decrypt(data))
            except: continue

    def send_play(self): self.rtsp_socket.send(b"PLAY")
    def send_pause(self): self.rtsp_socket.send(b"PAUSE")
    def send_teardown(self):
        self.rtsp_socket.send(b"TEARDOWN")
        self.stop_rtp = True
        self.master.destroy()

if __name__ == "__main__":
    porta_v = int(sys.argv[1]) if len(sys.argv) > 1 else PORTA_RTP_VIDEO
    porta_a = int(sys.argv[2]) if len(sys.argv) > 2 else PORTA_RTP_AUDIO

    root = tk.Tk()
    client = RTSPClient(root, porta_video=porta_v, porta_audio=porta_a)
    root.mainloop()