#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
User agent client. UDP. SIP.
"""

import socket
import sys
import xml.etree.ElementTree as ET
import time
import hashlib
import os


def WriteLogFich(fich, ip, port, event, message):
    """
    Función que transcribe el proceso de conexión en un fichero de texto
    """

    Log = open(fich, 'a')
    Now = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))
    port = str(port)  # Nos aseguramos de no introducir un entero

    if event == 'Starting':
        text = (Now + ' ' + event + '...' + '\r\n')
        Log.write(text)
    elif event == 'Send to':
        text = (Now + ' ' + event + ' ' + ip + ':' + port + ':' +
                message + '\r\n')
        Log.write(text)
    elif event == 'Received from':
        text = (Now + ' ' + event + ' ' + ip + ':' + port + ':' +
                message + '\r\n')
        Log.write(text)
    elif event == 'Error':
        text = (Now + ' ' + event + ':' + message + ip + ' port ' +
                port + '\r\n')
        Log.write(text)
        sys.exit(text)  # Informamos en la shell
    elif event == 'Finishing':
        text = (Now + ' ' + event + '.' + '\r\n')
        Log.write(text)
    Log.close()


def ToLogFormat(fich, ip, port, event, msn):
    """
    Elimina saltos de linea del mensaje y los sustituye por espacios en blanco.
    Escribe el mensaje utilizando WriteLogFich
    """

    TextLog = ' '.join(msn.split('\r\n'))
    WriteLogFich(fich, ip, port, event, msn)


if __name__ == "__main__":
    """
    Toma parámetros para la configuración de la conexión de un xml
    Se ata el socket a un proxy (servidor de registro)... UDP
    Usa varios métodos de sesión SIP
    """

    # Parámetros para configuración y ejecuación del UA.
    try:
        Method = sys.argv[2].upper()  # Método
        Option = sys.argv[3]  # Su uso dependerá del Método
        ConfigUA = sys.argv[1]
        ConfigTree = ET.parse(ConfigUA)
        ConfigRoot = ConfigTree.getroot()
        CDicc = {}  # Diccionario doble con los parámetros
        for child in ConfigRoot:
            CDicc[child.tag] = child.attrib
    except IndexError:
        sys.exit("Usage: python client.py config method option")
    ProxyIP = CDicc['regproxy']['ip']
    ProxyPort = int(CDicc['regproxy']['puerto'])
    LogFich = CDicc['log']['path']
    UserName = CDicc['account']['username']
    UAServerPort = int(CDicc['uaserver']['puerto'])
    UAServerIP = CDicc['uaserver']['ip']
    MyRTPPort = CDicc['rtpaudio']['puerto']
    Audio = CDicc['audio']['path']

    # Atamos el socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as my_socket:
        my_socket.connect((ProxyIP, ProxyPort))

        if Method == 'REGISTER':
            ToLogFormat(LogFich, '', '', 'Starting', '')
            Message = (Method + ' sip:' + UserName +
                       ':' + CDicc['uaserver']['puerto'] +
                       ' SIP/2.0\r\n' + 'Expires: ' + Option + '\r\n')
        elif Method == 'INVITE':
            Message = (Method + ' sip:' + Option + ' SIP/2.0\r\n')
            Message += ('Content-Type: application/sdp\r\n\r\n'
                        'v=0\r\n' +
                        'o=' + UserName + ' ' + UAServerIP + '\r\n'
                        's=music4betterlife\r\n' + 't=0\r\n' +
                        'm=audio ' + str(MyRTPPort) + ' RTP\r\n')
        elif Method == 'BYE':
            Message = (Method + ' sip:' + Option + ' SIP/2.0\r\n')

        # REVISAR SI ES NECESARIO AQUI O MÁS ADELANTE
        print("Enviando:", Message)
        my_socket.send(bytes((Message + '\r\n'), 'utf-8'))
        ToLogFormat(LogFich, ProxyIP, ProxyPort, 'Send to', Message)

        try:
            data = my_socket.recv(1024)
        except socket.error:
            ErrorMsn = " No server listening at "
            ToLogFormat(LogFich, ProxyIP, ProxyPort, 'Error', ErrorMsn)

        Answer = data.decode('utf-8')
        print(Answer)
        OK = ('SIP/2.0 200 OK')
        if 'Unauthorized' in Answer:
            Nonce = Answer.split('=')[1].split('\r')[0]
            Passwd = CDicc['account']['passwd']
            m = hashlib.md5()
            m.update(bytes(Nonce + Passwd, 'utf-8'))
            Response = m.hexdigest()
            Message += ('Authorization: Digest response=' + Response)
            ToLogFormat(LogFich, ProxyIP, ProxyPort, 'Send to', Message)
            my_socket.send(bytes((Message + '\r\n\r\n'), 'utf-8'))

        elif OK in Answer and Method == 'REGISTER':
            print('Registrado correctamente en servidor proxy')

        elif OK in Answer and Method == 'INVITE':
            # ACK
            Method = 'ACK'
            Message = (Method + ' sip:' + Option + ' SIP/2.0\r\n\r\n')
            print("Enviando:", Message)
            ToLogFormat(LogFich, ProxyIP, str(ProxyPort), 'Send to', Message)
            my_socket.send(bytes(Message, 'utf-8'))
            # Envío RTP
            HisRTPPort = Answer.split(' ')[9]
            HisRTPIP = Answer.split(' ')[8].split('\r')[0]
            ToLogFormat(LogFich, HisRTPIP, HisRTPPort, 'Send to', 'RTP Audio')
            ToClientExe = ('./mp32rtp -i' + HisRTPIP + ' -p ' +
                           HisRTPPort + ' < ' + Audio)
            os.system(ToClientExe)

        elif OK in Answer and Method == 'BYE':
            ToLogFormat(LogFich, ProxyIP, str(ProxyPort), 'Finishing', '')
            print('Llamada terminada')
            my_socket.close()
