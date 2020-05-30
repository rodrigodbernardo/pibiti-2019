import asyncio
import websockets
from datetime import datetime
import time
import subprocess
import socket
import numpy as np
import matplotlib.pyplot as plt
import csv
import glob
import os
import json
from itertools import count
from matplotlib.animation import FuncAnimation

#Pacotes para windows
if os.name == 'nt':
    import msvcrt

#Pacotes para linux/MacOs
#else:
#    import sys
#    import termios
#    import atexit
#    from select import select

clear = lambda: os.system('cls')
menu = "0"
capt_remaining = 0
capt_code = ""
x = []
y1 = []
y2 = []
y3 = []
y4 = []

indc = count()

async def clientConnected(websocket, path):
    #response = ''

    clear()

    print('Conexão bem sucedida!')

    print('\nMenu Principal\n')
    print('1-Captura')
    print('2-Análise em tempo real')
    print('3-Reiniciar sensor')
    mainMenu = input('>>> ')    #verificar se é um dos números

    try:
        await asyncio.wait_for(websocket.send(mainMenu), timeout=5.0)
    except asyncio.TimeoutError:
        print('O cliente parou de responder. Reiniciando o servidor.')
        return

    clear()
    if(mainMenu == '1'):
        print('1-captura\n')

        captureCode = input('Código da captura: ')  #verificar se a pasta existe, criar se nao existir
        numberOfCaptures = input('Número de capturas: ')   #verificar se é número
        numberOfSamples = input('Número de amostras em cada captura: ')    #verificar se é número; numero maximo é 2500

        try:
            await asyncio.wait_for(websocket.send(numberOfSamples), timeout=5.0)
        except asyncio.TimeoutError:
            print('O cliente parou de responder. Reiniciando o servidor.')
            return

        numberOfCaptures = int(numberOfCaptures)
        numberOfSamples = int(numberOfSamples)

        print('Iniciando captura. Não desligue o sistema.')
        for iteration in range (numberOfCaptures):
            await websocket.send('continue')

            print('Captura {} iniciada.'.format(iteration+1))

            #
            # Aguarda um tempo enquanto o sensor captura os dados.
            #

            timeOfCapture = await websocket.recv()
            print('Tempo de Captura: {} ms.' .format(timeOfCapture))
            print('Recebendo dados. Aguarde...')

            now = datetime.now()
            current_time = now.strftime(("%Y%m%d_%H-%M-%S"))
            
            #if(len(timeOfCapture) < 4):
            timeOfCapture = ("{:04d}".format(int(timeOfCapture)))

            #os.chdir(r'C:\Users\rodri\Documents\pibiti-2019\python\capture')
            file = open("./capture/{}_{}_A{:04d}_C{:03d}_{}ms.txt".format(captureCode,current_time,numberOfSamples,iteration+1,timeOfCapture),"w")

            for i in range(numberOfSamples):
                if (i == 0):
                    file.write("AcX,AcY,AcZ,GyX,GyY,GyZ,Tmp\n")

                dado = await websocket.recv()
                file.write("{}".format(dado))
                file.write("\n")

            file.close()

            timeOfDownload = await websocket.recv()
            print('Tempo de download: {} ms.'.format(timeOfDownload))
            print('Captura {} concluída.\n'.format(iteration+1))


        await websocket.send('stop')
        print('Processo concluído.')
            

    elif(mainMenu == '2'):
        print("Preparando análise. Pressione 'ESC' para sair.")
        while True:
            print(await websocket.recv())

            if msvcrt.kbhit():
                if ord(msvcrt.getch()) == 27:
                    print('Análise finalizada. Fazendo reconexão...')
                    break
    
    elif mainMenu == '3':
        return
        
        
def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

##
##  INICIO (será executado antes da funcao getData)
##


myip = get_ip()
port = 80
#while True:

clear()

print("****PIBITI-2019****")

mainMenu = input("""
***MENU PRINCIPAL***

1-CONECTAR AO SENSOR
2-PLOTAR DADOS CAPTURADOS
3-UTILIZAÇÃO DO SOFTWARE
4-SAIR

>>> """)

clear()

