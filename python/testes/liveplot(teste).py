import numpy as np
from itertools import count
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
#import pandas as pd
import random
import math


plt.figure(1)
x = []
y1 = []
y2 = []
y3 = []
y4 = []

index = count()

def animate(i):
    x.append(next(index))
    y1.append(math.sin(x[-1]/10))
    y2.append(-math.sin(x[-1]/10))
    y3.append(math.cos(x[-1]/10))
    y4.append(-math.cos(x[-1]/10))

    plt.subplot(3,2,1)
    plt.plot(x,y1)
    plt.xlim(x[-1]-100,x[-1]+10)

    plt.subplot(3,2,2)
    plt.plot(x,y2)
    plt.xlim(x[-1]-100,x[-1]+10)

    plt.subplot(3,2,3)
    plt.plot(x,y3)
    plt.xlim(x[-1]-100,x[-1]+10)

    plt.subplot(3,2,4)
    plt.plot(x,y4)
    plt.xlim(x[-1]-100,x[-1]+10)

    #plt.plot(x,y)
    #plt.plot(x,y2)
    #plt.plot(x,y3)

#fig, (ax1,ax2) = plt.subplots(2,1)
ani = FuncAnimation(plt.gcf(),animate,interval = 10)

#plt.plot(x,y)
plt.tight_layout()
plt.show()