#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socket
import socketserver
import sys
import os
import xml.etree.ElementTree as ET
from uaclient import ToLogFormat

try:  # Tomamos la configuración de la conexión de un xml
    ConfigUA = sys.argv[1]
    if not os.path.exists(ConfigUA):  # Comprueba que existe el fichero
        raise OSError
    ConfigTree = ET.parse(ConfigUA)
    ConfigRoot = ConfigTree.getroot()
    CDicc = {}  # C = Config
    for child in ConfigRoot:
        CDicc[child.tag] = child.attrib  # Diccionario doble 
except IndexError:
    print("Usage: python uaserver.py config")
except OSError:
    print("Configuration file not finded. Please fix path and restart")

class UAHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

    InfoRTPCaller = {}

    def handle(self):
        """Manejador de conexión"""
        IPCaller = str(self.client_address[0])
        PortCaller = str(self.client_address[1])
        
        Received = self.rfile.read().decode('utf-8')
        ListReceived = Received.split(' ')  # Lista de la cadena recibida
        ClientMethod = ListReceived[0]
        
        ToLogFormat(LogFich, IPCaller, PortCaller, 'Received from', Received)

        if not ClientMethod in AvailableMethods:
            Message = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
            ToLogFormat(LogFich, IPCaller, PortCaller, 'Sen to', Message)
            self.wfile.write(bytes(Message, 'utf-8'))
        elif ClientMethod == 'INVITE':
            print(ListReceived)
            self.InfoRTPCaller['IP'] = ListReceived[4].split('\r')[0]
            self.InfoRTPCaller['Port'] = ListReceived[5].split('\r')[0]
            NameCaller = ListReceived[1].split(':')[1]
            
            Message = ('SIP/2.0 100 Trying\r\n\r\n'
                      'SIP/2.0 180 Ring\r\n\r\n'
                      'SIP/2.0 200 OK\r\n')
            Message += ('Content-Type: application/sdp\r\n\r\n'
                        'v=0\r\n' + 
                        'o=' + NameCaller + ' ' + IPCaller + '\r\n'
                        's=music4betterlife\r\n' + 't=0\r\n' +
                        'm=audio ' + str(ServerPort) + ' RTP\r\n\r\n')
            ToLogFormat(LogFich, IPCaller, PortCaller, 'Sen to', Message) 
                 
            self.wfile.write(bytes(Message, 'utf-8'))
        elif ClientMethod == 'BYE':
            Message = 'SIP/2.0 200 OK\r\n\r\n'
            ToLogFormat(LogFich, IPCaller, PortCaller, 'Sen to', Message)
            self.wfile.write(bytes(Message, 'utf-8'))
        elif ClientMethod == 'ACK':
            ToLogFormat(LogFich, InfoRTPCaller['IP'], 
                        InfoRTPCaller['Port'], 'Sen to', 'RTP Audio')
            ToClientExe = ('./mp32rtp -i' + InfoRTPCaller['IP'] + ' -p ' +
                           InfoRTPCaller['Port'] + ' < ' + Audio)
            os.system(ToClientExe)
        else:
            Message = 'SIP/2.0 400 Bad Request\r\n\r\n'
            ToLogFormat(LogFich, IPCaller, PortCaller, 'Sen to', Message)
            self.wfile.write(bytes(Message, 'utf-8'))
            

# Parámetros para lanzar el server
ServerIP = CDicc['uaserver']['ip']
ServerPort = int(CDicc['uaserver']['puerto'])
LogFich = CDicc['log']['path']
Audio = CDicc['audio']['path']
# Proxy
ProxyIP = CDicc['regproxy']['ip']
ProxyPort = int(CDicc['regproxy']['puerto'])

AvailableMethods = ['INVITE', 'ACK', 'BYE']  # Métodos implementados

if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((ProxyIP, ProxyPort))
    
    serv = socketserver.UDPServer((ServerIP, ServerPort), UAHandler)
    print("Lanzando servidor UDP de eco...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
