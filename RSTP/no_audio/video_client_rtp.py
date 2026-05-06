import socket
import struct
import numpy as np
import cv2

def iniciar_cliente_teste(ip="127.0.0.1", porta=1234):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((ip, porta))
    
    print(f"Aguardando pacotes RTP em {ip}:{porta}...")
    print("Pressione 'q' na janela de vídeo para sair.")
    
    try:
        while True:
            data, addr = client_socket.recvfrom(65535) # Tamanho max bytes 
            
            if len(data) < 12:
                continue
            
            header = data[:12]
            rtp_header = struct.unpack('!BBHII', header)
            payload = data[12:]
            
            try:
                nparr = np.frombuffer(payload, np.uint8) # Convert Bytes -> Numpy Array -> Img OpenCV
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    cv2.imshow('Streaming RTP - 2026', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            except Exception as e:
                print(f"Erro ao decodificar frame: {e}") 
    
    except KeyboardInterrupt:
        print("\nCliente parado.")
    finally:
        client_socket.close()
        cv2.destroyAllWindows()
        
if __name__ == "__main__":
    iniciar_cliente_teste()