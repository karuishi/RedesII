import socket
import time
import struct

class RTPPacket:
    def __init__(self, payload_type, seq_num, timestamp, payload):
        self.version = 2
        self.padding = 0
        self.extension = 0
        self.cc = 0
        self.marker = 0
        self.payload_type = payload_type
        self.seq_num = seq_num
        self.timestamp = timestamp
        self.payload = payload

    def get_packet(self):
        """Monta o cabeçalho de 12 bytes + payload"""
        header_0 = (self.version << 6) | (self.padding << 5) | (self.extension << 4) | self.cc
        header_1 = (self.marker << 7) | self.payload_type
        
        # 'H' = 16 bits (seq_num), 'I' = 32 bits (timestamp/ssrc)
        header = struct.pack('!BBHII', header_0, header_1, self.seq_num, self.timestamp, 12345)
        return header + self.payload

def iniciar_servidor(ip_destino, porta_destino):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # QoS: Definindo prioridade no cabeçalho IP (DSCP)
    server_socket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)

    seq_num = 0
    timestamp = 0
    fps = 25
    intervalo = 1.0 / fps

    print(f"Transmitindo para {ip_destino}:{porta_destino}...")

    try:
        while True:
            # Simulação: Pegando um quadro de vídeo (aqui seriam os bytes do H.264/MJPEG)
            # "quadro" falso de 500 bytes para teste
            frame_fake = b"dados_do_video_" + str(seq_num).encode()

            pacote = RTPPacket(
                payload_type=26,  # 26 é o padrão para JPEG/MJPEG
                seq_num=seq_num,
                timestamp=timestamp,
                payload=frame_fake
            )
            
            server_socket.sendto(pacote.get_packet(), (ip_destino, porta_destino))

            seq_num = (seq_num + 1) % 65536
            timestamp += 3600 # Valor comum para 90kHz (90000 / 25 fps)
            
            time.sleep(intervalo)
            
            if seq_num % 100 == 0:
                print(f"Enviados {seq_num} pacotes...")

    except KeyboardInterrupt:
        print("\nServidor finalizado pelo usuário.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    # Para testar localmente, use 127.0.0.1
    iniciar_servidor("127.0.0.1", 1234)