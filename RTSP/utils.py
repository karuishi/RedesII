import struct
import time
from cryptography.fernet import Fernet

PORTA_RTP_VIDEO = 12345
PORTA_RTP_AUDIO = 12346
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
        # Cabeçalho RTP simplificado
        header = struct.pack('!BBHII', 
                             (self.version << 6), 
                             self.payload_type, 
                             self.seq_num, 
                             self.timestamp, 
                             0) # SSRC ou Identificador
        return header + self.payload