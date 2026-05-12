import socket
import struct
import numpy as np
import cv2
import threading
import tkinter as tk
from cryptography.fernet import Fernet

KEY = b'6u0WByv79reW-9G9e_v38-X8X6f7v8B-9v9e_v38-X8='
fernet = Fernet(KEY)

class RTSPClient:
    def __init__(self, master, ip="127.0.0.1"):
        self.master = master
        self.ip = ip
        self.rtsp_port = 8554
        self.rtp_port = 12345
        self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtsp_socket.connect((self.ip, self.rtsp_port))
        
        self.setup_gui()
        self.stop_rtp = False

    def setup_gui(self):
        self.master.title("Controle RTSP/RTP")
        
        tk.Button(self.master, text="SETUP", command=self.send_setup, width=15).pack(pady=5)
        tk.Button(self.master, text="PLAY", command=self.send_play, width=15).pack(pady=5)
        tk.Button(self.master, text="PAUSE", command=self.send_pause, width=15).pack(pady=5)
        tk.Button(self.master, text="TEARDOWN", command=self.send_teardown, width=15).pack(pady=5)

    def send_setup(self):
        self.rtsp_socket.send(b"SETUP rtsp://server/video RTSP/1.0")
        print(self.rtsp_socket.recv(1024).decode())
        threading.Thread(target=self.receive_rtp, daemon=True).start()

    def send_play(self):
        self.rtsp_socket.send(b"PLAY rtsp://server/video RTSP/1.0")

    def send_pause(self):
        self.rtsp_socket.send(b"PAUSE rtsp://server/video RTSP/1.0")

    def send_teardown(self):
        self.rtsp_socket.send(b"TEARDOWN rtsp://server/video RTSP/1.0")
        self.stop_rtp = True
        self.master.destroy()

    def receive_rtp(self):
        rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        rtp_socket.bind(('0.0.0.0', self.rtp_port))
        
        while not self.stop_rtp:
            try:
                rtp_socket.settimeout(1.0)
                data, addr = rtp_socket.recvfrom(65535)
                if len(data) < 12: continue
                
                payload = data[12:]
                payload_decrypted = fernet.decrypt(payload)
                nparr = np.frombuffer(payload_decrypted, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    cv2.imshow('Streaming RTP - Controlado', frame)
                    cv2.waitKey(1)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Erro: {e}")
        
        cv2.destroyAllWindows()
        rtp_socket.close()

if __name__ == "__main__":
    root = tk.Tk()
    client = RTSPClient(root)
    root.mainloop()