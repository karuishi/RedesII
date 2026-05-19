import cv2
import socket
import time
import wave
import threading
import numpy as np
from moviepy import AudioFileClip
from utils import *

class ClientSession:
    def __init__(self):
        self.state = ServerState.INIT

def video_stream_worker(video_path, ip_destino, porta_destino, session):
    video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    cap = cv2.VideoCapture(video_path)
    seq_num = 0
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    
    while cap.isOpened():
        if session.state == ServerState.PLAYING:
            start_time = time.time()
            
            ret, frame = cap.read()
            if not ret: break
            
            frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            
            payload = fernet.encrypt(buffer.tobytes())
            timestamp = int(time.time() * 90000) & 0xFFFFFFFF
            pacote = RTPPacket(26, seq_num, timestamp, payload)

            video_socket.sendto(pacote.get_packet(), (ip_destino, porta_destino))  

            seq_num = (seq_num + 1) % 65536
            elapsed_time = time.time() - start_time
            sleep_time = max(0, (1.0 / fps) - elapsed_time)
            time.sleep(sleep_time)
        elif session.state == ServerState.INIT: break
        else: time.sleep(0.1)
    cap.release()

def audio_stream_worker(video_path, ip_destino, porta_destino, session):
    audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # carregando a faixa de audio do arquivo de video
    audio_clip = AudioFileClip(video_path)
    fps_audio = 44100
    chunk_size = 1024
    delay = chunk_size / float(fps_audio)

    # extrai todo o áudio de uma vez
    audio_array = audio_clip.to_soundarray(fps=fps_audio)
    audio_clip.close()

    # Passa o array de floats para int16 (formato esperado pelo cliente pyaudio)
    pcm16_audio = np.int16(audio_array * 32767)
    total_frames = len(pcm16_audio)
    
    idx = 0
    seq_num = 0 #inicalização do numero de sequencia
    
    while True:
        if session.state == ServerState.PLAYING:
            if idx >= total_frames:
                break # fim do áudio
                
            # recorta o chunk atual manualmente
            fim = min(idx + chunk_size, total_frames)
            data_chunk = pcm16_audio[idx:fim]
            
            payload = fernet.encrypt(data_chunk.tobytes())
            
            #criando o cabeçalho RTP para o audio
            timestamp = int(time.time() * 44100) & 0xFFFFFFFF
            pacote = RTPPacket(97, seq_num, timestamp, payload)

            audio_socket.sendto(pacote.get_packet(), (ip_destino, porta_destino))
            
            seq_num = (seq_num + 1) % 65536
            idx += chunk_size
            time.sleep(delay)
            
        elif session.state == ServerState.INIT: 
            break
        else: 
            # Pausado
            time.sleep(0.1)

def handle_rtsp(conn, addr):
    print(f"Conexão RTSP de {addr}")
    session = ClientSession()

    while True:
        data = conn.recv(1024).decode()
        if not data: break

        parts = data.split(' ')
        request = parts[0]

        if request == "SETUP":
            session.state = ServerState.READY
            
            porta_v = int(parts[1]) if len(parts) > 1 else PORTA_RTP_VIDEO
            porta_a = int(parts[2]) if len(parts) > 2 else PORTA_RTP_AUDIO

            conn.send(b"RTSP/1.0 200 OK\nSession: 123456")
            
            arquivo = "hobi67.mp4"

            threading.Thread(target=video_stream_worker, args=(arquivo, addr[0], porta_v, session)).start()
            threading.Thread(target=audio_stream_worker, args=(arquivo, addr[0], porta_a, session)).start()
            
            print(f"[{addr}] Setup concluído para portas {porta_v} e {porta_a}")

        elif request in ["PLAY", "PAUSE", "TEARDOWN"]:
            if request == "PLAY": session.state = ServerState.PLAYING
            elif request == "PAUSE": session.state = ServerState.READY
            elif request == "TEARDOWN": session.state = ServerState.INIT
            conn.send(b"RTSP/1.0 200 OK")
            if request == "TEARDOWN": break

    print(f"Conexão encerrada com {addr}")
    conn.close()

if __name__ == "__main__":
    rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rtsp_socket.bind(('0.0.0.0', PORTA_RTSP))
    rtsp_socket.listen(1)
    print(f"Servidor Iniciado...")
    while True:
        conn, addr = rtsp_socket.accept()
        threading.Thread(target=handle_rtsp, args=(conn, addr)).start()