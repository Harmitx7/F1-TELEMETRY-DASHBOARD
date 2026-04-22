"""
F1 24 UDP Client
Handles receiving and parsing binary UDP packets from the F1 game.
Specific to F1 23/24 Packet Format (2023 Spec).
"""
import socket
import struct
import threading
import logging
from telemetry_state import state

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('F1UDP')

# Constants
UDP_IP = "0.0.0.0"
UDP_PORT = 20777
BUFFER_SIZE = 2048

# Packet IDs
PACKET_ID_SESSION = 1
PACKET_ID_LAP_DATA = 2
PACKET_ID_CAR_TELEMETRY = 6

class F1PacketParser:
    """Parses binary packets from F1 24"""
    
    @staticmethod
    def parse_header(packet):
        """Parse standard 24-byte header"""
        # uint16, uint8, uint8, uint8, uint8, uint64, float, uint32, uint32, uint8, uint8
        header_fmt = '<HBBBBQfIIBB'
        header_size = struct.calcsize(header_fmt)
        
        if len(packet) < header_size:
            return None
            
        data = struct.unpack(header_fmt, packet[:header_size])
        return {
            'packet_format': data[0],  # 2023/2024
            'game_major_version': data[1],
            'game_minor_version': data[2],
            'packet_version': data[3],
            'packet_id': data[4],
            'session_uid': data[5],
            'session_time': data[6],
            'frame_identifier': data[7],
            'player_car_index': data[8]
        }

    @staticmethod
    def parse_car_telemetry(packet, player_index):
        """Parse Car Telemetry Data (ID 6)"""
        try:
            header_fmt = '<HBBBBBQ fIIBB'
            header_size = struct.calcsize(header_fmt)

            car_data_fmt = '<HfffBbHBBHHHHHBBBBBBBBHffffBBBB'
            car_data_size = struct.calcsize(car_data_fmt)

            offset = header_size + (player_index * car_data_size)

            if len(packet) < offset + car_data_size:
                return None

            data = struct.unpack(car_data_fmt, packet[offset:offset+car_data_size])

            return {
                'speed': data[0],
                'throttle': data[1],
                'steer': data[2],
                'brake': data[3],
                'clutch': data[4],
                'gear': data[5],
                'rpm': data[6],
                'drs': data[7],
                'rev_lights_percent': data[8],
                'engine_temp': data[22],
                'tyres_surface_temp': [data[14], data[15], data[16], data[17]]
            }
        except (struct.error, IndexError) as e:
            logger.warning(f"Failed to parse car telemetry: {e}")
            return None

    @staticmethod
    def parse_lap_data(packet, player_index):
        """Parse Lap Data (ID 2)"""
        try:
            header_fmt = '<HBBBBBQ fIIBB'
            header_size = struct.calcsize(header_fmt)

            lap_data_fmt = '<IIHHfffBBBBBBBBBBBBBBHHB'
            lap_data_size = struct.calcsize(lap_data_fmt)

            offset = header_size + (player_index * lap_data_size)

            if len(packet) < offset + lap_data_size:
                return None

            data = struct.unpack(lap_data_fmt, packet[offset:offset+lap_data_size])

            return {
                'last_lap_time': data[0],
                'current_lap_time': data[1],
                'sector1_time': data[2],
                'sector2_time': data[3],
                'lap_distance': data[4],
                'total_distance': data[5],
                'car_position': data[7],
                'current_lap': data[8],
                'pit_status': data[9],
                'sector': data[11],
                'current_lap_invalid': data[12],
                'penalties': data[13]
            }
        except (struct.error, IndexError) as e:
            logger.warning(f"Failed to parse lap data: {e}")
            return None

    @staticmethod
    def parse_session_data(packet):
        """
        Parse Session Data (ID 1)
        Extracts weather, track temperature, session type, etc.
        """
        header_fmt = '<HBBBBBQ fIIBB'
        header_size = struct.calcsize(header_fmt)
        
        # Session packet structure (simplified for key fields)
        # Format: B(Weather), B(TrackTemp), B(AirTemp), B(TotalLaps), H(SessionTime), B(SessionType), B(TrackID), B(Formula)
        session_fmt = '<BBBBHBBBxxxxxxxxx'  # x = padding for unused fields
        session_size = struct.calcsize(session_fmt)
        
        offset = header_size
        
        if len(packet) < offset + session_size:
            return None
        
        try:
            data = struct.unpack(session_fmt, packet[offset:offset+session_size])
            
            return {
                'weather': data[0],
                'track_temperature': data[1],
                'air_temperature': data[2],
                'total_laps': data[3],
                'session_time_left': data[4],
                'session_type': data[5],
                'track_id': data[6],
                'formula': data[7]
            }
        except struct.error:
            return None

class UdpListener(threading.Thread):
    def __init__(self):
        super(UdpListener, self).__init__()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.running = False
        self.daemon = True
        
    def run(self):
        self.running = True
        try:
            # Allow address reuse to prevent "Address already in use" errors on restart
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((UDP_IP, UDP_PORT))
            logger.info(f"UDP Listener started on port {UDP_PORT}")
            
            while self.running:
                try:
                    data, _ = self.sock.recvfrom(BUFFER_SIZE)
                    
                    # Parse Header first to get ID and Player Index
                    # Parse Header first to get ID and Player Index
                    # F1 24 Header Format with Overall Frame ID and Secondary Player Index
                    header_fmt = '<HBBBBQfIIBB' 
                    header_size = struct.calcsize(header_fmt)
                    
                    if len(data) < header_size:
                        continue
                        
                    # Unpack header
                    header_raw = struct.unpack(header_fmt, data[:header_size])
                    packet_id = header_raw[4]
                    player_index = header_raw[9] # Index 9 in new format (was 8)
                    
                    # Dispatch based on packet type
                    if packet_id == PACKET_ID_CAR_TELEMETRY:
                        result = F1PacketParser.parse_car_telemetry(data, player_index)
                        if result:
                            state.update_telemetry(result)
                            
                    elif packet_id == PACKET_ID_LAP_DATA:
                        result = F1PacketParser.parse_lap_data(data, player_index)
                        if result:
                            state.update_lap_data(result)
                            
                    elif packet_id == PACKET_ID_SESSION:
                        # Complete session packet parsing
                        result = F1PacketParser.parse_session_data(data)
                        if result:
                            state.update_session(result)


                except struct.error as se:
                    logger.warning(f"Packet Struct Error: {se} (ID: {packet_id if 'packet_id' in locals() else 'Unknown'})")
                except Exception as e:
                    logger.error(f"Error handling packet ID {packet_id if 'packet_id' in locals() else 'Unknown'}: {e}")
                    
        except Exception as e:
            logger.critical(f"FATAL UDP Listener Error: {e}")
        finally:
            logger.info("UDP Listener stopping...")
            self.sock.close()
            
    def stop(self):
        self.running = False
        # Unblock recvfrom by shutting down the socket
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass  # Socket may already be closed
