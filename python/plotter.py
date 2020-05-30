### PLOTTER

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

folders = []

while(True):
    print('MENU\n')
    print('1 - plotar unica captura')
    print('2 - comparação entre capturas')
    menu = input('>>> ')

    if(menu == '1'):
        continue

    elif(menu == '2'):
        numCapturas = int(input('Quantas capturas deseja comparar?'))

        for captura in range (numCapturas):
            error = 1
            while(error):
                entrada = input('Digite o nome da captura {}: '.format(captura+1))
                
                if (os.path.isdir("./python_server/capture/{}".format(entrada))):
                    folders.append(entrada)
                    error = 0
                else:
                    print("PASTA INESISTENTE. TENTE NOVAMENTE.\n\n")

        numAmostras = int(input('Quantas amostras deseja plotar em cada captura? '))
        selectAxis = input('Qual eixo deseja comparar? ')

       # for folderPath in folders:
        plt.figure()
        for folderIndex in range(numCapturas):
            #for filePath in glob.glob("./python_server/capture/{}/*.txt".format(folders[folderIndex])):
            #with open(filePath) as csv_file:
                #filePath = filePath.replace("./python_server/capture/{}".format(folders[folderIndex]),'').replace(".txt",'')

            with open("./python_server/capture/{}/{}.txt".format(folders[folderIndex],folders[folderIndex])) as csv_file:    
                csv_reader = csv.reader(csv_file, delimiter=',')
                line_count = 0 

                d={'acx':[],'acy':[],'acz':[],'gyx':[],'gyy':[],'gyz':[]}#,'tmp':[]}
                
                #axisVector = []
                
                
                
                #plt.suptitle("{}".format(path),fontsize=12)
                #nome = input('Digite o nome: ')
                #plt.suptitle("Eixo X - Giroscópio - {} Hz".format(nome),fontsize=12)

                for line in csv_reader:
                    #ESTE PROGRAMA SIMPLESMENTE IGNORA A PRIMEIRA LINHA DO ARQUIVO .TXT. NUMA FUTURA VERSAO PODE-SE UTILIZAR
                    #OS DADOS DELA PARA IDENTIFICAR OS EIXOS NA DICT 'd'
                    if line_count !=0:
                        
                        axisIndex = 0
                        for axis in d:
                            if(axis == selectAxis):
                                d[axis].append(int(line[axisIndex]))
                            else:    
                                axisIndex += 1

                    line_count += 1

            x = np.arange(2500)
            plt.subplot(numCapturas,1,folderIndex)
            plt.plot(x,d[selectAxis])
            plt.ylim(-32768,32767)
            plt.xlim(0,numAmostras)
            plt.title(selectAxis)
            #index += 1

        finalPath = "./python_server/image/"
        for n in range(numCapturas):
            finalPath.append(folders[n])
            finalPath.append('-')
        finalPath.append('{}-{}.png'.format(numAmostras,selectAxis))
        plt.savefig(finalPath, dpi = 600)
