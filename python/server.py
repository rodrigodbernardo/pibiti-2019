import asyncio#
import websockets#
from datetime import datetime#
import time#
import socket#
import numpy as np
import matplotlib.pyplot as plt
import csv
import glob#
import os#

#Pacotes para windows
if os.name == 'nt':
    import msvcrt

clear = lambda: os.system('cls')
menu = "0"

x = []

async def clientConnected(websocket, path):
    clear()

    print('Conexão bem sucedida!')

    print('\nMenu Principal\n')
    print('1-Captura')
    print('2-Análise em tempo real')
    print('3-Reiniciar sensor')
    mainMenu = input('>>> ')                                                                #verificar se é um dos números

    try:
        await asyncio.wait_for(websocket.send(mainMenu), timeout=5.0)
    except asyncio.TimeoutError:
        print('O cliente parou de responder. Reiniciando o servidor.')
        return

    clear()
    if(mainMenu == '1'):
        print('1-captura\n')

        captureCode = input('Código da captura: ')                                          #verificar se a pasta existe, criar se nao existir
        numberOfCaptures = input('Número de capturas: ')                                    #verificar se é número
        numberOfSamples = input('Número de amostras em cada captura: ')                     #verificar se é número; numero maximo é 2500

        try:
            await asyncio.wait_for(websocket.send(numberOfSamples), timeout=5.0)
        except asyncio.TimeoutError:
            print('O cliente parou de responder. Reiniciando o servidor.')
            return

        await websocket.send(numberOfCaptures)

        numberOfCaptures = int(numberOfCaptures)
        numberOfSamples = int(numberOfSamples)

        print('Iniciando captura. Não desligue o sistema.')

        for iteration in range (numberOfCaptures):
            print('Captura {} iniciada.'.format(iteration+1))

            # Aguarda um tempo enquanto o sensor captura os dados.

            timeOfCapture = await websocket.recv()
            print('Tempo de Captura: {} ms.' .format(timeOfCapture))
            print('Recebendo dados. Aguarde...')

            now = datetime.now()
            current_time = now.strftime(("%Y%m%d_%H-%M-%S"))
            
            timeOfCapture = ("{:04d}".format(int(timeOfCapture)))
            file = open("./python/capture/{}_{}_A{:04d}_C{:03d}_{}ms.txt".format(captureCode,current_time,numberOfSamples,iteration+1,timeOfCapture),"w")

            for i in range(numberOfSamples):
                if (i == 0):
                    file.write("AcX,AcY,AcZ,GyX,GyY,GyZ,Tmp\n")

                dado = await websocket.recv()
                file.write("{}\n".format(dado))

            file.close()

            timeOfDownload = await websocket.recv()
            print('Tempo de download: {} ms.'.format(timeOfDownload))
            print('Captura {} concluída.\n'.format(iteration+1))

        #   separei o plot da aquisição de dados para passar o menor tempo possível capturando os dados;
        #   FUTURO: separar o salvamento do arquivo da aquisição de dados, para deixar o processo mais rápido
        print('Processo concluído. Preparando para plotar dados...')

        #   Procura todos os arquivos .txt na pasta das capturas para realizar a plotagem.
        #   FUTURO: trocar isso por guardar os dados das capturas numa lista e só entao plotar e gravar ao mesmo tempo
        for capturePath in glob.glob('./python/capture/*.txt'):            
            with open(capturePath) as csv_file:
                capturePath = capturePath.replace('capture','image').replace('.txt','.png')
                if os.path.exists(capturePath):
                    continue

                csv_reader = csv.reader(csv_file, delimiter = ',')

                
                #   opção: utilizar dicionario
                #   y = {acx:[],acy:[],acz:[],gyx:[],gyy:[],gyz:[]}
                #   ** não utilizei dicionários aqui por que seus elementos não têm indexação                
                y = [[[],[]] , [[],[]] , [[],[]]]   # y é uma matriz 3x2 onde cada elemento é um vetor que guardará os dados das capturas.
                #axis = (('Acelerômetro - X','Acelerômetro - Y'),('Acelerômetro - Z','Giroscópio - X'),('Giroscópio - Y','Giroscópio - Z'))
                
                #   Lê linha a linha do arquivo e salva em y.
                #
                next(csv_reader)    #pula a primeira linha (cabeçalho)
                for line in csv_reader:
                    index = 0
                    for rows in range (3):
                        for cols in range (2):
                            y[rows][cols].append(line[index])
                            index += 1

                x = np.arange(len(y[0][0]))
                fig, plots = plt.subplots(nrows=3,ncols=2,sharex=True)

                #   Percorre y plotando os dados do eixo correspondente
                #
                for rows in range(3):
                    for cols in range (2):
                        plots[rows,cols].plot(x,y[rows][cols])
                        #plots[rows,cols].set_title(axis[rows][cols])

                
                plots[0,0].set_title('Acelerômetro - X')
                plots[0,1].set_title('Acelerômetro - Y')
                plots[1,0].set_title('Acelerômetro - Z')
                plots[1,1].set_title('Giroscópio - X')
                plots[2,0].set_title('Giroscópio - Y')
                plots[2,1].set_title('Giroscópio - Z')

                print('Salvando imagem em {}.'.format(capturePath))
                plt.savefig('{}'.format(capturePath),dpi = 200)

        print('Processo finalizado.')
            
    elif(mainMenu == '2'):
        print("Preparando análise. Pressione 'ESC' para sair.")
        while True:
            print(await websocket.recv())

            if msvcrt.kbhit():
                if ord(msvcrt.getch()) == 27:
                    print('Análise finalizada. Fazendo reconexão...')
                    break
    
    elif mainMenu == '3':
        pass
        
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

clear()

print("****PIBITI-2019****")

mainMenu = input("""
***MENU PRINCIPAL***

1-Conectar ao sensor
2-Plotar dados
3-Manual
4-Sair

>>> """)

clear()

if(mainMenu == '1'):
    print("1-Conectar ao sensor")
    print("Criando servidor em: {}:{}".format(myip,port))
    w_server = websockets.serve(clientConnected, myip, port)

    print("\nAguardando conexão...")
    asyncio.get_event_loop().run_until_complete(w_server)
    asyncio.get_event_loop().run_forever()

elif(mainMenu == '2'):
    
    print('2-Plotar dados')
    
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
            
            y = [[[],[]] , [[],[]] , [[],[]]]

            index = 0

            next(csv_reader)
            for line in csv_reader:
                for rows in range (3):
                    for cols in range (2):
                        y[rows][cols].append(line[index])
                        index += 1

            x = np.arange(len(y[0][0]))

            fig, plots = plt.subplots(nrows=3,ncols=2)
            fig.suptitle = 'captura'
            fig.ylim(-32768,32767)

            for rows in range(3):
                for cols in range (2):
                    plots[rows,cols].plot(x,y[rows][cols])

            if not(os.path.isdir("./python_server/image/{}".format(folder))):
                os.mkdir("./python_server/image/{}".format(folder))
            print("SALVANDO PLOT '{}.png'".format(path))
            
            #plt.subplots_adjust(left=0.125, bottom=0.1, right=0.9, top=0.9, wspace=0.2, hspace=5)
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