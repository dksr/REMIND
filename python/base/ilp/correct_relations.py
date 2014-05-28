
#file_name = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/all/load_arr/la_cof_all_cam2_clean_qtc_protos_2_type.b'
#write_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/all/load_arr/la_cof_all_cam2_clean_qtc_protos_2_type_correct.b'

#f = open(file_name)
#wf = open(write_file, 'w')

#for line in f:
    #if "obj_86842, obj_85899" in line:
        #continue
    #else:
        #wf.write(line)
#f.close()
#wf.close()
        
#print 'over'

import os
import sys

base_py = '/home/csunix/dksreddy/work/base/src/python/'
sys.path.append(base_py)
sys.path.append(base_py + 'ilp/data')
cof_py  = '/home/csunix/dksreddy/work/cofriend/src/python/'
sys.path.append(cof_py)
sys.path.append(cof_py + 'visualization') 

import pyximport; pyximport.install()
import random
import cPickle as pickle
from utils import *
from logic import *

#from pyswip import Prolog

#prolog_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/load_arr/la_cof_all_cam2_clean_qtc_protos_4_type.b'
#prolog = Prolog()
#prolog.consult(prolog_file)
#print 'Prolog file consulted'



 #TROLLEY_ARRIVES
#q = 'rel_1(V_4, R, int(V_5, T)), rel_2(V_4, R, int(V_6, V_7)), meets(int(V_6, V_7), int(V_5, T))' 
#q = 'trol_arr(Obj1, Obj2, int(I1, I2)), trol_leave(Obj1, Obj2, int(I3, I4))' 


#before(int(N, O), int(J, K))
#q = 'trol_arr(H, I, int(I1, I2)), trol_leave(H, I, int(I3, I4))'
#q = 'sur(A, B, int(I1,I1))'#, transporter(A)' #rel_1(A, B, int(I3,I4))
#a = list(prolog.query(q))

#q = 'rel_1(A, B, int(I1,I1))'#, transporter(A)' #rel_1(A, B, int(I3,I4))
#b = list(prolog.query(q))

#q = 'rel_2(A, B, int(I1,I1))'#, transporter(A)' #rel_1(A, B, int(I3,I4))
#c = list(prolog.query(q))

#q = 'rel_3(A, B, int(I1,I1))'#, transporter(A)' #rel_1(A, B, int(I3,I4))
#c = list(prolog.query(q))

#q = 'rel_4(A, B, int(I1,I1))'#, transporter(A)' #rel_1(A, B, int(I3,I4))
#c = list(prolog.query(q))

#q = 'con(A, B, int(I1,I1))'#, transporter(A)' #rel_1(A, B, int(I3,I4))
#d = list(prolog.query(q))

#q_res = list(flatten([a,b,c,d]))

file_name = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/all/cof_all_cam2_clean_qtc_protos_4_type.b'
write_file = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/all/cof_all_cam2_clean_qtc_protos_4_type_correct.b'

f = open(file_name)
wf = open(write_file, 'w')

for line in f:
    ind = line.find(").")
    if ind > 0 :
        l = line[0:ind+1]
        exp = expr(l)
        if len(exp.args) > 2:
            if exp.args[2].args[0] == exp.args[2].args[1]:
                print exp
                continue
            else:
                wf.write(line)
        else:
            wf.write(line)
wf.close()  
f.close()
print 'over'        