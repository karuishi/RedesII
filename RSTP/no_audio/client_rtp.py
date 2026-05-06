import socket
import struct
import numpy as np

def iniciar_cliente_teste(ip="127.0.0.1", porta=1234):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((ip, porta))
    
    print(f"Aguardando pacotes RTP em {ip}:{porta}...")
    
    try:
        while True:
            data, addr = client_socket.recvfrom(2048) # Tamanho max bytes 
            
            if len(data) < 12:
                print("Pacote inválido recebido (menor que o cabeçalho RTP).")
                continue
            
            header = data[:12]
            rtp_header = struct.unpack('!BBHII', header)
            
            v_p_x_cc = rtp_header[0]
            m_pt = rtp_header[1]
            seq_num = rtp_header[2]
            timestamp = rtp_header[3]
            ssrc = rtp_header[4]
            
            payload = data[12:]
            
            print(f"[RECEBIDO] Origem: {addr}")
            print(f"   Seq: {seq_num} | Time: {timestamp} | SSRC: {ssrc}")
            print(f"   Payload ({len(payload)} bytes): {payload.decode(errors='ignore')[:30]}...")
            print("-" * 50)
    
    except KeyboardInterrupt:
        print("\nCliente parado.")
    finally:
        client_socket.close()
        
if __name__ == "__main__":
    iniciar_cliente_teste()