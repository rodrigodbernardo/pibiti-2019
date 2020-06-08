print('1-captura\n')
while (True):
    try:
        captureCode = input('Código da captura: ')                                              #verificar se a pasta existe, criar se nao existir
        numberOfCaptures = int(input('Número de capturas(1-99): '))                                    #verificar se é número
        numberOfSamples = int(input('Número de amostras em cada captura(1-2500): '))                     #verificar se é número; numero maximo é 2500
    
        if not (numberOfCaptures in range(1,100) and numberOfSamples in range(1,2501)):
            raise Exception
    except TypeError:
        print('Entrada incorreta. Tente novamente\n')
    except Exception:
        print('Fora do alcance. Tente novamente\n')
    else:
        break

print('Fora do loop')