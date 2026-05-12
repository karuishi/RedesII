import cv2
import socket
import time
import wave
import threading
from utils import *

def video_stream_worker(video_path, ip_destino):
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cap = cv2.VideoCapture(video_path)
    seq_num = 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    
    while cap.isOpened():
        if ServerState.state == ServerState.PLAYING:
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret: break
            
            frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            
            payload = fernet.encrypt(buffer.tobytes())
            timestamp = int(time.time() * 90000) & 0xFFFFFFFF
            pacote = RTPPacket(26, seq_num, timestamp, payload)
            video_socket.sendto(pacote.get_packet(), (ip_destino, PORTA_RTP_VIDEO))
            
            seq_num = (seq_num + 1) % 65536
            elapsed_time = time.time() - start_time
            sleep_time = max(0, (1.0 / fps) - elapsed_time)
            time.sleep(sleep_time)
        elif ServerState.state == ServerState.INIT: break
        else: time.sleep(0.1)
    cap.release()

def audio_stream_worker(audio_path, ip_destino):
    audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    wf = wave.open(audio_path, 'rb')
    chunk_size = 1024
    delay = chunk_size / float(wf.getframerate())

    while True:
        if ServerState.state == ServerState.PLAYING:
            data = wf.readframes(chunk_size)
            if not data: break
            payload = fernet.encrypt(data)
            audio_socket.sendto(payload, (ip_destino, PORTA_RTP_AUDIO))
            time.sleep(delay)
        elif ServerState.state == ServerState.INIT: break
        else: time.sleep(0.1)
    wf.close()

def handle_rtsp(conn, addr):
    print(f"Conexão RTSP de {addr}")
    while True:
        data = conn.recv(1024).decode()
        if not data: break
        request = data.split(' ')[0]

        if request == "SETUP":
            ServerState.state = ServerState.READY
            conn.send(b"RTSP/1.0 200 OK\nSession: 123456")
            threading.Thread(target=video_stream_worker, args=("videoplayback.mp4", addr[0])).start()
            threading.Thread(target=audio_stream_worker, args=("audio.wav", addr[0])).start()
        elif request in ["PLAY", "PAUSE", "TEARDOWN"]:
            if request == "PLAY": ServerState.state = ServerState.PLAYING
            elif request == "PAUSE": ServerState.state = ServerState.READY
            elif request == "TEARDOWN": ServerState.state = ServerState.INIT
            conn.send(b"RTSP/1.0 200 OK")
            if request == "TEARDOWN": break

if __name__ == "__main__":
    rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rtsp_socket.bind(('0.0.0.0', PORTA_RTSP))
    rtsp_socket.listen(1)
    print(f"Servidor Iniciado...")
    while True:
        conn, addr = rtsp_socket.accept()
        threading.Thread(target=handle_rtsp, args=(conn, addr)).start()