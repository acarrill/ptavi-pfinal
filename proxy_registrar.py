#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import socketserver
import socket
import sys
import json
import time
import os
import xml.etree.ElementTree as ET
from uaclient import ToLogFormat



try:  # Tomamos la configuración del Proxy de un xml
    ConfigProxy = sys.argv[1]
    if not os.path.exists(ConfigProxy):  # Comprueba que existe el fichero
        raise OSError
    ConfigTree = ET.parse(ConfigProxy)
    ConfigRoot = ConfigTree.getroot()
    CDicc = {}  # C = Config
    for child in ConfigRoot:
        CDicc[child.tag] = child.attrib  # Diccionario doble 
except IndexError:
    print("Usage: python proxy_registrar.py config")
except OSError:
    print("Configuration file not finded. Please fix path and restart")



class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    # Diccionario como atributo de clase
    Users = {}


    def json2registered(self):
        """Comprueba la existencia de json, si existe, actualiza diccionario"""
        
        try:
            with open("registered.json", 'r') as Users_Data:
                self.Users = json.load(Users_Data)
        except:
            pass
 
 
    def register2json(self):
        """Una vez que hay actividad, crea o actualiza fichero json"""
        
        with open('registered.json', 'w') as Fich_Users:
            json.dump(self.Users, Fich_Users, sort_keys=True, indent='\t',
                      separators=(',', ':'))


    def deleteUsers(self):
        """Crea una lista con los usuarios expirados"""
        
        Now = time.strftime('%Y-%m-%d %H:%M:%S',
                                   time.localtime(time.time()))
        To_Delete = []
        for name in self.Users:
            RegisteredTime = self.Users[name]['registered']
            Expiration = self.ExpiresTime(RegisteredTime, self.Users[name]['expires'])
            print(Expiration)
            if Expiration < Now:
                To_Delete.append(name)
        return To_Delete


    def ReSend (self, ip, port, msn):
        """
        Redirije el mensaje a un usuario destino 
        Imprime en log
        Devuelve respuesta
        """
        
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        my_socket.connect((ip, port))
        ToLogFormat(LogFich, ip, port, 'Sen to', msn)
        my_socket.send(bytes(msn, 'utf-8'))
        data = my_socket.recv(1024)
        return data
   
   
    def ExpiresTime (self, registered, toexpire):
        """
        Devuelve fecha de expiración:
        (fecha de registro a segundos + expiración)
        """
        
        RegistInSeconds = time.mktime(time.strptime(registered, '%Y-%m-%d %H:%M:%S'))
        ExpiresTime = time.strftime('%Y-%m-%d %H:%M:%S',
                                   time.localtime(RegistInSeconds + toexpire))
        return ExpiresTime
    
    
    def handle(self):
        """Nuestro manejador de la conexión"""
        
        IPClient = str(self.client_address[0])
        PortClient = str(self.client_address[1])
        
   #     self.wfile.write(b"SIP/2.0 200 OK")
        Received = self.rfile.read().decode('utf-8')
        ReceivedList = Received.split(' ')
        print("El cliente nos manda ", Received)


        ClientMethod = ReceivedList[0]
        self.json2registered()
        
        print(ReceivedList)
        if ClientMethod == 'REGISTER':
            Expires = float(ReceivedList[3].split('\r')[0])
            RegisteredTime = time.strftime('%Y-%m-%d %H:%M:%S',
                                         time.localtime(time.time()))
                                         
            PortReceiverClient = int(ReceivedList[1].split(':')[2])
            
            Addres = ReceivedList[1].split(':')[1]
            print(Addres)
            self.Users[Addres] = {'ip': self.client_address[0],
                                  'port': PortReceiverClient,
                                  'registered': RegisteredTime,
                                  'expires': Expires}
     
            if Expires == 0:
                print('aaaa')
                del self.Users[Addres]
            # creamos una lista con los usuarios a borrar
            self.register2json()
            Expire_List = self.deleteUsers()
            print(Expire_List)
            for name in Expire_List:
                del self.Users[name]
            self.register2json()           
            
        elif ClientMethod == 'INVITE':
            UserInvited = ReceivedList[1].split(':')[1]
            if UserInvited in self.Users:
                IPInvited = self.Users[UserInvited]['ip']
                PortInvited = self.Users[UserInvited]['port']
                            
                AnswerCode = self.ReSend(IPInvited, PortInvited, Received)
                Answer = AnswerCode.decode('utf-8')
                print(Answer)
                
                self.wfile.write(AnswerCode)


# Parámetros necesarios para el funcionamiento del proxy
Port = int(CDicc['server']['puerto'])
LogFich = CDicc['log']['path']

if __name__ == "__main__":
    serv = socketserver.UDPServer(('', Port), SIPRegisterHandler)
    print("Lanzando servidor UDP de eco...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
