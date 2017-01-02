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
import hashlib
import random


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
    Passwds = {}
    # Establecemos un nonce para la encriptación
    Nonce = str(8983747192038)

    def Json2Dicc(self, fich, dicc):
        """Comprueba la existencia de json, si existe, actualiza diccionario"""
        
        try:
            with open(fich, 'r') as Users_Data:
                dicc = json.load(Users_Data)
        except:
            pass
 
 
    def Dicc2Json(self, fich, dicc):
        """Una vez que hay actividad, crea o actualiza fichero json"""
        
        with open(fich, 'w') as Fich_Users:
            json.dump(dicc, Fich_Users, sort_keys=True, indent='\t',
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
        ToLogFormat(LogFich, ip, port, 'Send to', msn)
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
    
    
    def Authenticated (self, address, sendedpasswd):
        """
        Busca contraseña de cliente y comprueba que su response
        coincida con el recibido
        """
        
        ClientPasswd = self.Passwds[address]['passwd'] 
        GoodM = hashlib.md5()
        TentativeM = hashlib.md5()
        Goodm.update(bytes(self.Nonce + ClientPasswd, 'utf-8'))
        TentativeM.update(bytes(self.Nonce + sendedpasswd, 'utf-8'))
        GoodResponse = GoodM.hexdigest()
        TentativeResponse = TentativeM.hexdigest() 
        Authenticater = (TentativeResponse == GoodResponse)
        return Athenticater
        
        
    def handle(self):
        """Nuestro manejador de la conexión"""
        
        IPClient = str(self.client_address[0])
        PortClient = str(self.client_address[1])
        
   #     self.wfile.write(b"SIP/2.0 200 OK")
        Received = self.rfile.read().decode('utf-8')
        ReceivedList = Received.split(' ')
        print("El cliente nos manda ", Received)
        ToLogFormat(LogFich, IPClient, PortClient, 'Received from', Received)

        ClientMethod = ReceivedList[0]
        self.Json2Dicc('registered.json', self.Users)
        
        if not ClientMethod in AvailableMethods:
            Message = 'SIP/2.0 405 Method Not Allowed\r\n\r\n'
            ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Message)
            self.wfile.write(bytes(Message, 'utf-8'))

        elif ClientMethod == 'REGISTER':
            Expires = float(ReceivedList[3].split('\r')[0])
            RegisteredTime = time.strftime('%Y-%m-%d %H:%M:%S',
                                         time.localtime(time.time()))
            PortReceivedClient = int(ReceivedList[1].split(':')[2])
            Addres = ReceivedList[1].split(':')[1]
            print(Addres)
            
            if 'Authorization' in Received:
                SendedPasswd = Received.split('=')[1]
                if Addres in self.Users:  # Existe comprobamos response
                    if self.Athenticated(Addres, SendedPasswd):
                        Message = 'SIP/2.0 200 OK\r\n\r\n'
                        ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Message)
                        self.wfile.write(bytes(Message, 'utf-8'))
                    else:
                        Message = ('SIP/2.0 401 Unauthorized\r\n' +
                                   'WWW Authenticate: Digest nonce="' +
                                    self.Nonce + '"')
                        ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Message)
                        self.wfile.write(bytes(Message, 'utf-8'))
                else:  # Nuevo usuario, no autentificamos
                    print('a')
                    self.Users[Addres] = {'ip': self.client_address[0],
                                          'port': PortReceivedClient,
                                          'registered': RegisteredTime,
                                          'expires': Expires}
                    self.Dicc2Json('registered.json', self.Users)
                    Message = 'SIP/2.0 200 OK\r\n\r\n'
                    ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Message)
                    self.wfile.write(bytes(Message, 'utf-8'))
            else:
                Message = ('SIP/2.0 401 Unauthorized\r\n' +
                           'WWW Authenticate: Digest nonce="' +
                           self.Nonce + '"')
                ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Message)
                self.wfile.write(bytes(Message, 'utf-8'))

            # creamos una lista con los usuarios a borrar
            Expire_List = self.deleteUsers()
            print(Expire_List)
            for name in Expire_List:
                del self.Users[name]
            self.Dicc2Json('registered.json', self.Users)           
            
        elif ClientMethod == 'INVITE':
            # Busca ID del invitado, le reenvia; después reenvía su respuesta
            UserInvited = ReceivedList[1].split(':')[1]
            if UserInvited in self.Users:
                IPInvited = self.Users[UserInvited]['ip']
                PortInvited = self.Users[UserInvited]['port']

                AnswerCode = self.ReSend(IPInvited, PortInvited, Received)
                Answer = AnswerCode.decode('utf-8')#NO NECESARIO, TRAZA DE PRUEBA
                print(Answer)
                
                ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Answer)
                self.wfile.write(AnswerCode)
            else:
                Message = "SIP/2.0 404 User Not Found\r\n\r\n"
                ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Message)
                self.wfile.write(bytes(Message, 'utf-8'))
                
        elif ClientMethod == 'ACK':
            # Información de destino
            UserInvited = ReceivedList[1].split(':')[1]
            IPInvited = self.Users[UserInvited]['ip']
            PortInvited = self.Users[UserInvited]['port']
            AnswerCode = self.ReSend(IPInvited, PortInvited, Received)
            
        elif ClientMethod == 'BYE':
            UserByeByed = ReceivedList[1].split(':')[1]
            if UserByeByed in self.Users:
                IPByeByed = self.Users[UserByeByed]['ip']
                PortByeByed = self.Users[UserByeByed]['port']
            
                AnswerCode = self.ReSend(IPInvited, PortInvited, Received)
                Answer = AnswerCode.decode('utf-8')
                ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Answer)
                self.wfile.write(AnswerCode)
            else:
                Message = 'SIP/2.0 404 User Not Found\r\n\r\n'
                ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Message)
                self.wfile.write(bytes(Message, 'utf-8'))
        else:
            Message = 'SIP/2.0 400 Bad Request\r\n\r\n'
            ToLogFormat(LogFich, IPClient, PortClient, 'Send to', Message)
            self.wfile.write(bytes(Message, 'utf-8'))

# Parámetros necesarios para el funcionamiento del proxy
Port = int(CDicc['server']['puerto'])
LogFich = CDicc['log']['path']

AvailableMethods = ['REGISTER', 'INVITE', 'ACK', 'BYE']  # Métodos implementados

if __name__ == "__main__":
    serv = socketserver.UDPServer(('', Port), SIPRegisterHandler)
    print("Lanzando servidor UDP de eco...")
    try:
        serv.serve_forever()
    except KeyboardInterrupt:
        print("Finalizado servidor")
