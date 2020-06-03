a = [[[],[]],[[],[]],[[],[]]]

b = [0,1,2,3,4,5]

for k in range (5):
    index = 0
    for i in range (3):
        for j in range(2):
            a[i][j].append(b[index])
            index+=1

print (a)