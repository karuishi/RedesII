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
    # Utilizamos um socket UDP porque é o padrão para transmissão de mídia em tempo real (RTP). 
    # O UDP não exige confirmação de recebimento, o que o torna muito mais rápido que o TCP e evita 
    # atrasos na reprodução caso um pacote se perca na rede.
    audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # carregando a faixa de audio do arquivo de video
    audio_clip = AudioFileClip(video_path)
    fps_audio = 44100
    chunk_size = 1024
    delay = chunk_size / float(fps_audio)    #descobre quanto tempo os 1024 frames do audio demoram pra tocar irl

    # extrai todo o áudio para memoria ram de uma vez, fecha o arquivo p liberar recursos, converte a matriz e conta o tamanho real
    audio_array = audio_clip.to_soundarray(fps=fps_audio)
    audio_clip.close()

    # Passa o array de floats para int16 (formato esperado pelo cliente pyaudio)

    # O MoviePy devolve o som como números decimais flutuantes (entre -1.0 e 1.0). 
    # A linha de conversão (* 32767) normaliza esses dados matematicamente para 
    # inteiros de 16-bits (PCM16). Isso é necessário porque o PyAudio do lado do 
    # cliente só sabe reproduzir o formato PCM16.
    pcm16_audio = np.int16(audio_array * 32767)
    total_frames = len(pcm16_audio)
    
    idx = 0
    seq_num = 0 #inicalização do numero de sequencia
    
    # mantem a thread viva durante a conexão
    while True:
        # garante o envio de dados isolado (cada cliente controla sua propria sessão)
        if session.state == ServerState.PLAYING:
            if idx >= total_frames:
                break # fim do áudio
                
            # recorta um chunk do array de áudio que tá na memória, transforma de matriz numérica
            # para bytes puros com o tobytes e aplica a criptografia.
            fim = min(idx + chunk_size, total_frames)
            data_chunk = pcm16_audio[idx:fim]
            payload = fernet.encrypt(data_chunk.tobytes())
            # justificando:
            # estamos fazendo o fatiamento manual do audio com o idx:fim, pq ele permite que controlemos
            # exatamente o tamanho do pacote que vai para a rede
            # A criptografia com Fernet protege o conteúdo do payload para que a mídia não possa ser 
            # interceptada e reproduzida no meio do caminho.
            
            #criando o cabeçalho RTP para o audio
            # cria o timestamp, junta com o num de sequencia e o payload que foi criptografado dentro de um pacote rtp
            # e dispara via udp para a porta dinamica do cliente.
            timestamp = int(time.time() * 44100) & 0xFFFFFFFF     #vital para que o cliente saiba a hora exata de tocar aquele pacote,
            pacote = RTPPacket(97, seq_num, timestamp, payload)
            audio_socket.sendto(pacote.get_packet(), (ip_destino, porta_destino))
            
            seq_num = (seq_num + 1) % 65536   # garante que o número de sequência volte a zero ao atingir o limite de 16 bits do protocolo RTP
            idx += chunk_size
            time.sleep(delay)   # obriga o servidor a transmitir o pacote na mesma velocidade que o cliente o consome (evitando estourar a memoria e a conexão do cliente)
            
        elif session.state == ServerState.INIT: 
            break
        else: 
            # trata o comando PAUSE. 
            # mantém a thread leve e em espera sem consumir o processador desnecessariamente
            time.sleep(0.1)

def handle_rtsp(conn, addr):
    # Registra no console do servidor o IP e porta (addr) do cliente que acabou de conectar.
    print(f"Conexão RTSP de {addr}")
    
    # Cria uma nova instância de sessão para este cliente específico.
    # Isso inicializa uma máquina de estados (geralmente começando no estado INIT).
    session = ClientSession()

    # Inicia um loop infinito para manter a conexão TCP aberta, aguardando os comandos do cliente.
    while True:
        # Recebe até 1024 bytes de dados do socket do cliente e decodifica de bytes para string.
        data = conn.recv(1024).decode()
        
        # Se os dados estiverem vazios (o cliente fechou a conexão abruptamente), quebra o loop.
        if not data: break

        # Divide a mensagem recebida usando os espaços como separador. 
        # Ex: "SETUP 5000 5002" vira ["SETUP", "5000", "5002"]
        parts = data.split(' ')
        request = parts[0] # O comando principal é a primeira palavra (índice 0).

        # Verifica se o comando é de configuração inicial
        if request == "SETUP":
            # Altera o estado da sessão para READY (pronto para transmitir).
            session.state = ServerState.READY
            
            # Extrai as portas UDP que o cliente quer usar para receber o vídeo e o áudio.
            # Se o cliente não informar as portas, utiliza portas padrão predefinidas no servidor.
            porta_v = int(parts[1]) if len(parts) > 1 else PORTA_RTP_VIDEO
            porta_a = int(parts[2]) if len(parts) > 2 else PORTA_RTP_AUDIO

            # Envia a resposta de sucesso padrão do protocolo RTSP de volta para o cliente.
            conn.send(b"RTSP/1.0 200 OK\nSession: 123456")
            
            # Define o nome do arquivo de mídia que será transmitido ao cliente.
            arquivo = "bill_nav.mp4"

            # INICIALIZAÇÃO DAS THREADS DE STREAMING (RTP via UDP):
            # Cria e inicia uma thread paralela responsável apenas por ler e enviar os quadros de vídeo.
            threading.Thread(target=video_stream_worker, args=(arquivo, addr[0], porta_v, session)).start()
            # Cria e inicia uma thread paralela responsável apenas por ler e enviar os blocos de áudio.
            threading.Thread(target=audio_stream_worker, args=(arquivo, addr[0], porta_a, session)).start()
            
            # Registra no console que a configuração deste cliente foi finalizada.
            print(f"[{addr}] Setup concluído para portas {porta_v} e {porta_a}")

        # Se o comando for de manipulação de fluxo contínuo
        elif request in ["PLAY", "PAUSE", "TEARDOWN"]:
            
            # Se for PLAY, muda o estado para PLAYING. 
            # Isso "destrava" as threads iniciadas no SETUP, fazendo com que elas comecem a enviar os pacotes RTP de mídia.
            if request == "PLAY": session.state = ServerState.PLAYING
            
            # Se for PAUSE, retrocede o estado para READY.
            # As threads ainda estarão ativas na memória, mas pararão de enviar pacotes UDP, pausando a mídia.
            elif request == "PAUSE": session.state = ServerState.READY
            
            # Se for TEARDOWN, altera o estado para INIT (sinalizando às threads que elas devem encerrar sua execução).
            elif request == "TEARDOWN": session.state = ServerState.INIT
            
            # Confirma o recebimento e o sucesso do comando para o cliente.
            conn.send(b"RTSP/1.0 200 OK")
            
            # Se o cliente solicitou o encerramento da sessão, quebra o loop while True.
            if request == "TEARDOWN": break

    # Após o loop ser quebrado (seja pelo TEARDOWN ou por perda de conexão), 
    # imprime um log de encerramento e fecha permanentemente o socket TCP desse cliente.
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
