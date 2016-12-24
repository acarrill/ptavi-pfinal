#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
User agent client. UDP. SIP.
"""

import socket
import sys
import xml.etree.ElementTree as ET
import time

def WriteLogFich(fich, ip, port, event, message):
    """
    Función que transcribe el proceso de conexión en un fichero de texto
    """
    
    Log = open(fich, 'a')
    Now = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    
    if event == 'Starting':
        text = (Now + ' ' +  event + '...')
        Log.write(text)
    elif event == 'Send to':
        text = (Now + ' ' +  event + ' ' + ip + ':' + port + ':' 
                + message + '\r\n')
        Log.write(text)
    elif event == 'Received from':
        text = (Now + ' ' +  event + ' ' + ip + ':' + port + ':' 
                + message + '\r\n')
        Log.write(text)
    elif event == 'Error':
        text = (Now + event + ':' + message)
        Log.write(text)
    elif event == 'Finishing':
        text = (Now + ' ' +  event + '.')
        Log.write(text)
    Log.close()
        


# Parámetros para configuración y ejecuación del UA.
try:
    Method = sys.argv[2].upper()  # Método
    Option = sys.argv[3]  # Su uso dependerá del Método
    ConfigUA = sys.argv[1]
    ConfigTree = ET.parse(ConfigUA)
    ConfigRoot = ConfigTree.getroot()
    CDicc = {}  # C = Config
    for child in ConfigRoot:
        CDicc[child.tag] = child.attrib      
except IndexError:
    print("Usage: python client.py config method option")

ProxyIP = CDicc['regproxy']['ip']
ProxyPort = int(CDicc['regproxy']['puerto'])
LogFich = CDicc['log']['path']

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
if __name__ == "__main__":
    """Se crea socket y se manda método al server"""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.connect((ProxyIP, ProxyPort))
        
        if Method == 'REGISTER':
            WriteLogFich(LogFich, 'a', 'a', 'Starting', '')
            Message = (Method + ' sip:' + CDicc['account']['username'] + 
                       ':' + CDicc['uaserver']['puerto'] +
                      ' SIP/2.0\r\n' + 'Expires: ' + Option + '\r\n\r\n')
            #Escribir en fichero 'log'
        
            
        print("Enviando:", Message)
        my_socket.send(bytes(Message, 'utf-8') + b'\r\n\r\n')
        data = my_socket.recv(1024)
        
        
        Answer = data.decode('utf-8')
        OK = ('SIP/2.0 100 Trying\r\n\r\n'  # Invite recibido correctamente
              'SIP/2.0 180 Ring\r\n\r\n'
              'SIP/2.0 200 OK\r\n\r\n')
