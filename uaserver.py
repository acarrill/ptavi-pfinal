#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import sys
import os
import xml.etree.ElementTree as ET
from uaclient import WriteLogFich

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
    print("Usage: python server.py config")
except OSError:
    print("Configuration file not finded. Please fix path and restart")


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """

    def handle(self):
        """Manejador de conexión"""
        Received = self.rfile.read().decode('utf-8')
        ListReceived = Received.split(' ')  # Lista de la cadena recibida
        ClientMethod = ListReceived[0]

        if len(ListReceived) != 3 or ListReceived[2] != 'SIP/2.0\r\n\r\n':
            self.wfile.write(b'SIP/2.0 400 Bad Request\r\n\r\n')
        elif ClientMethod == 'INVITE':
            self.wfile.write(bytes('SIP/2.0 100 Trying\r\n\r\n'
                                   'SIP/2.0 180 Ring\r\n\r\n'
                                   'SIP/2.0 200 OK\r\n\r\n', 'utf-8'))
        elif ClientMethod == 'BYE':
            self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
        elif ClientMethod == 'ACK':
            ToClientExe = './mp32rtp -i 127.0.0.1 -p 23032 < ' + Audio
            os.system(ToClientExe)
        else:
            self.wfile.write(b'SIP/2.0 405 Method Not Allowed\r\n\r\n')

#Parámetros para lanzar el server
ServerIP = CDicc['uaserver']['ip']
ServerPort = int(CDicc['uaserver']['puerto'])

if __name__ == "__main__":
    # Creamos servidor de eco y escuchamos
    serv = socketserver.UDPServer((ServerIP, ServerPort), EchoHandler)
    print("Lanzando servidor UDP de eco...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
