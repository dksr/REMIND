import math
import numpy as np
import matplotlib
import matplotlib.cm as cm
import matplotlib.pyplot as plt

def distance(x1, y1, x2, y2):
    # Calculates the length of a line in 2d space.
    return math.sqrt(math.pow(x1 - x2, 2) + math.pow(y1 - y2, 2))

def find_angle(x1,y1,x2,y2,x3,y3):
    a = distance(x1,y1,x2,y2)
    b = distance(x1,y1,x3,y3)
    c = distance(x2,y2,x3,y3)
    
    try:
        cos1 = (math.pow(a,2) + math.pow(b,2) - math.pow(c,2))/ (2 * a * b)        
    except ZeroDivisionError:
        cos1 = 1
    try:
        cos2 = (math.pow(a,2) + math.pow(c,2) - math.pow(b,2))/ (2 * a * c)
    except ZeroDivisionError:
        cos2 = 1
            
    ang1 = math.acos(round(cos1,2))
    ang2 = math.acos(round(cos2,2))
    ang = min(ang1, ang2)
    return ang

def gen_logistic(A, K, B, Q, M, t, v=0.5):
    num = K - A
    den = 1 + Q*(math.exp(-B*(t-M)))
    den = math.pow(den, 1/v)
    return A + num/den
    

A = 0
K = 1
B = 6
Q = 0.01
M = 0.01

x1, y1 = 4,0
x2, y2 = 6,0

delta = 1
x = np.arange(0, 11.0, delta)
y = np.arange(0, 4.0, delta)
X, Y = np.meshgrid(x, y)
Z = np.zeros((X.shape[0],X.shape[1]))

for i in range(y.shape[0]):
    for j in range(x.shape[0]):
        ang = find_angle(x1,y1,x2,y2,j,i)
        dist1 = distance(x1, y1, x[j], y[i])
        dist2 = distance(x2, y2, x[j], y[i])
        avg_dist = (dist1+dist2)/2
        if avg_dist == 0:
            avg_dist = 0.0000001
        Z[i,j] = 2*gen_logistic(A, K, B, Q, M, ang) + 1/avg_dist
        
plt.figure()
plt.contourf(X,Y,Z)
#plt.gca().invert_yaxis()
plt.colorbar()
plt.show()
        






    