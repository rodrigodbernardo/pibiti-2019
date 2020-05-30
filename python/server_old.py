#PIBITI 2019

#VERSAO C - SISTEMA COMPLETO
#CONTROLE VIA SERVIDOR PYTHON

#SERVIDOR WEBSOCKET EM PYTHON (UTILIZANDO ASYNCIO E WEBSOCKETS)
#AUTOR: RODRIGO D. B. DE ARAUJO


##OBS: todo o sistema foi feito com uma venv rodando na pasta acima à deste arquivo.
# Por isso os caminhos podem parecer confusos

# As funcoes que ainda nao estao funcionando como eu gostaria sao
# - OTA(atualizacao do firmware sem fios)
# - Plotagem em tempo real dos dados dos sensores

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
    global menu
    global capt_remaining
    global capt_code

    if(menu != '2'):
        clear()
        print("\nSENSOR CONECTADO!\n")

        menu = input("""
**MENU**

1-CAPTURA DE DADOS
2-ANALISE EM TEMPO REAL
3-REINICIAR SENSOR
4-VOLTAR AO MENU PRINCIPAL

>>> """)

        clear()

    if (menu == "1"):
        if (capt_remaining == 0):
            print("\n1-CAPTURA DE DADOS")
            
            capt_code = input("CODIGO DA CAPTURA[XYZZ](Recomendado: teste): ")
            if not (os.path.isdir("./python_server/capture/{}".format(capt_code))):
                print("PASTA INESISTENTE. CRIANDO UMA NOVA...")
                os.mkdir("./python_server/capture/{}".format(capt_code))
                print("OK! SEUS ARQUIVOS SERAO SALVOS em ./capture/{}'. ESCOLHA-A POSTERIORMENTE NA OPCAO \n'PLOTAR DADOS CAPTURADOS' PARA UMA VISUALIZACAO GRAFICA".format(capt_code))
            capt_remaining = int(input("\nCADA CAPTURA CONTEM 2500 AMOSTRAS\nNUMERO DE CAPTURAS(Recomendado: 1): "))
        
        print(">>> {} <<<".format(capt_remaining))
        capt_remaining -= 1

        #ENVIA O COMANDO PARA O MICROCONTROLADOR ATE RECEBER UMA RESPOSTA POSITIVA
        response = ""
        while(response != "OK"):
            await websocket.send("1-CAP")
            response = await websocket.recv()

        response = ""
        print("CAPTURANDO DADOS...")

        captureTime = await websocket.recv()
        print("TEMPO DE CAPTURA: {} ms\n".format(captureTime))
        print("RECEBENDO DADOS. AGUARDE...")
        
        now = datetime.now()
        current_time = now.strftime("%Y_%m_%d-%H_%M_%S")
        file = open("./python_server/capture/{}/{}-{}-{}.txt".format(capt_code,current_time,captureTime,capt_code),"w+")

        for i in range(2500):
            if (i == 0):
                file.write("AcX,AcY,AcZ,GyX,GyY,GyZ,Tmp\n")

            dado = await websocket.recv()
            file.write("{}".format(dado))

            file.write("\n")

        print("RECEBIMENTO COMPLETO. ARQUIVO SALVO EM ~../python_server/capture/{}/{}-{}-{}.txt".format(capt_code,current_time,captureTime,capt_code))
        file.close()


    elif menu == "2":

        await websocket.send("2-VIS")

        while True:
            try:
                #print(await websocket.recv())
                

                ani = FuncAnimation(plt.gcf(),animate,interval = 1)

                #plt.plot(x,y)
                plt.tight_layout()
                plt.show()

            except:
                pass

    elif menu == "3":
        print("\n3-REINICIAR SENSOR")
        await websocket.send("3-REB")
        print("REINICIANDO SENSOR. AGUARDE...")
        menu = "0"
    
    elif menu == "4":
        print("\n4-VOLTAR AO MENU PRINCIPAL")
        asyncio.get_event_loop().stop()
    
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
while True:

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
        break
    input("PRESSIONE ENTER PARA PROSSEGUIR.")