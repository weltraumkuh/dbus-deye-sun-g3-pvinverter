""" A basic class fro Communication with Deye Inverters via AT commands """

import socket


class DeyeAtComm:
    Logger_Init_CMD=b'WIFIKIT-214028-READ'

    def modbus_crc(self,data):
        POLY = 0xA001
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ POLY
                else:
                    crc = crc >> 1
        return crc



    def deye_at_command(self,register_addr : int ,count : int, function :int,values: None | list[int, ...] = None) :
        req_data = bytearray([1, function])
        req_data.extend(register_addr.to_bytes(2,'big'))
        req_data.extend(count.to_bytes(2,'big'))
        if values:
            v_len=len(values)
            rq_data.extend(v_len.to_bytes(2,'big'))
            for v in values:
                req_data.extend(v.to_bytes(2,'big'))
        crc = self.modbus_crc(req_data)
        req_data.extend(crc.to_bytes(2,'little'))
        req_len=len(req_data)
        cmd = f'INVDATA={req_len},{req_data.hex()}'
        at_cmd = f'AT+{cmd}\n'.encode()
        return at_cmd

    def parse_at_response(self,rx_data : bytes) :
        rx_string= rx_data.decode('ASCII')
        rx_string = rx_string.replace('\x10','')
        rx_string = rx_string.replace('\r','')
        rx_string = rx_string.strip()
        assert '+ok=' in rx_string, f'RX String does is not "OK": {rx_string=}'
        rx_payload=rx_string.partition('+ok=')[2]
        payload_bin = bytes.fromhex(rx_payload)
        crc_check = self.modbus_crc(payload_bin[:-2])
        crc_check = crc_check.to_bytes(2,'little')
        crc_rx = payload_bin[-2:]
        assert crc_rx == crc_rx, f'CRC error rx:{crc_rx=} not {crc_check}'
        rx_len = payload_bin[2]
        assert rx_len+5 == len(payload_bin), f'Payload length is not {rx_len=}: {payload_bin=}'
    #    return  ModbusResponse( 
    #                            slave_id=payload_bin[0],
    #                            modbus_function=payload_bin[1],
    #                            payload=payload_bin[3:-2]
    #                            )
        payload=[]
    #    print(f'Convert {payload_bin=}:')
        for idx in range(int(rx_len/2)):
            (h,l) = payload_bin[2*idx+3:2*idx+5]
            v=int.from_bytes((h,l),'big')
    #        print(f'{h=},{l=} to: {v=}')
            payload.append(v)
    #    return payload_bin[3:-2]
        return payload





    def read(self, register_addr :int ,count :int) :
        payload=self.deye_at_command(register_addr,count,0x03)
    #    payload_str = payload.decode('ASCII')
        print(f'Send Payload: "{payload=}"')
        self.sock.sendto(payload,(self.Logger_IP,self.Logger_Port))
        rx_payload=self.sock.recv(1024)
        response=self.parse_at_response(rx_payload)
        return response


    def hello(self) :
        self.sock.sendto(self.Logger_Init_CMD,(self.Logger_IP,self.Logger_Port))
        data=self.sock.recv(1024)
        self.sock.sendto(b'+ok',(self.Logger_IP,self.Logger_Port))
        return data.decode().split(',')

    def bye(self) :
        self.sock.sendto(b'AT+Q\n',(self.Logger_IP,self.Logger_Port))

    def getversion(self) :
        self.sock.sendto(b'AT+YZVER\n',(self.Logger_IP,self.Logger_Port))
        repl = self.sock.recv(1024).decode()
        assert'+ok=' in repl, f'getversion, Reply is not ok: {repl}'
        (status,version)=repl.split('=')
        return version
        

    def __init__(self ,IP , Port,timeout=1) :
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.settimeout(timeout)
        self.Logger_IP=IP
        self.Logger_Port=Port
        self.ip=''
        self.mac=''
        self.serial=''
        try:
            (self.ip,self.mac,self.serial)=self.hello()
        finally:
            return

    def __del__(self) :
        try:
            print('Disconnect with AT+Q')
            self.bye()
        finally:
            return