if(mainMenu == '1'):
    print("1-CONECTAR AO SENSOR")
    print("CRIANDO SERVIDOR EM: {}:{}".format(myip,port))
    w_server = websockets.serve(clientConnected, myip, port)

    print("\nAGUARDANDO COMUNICAÇÃO WEBSOCKET...")
    asyncio.get_event_loop().run_until_complete(w_server)
    asyncio.get_event_loop().run_forever()

elif(mainMenu == '2'):
    
    print('2-PLOTAR DADOS CAPTURADOS')
    
    error = 1
    while(error):
        folder = input("CODIGO DA PASTA [XYZZ]: ")
        if (os.path.isdir("./python_server/capture/{}".format(folder))):
            error = 0
        else:
            print("PASTA INESISTENTE. TENTE NOVAMENTE.\n\n")

    cap = int(input("QUANTAS AMOSTRAS DESEJA PLOTAR (1 - 2500)? "))

    for path in glob.glob("./python_server/capture/{}/*.txt".format(folder)):
        with open(path) as csv_file:
            path = path.replace("./python_server/capture/{}".format(folder),'').replace(".txt",'')

            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0 #Zera a contagem de linhas a cada arquivo lido.

            d={'acelerometro-x':[],'acelerometro-y':[],'acelerometro-z':[],'giroscopio-x':[],'giroscopio-y':[],'giroscopio-z':[]}#,'tmp':[]}
            x = np.arange(2500)
            
            plt.figure()
            #plt.suptitle("{}".format(path),fontsize=12)
            #nome = input('Digite o nome: ')
            #plt.suptitle("Eixo X - Giroscópio - {} Hz".format(nome),fontsize=12)

            for line in csv_reader:
                #ESTE PROGRAMA SIMPLESMENTE IGNORA A PRIMEIRA LINHA DO ARQUIVO .TXT. NUMA FUTURA VERSAO PODE-SE UTILIZAR
                #OS DADOS DELA PARA IDENTIFICAR OS EIXOS NA DICT 'd'
                if line_count !=0:
                    index = 0
                    for axis in d:
                        d[axis].append(int(line[index]))
                        index += 1
                line_count += 1

            index = 1
            for axis in d:
                plt.subplot(3,2,index)
                plt.plot(x,d[axis])
                plt.ylim(-32768,32767)
                plt.xlim(0,cap)
                plt.title(axis)
                index += 1

            #plt.plot(x,d['gyx'])
            #plt.ylim(-15000,15000)
            #plt.xlim(0,cap)
            #plt.title('Eixo X - Acelerômetro')

            

            if not(os.path.isdir("./python_server/image/{}".format(folder))):
                os.mkdir("./python_server/image/{}".format(folder))
            print("SALVANDO PLOT '{}.png'".format(path))
            plt.tight_layout()
            plt.savefig("./python_server/image/{}/{}.png".format(folder,path), dpi = 600)
    
    print("PRONTO. VERIFIQUE A PASTA 'image' PARA VISUALIZAR")

elif(mainMenu == '3'):
    tutorialMenu = '1'
    while(tutorialMenu != '0'):
        print("3-UTILIZAÇÃO DO SOFTWARE")
        tutorialMenu = input("""
    **MENU**
    0-RETORNAR AO MENU PRINCIPAL
    1-CÓDIGO DA CAPTURA
    2- --
    3- --
    4-A terminar....

    >>> """)
        clear()
        if(tutorialMenu == '1'):
            print("""
    Os codigos das capturas sao utilizados para que elas possam ser 
    separadas em pastas de acordo com suas características, como as
    bombas envolvidas e a frequencia.

    Esses codigos sao compostos por:
    X - tanque de onde vem o fluxo; tambem identifica a bomba
    Y - tanque para onde vai o fluxo
    ZZ - frequencia
    
    B - fluxo bloqueado
    V - bomba a vazio
    
    Por exemplo, se uma captura é realizada do tanque 4 para o tan-
    que 0, a uma frequencia de 30Hz, com a bomba a vazio, seu codi-
    go será '4030V'.""")
            input("Pressione ENTER para retornar ao menu.")

elif(mainMenu == '4'):
    print('4-SAIR')
    #break
input("PRESSIONE ENTER PARA PROSSEGUIR.")