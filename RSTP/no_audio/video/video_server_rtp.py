import cv2
import socket
import time
import struct
from cryptography.fernet import Fernet

porta = 1234
KEY = b'6u0WByv79reW-9G9e_v38-X8X6f7v8B-9v9e_v38-X8=' # Chave exemplo 32 bytes base64
fernet = Fernet(KEY)

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
        header = struct.pack('!BBHII', header_0, header_1, self.seq_num, self.timestamp, porta)
        return header + self.payload
    
def stream_video(video_path, ip_destino, porta_destino):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xBB) # QoS
    
    cap = cv2.VideoCapture(video_path)
    seq_num = 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    intervalo = 1.0 / fps
    
    print(f"Iniciando streaming de {video_path} a {fps} FPS...")
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            frame = cv2.resize(frame, (640, 480)) #64kb e 480p
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50]) # Transforma o frame para JPEG com 50% da qualidade
            payload = buffer.tobytes()
            payload_encripted = fernet.encrypt(payload) # Segurança de pacotes
        
            timestamp = int(time.time() * 90000) & 0xFFFFFFFF # Timestamp de 90kHz (padrão de vídeo)
            
            pacote = RTPPacket(26, seq_num, timestamp, payload_encripted) # PT 26 = JPEG
            
            if len(payload) <= 65507:
                server_socket.sendto(pacote.get_packet(), (ip_destino, porta_destino))
            
            seq_num = (seq_num + 1) % 65536
            time.sleep(intervalo)
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        cap.release()
        server_socket.close()
        print("Streaming finalizado.")

if __name__ == "__main__":
    stream_video("videoplayback.mp4", "127.0.0.1", porta)