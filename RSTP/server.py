import cv2
import socket
import time
import struct
import threading
from cryptography.fernet import Fernet

PORTA_RTP = 12345
PORTA_RTSP = 8554
KEY = b'6u0WByv79reW-9G9e_v38-X8X6f7v8B-9v9e_v38-X8='
fernet = Fernet(KEY)

class ServerState:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

class RTPPacket:
    def __init__(self, payload_type, seq_num, timestamp, payload):
        self.version = 2
        self.payload_type = payload_type
        self.seq_num = seq_num
        self.timestamp = timestamp
        self.payload = payload
        
    def get_packet(self):
        header_0 = (self.version << 6)
        header_1 = self.payload_type
        header = struct.pack('!BBHII', header_0, header_1, self.seq_num, self.timestamp, PORTA_RTP)
        return header + self.payload

def stream_worker(video_path, ip_destino):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cap = cv2.VideoCapture(video_path)
    seq_num = 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    intervalo = 1.0 / fps

    while cap.isOpened():
        if ServerState.state == ServerState.PLAYING:
            ret, frame = cap.read()
            if not ret: break
            
            frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            payload_encripted = fernet.encrypt(buffer.tobytes())
            timestamp = int(time.time() * 90000) & 0xFFFFFFFF
            pacote = RTPPacket(26, seq_num, timestamp, payload_encripted)
            
            server_socket.sendto(pacote.get_packet(), (ip_destino, PORTA_RTP))
            seq_num = (seq_num + 1) % 65536
            time.sleep(intervalo)
        elif ServerState.state == ServerState.INIT:
            break
        else:
            time.sleep(0.1) # Pause state

    cap.release()
    server_socket.close()

def iniciar_servidor_rtsp():
    rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rtsp_socket.bind(('0.0.0.0', PORTA_RTSP))
    rtsp_socket.listen(1)
    print(f"Servidor RTSP aguardando em {PORTA_RTSP}...")

    while True:
        conn, addr = rtsp_socket.accept()
        threading.Thread(target=handle_rtsp, args=(conn, addr)).start()

def handle_rtsp(conn, addr):
    print(f"Conexão RTSP de {addr}")
    while True:
        data = conn.recv(1024).decode()
        if not data: break
        
        request = data.split(' ')[0]
        if request == "SETUP":
            ServerState.state = ServerState.READY
            conn.send(b"RTSP/1.0 200 OK\nSession: 123456")
            # Inicia a thread de vídeo
            threading.Thread(target=stream_worker, args=("videoplayback.mp4", addr[0])).start()
        elif request == "PLAY":
            ServerState.state = ServerState.PLAYING
            conn.send(b"RTSP/1.0 200 OK")
        elif request == "PAUSE":
            ServerState.state = ServerState.READY
            conn.send(b"RTSP/1.0 200 OK")
        elif request == "TEARDOWN":
            ServerState.state = ServerState.INIT
            conn.send(b"RTSP/1.0 200 OK")
            break

if __name__ == "__main__":
    iniciar_servidor_rtsp()