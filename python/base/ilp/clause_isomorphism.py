import cPickle as pickle
import os
import sys

base_py = '/home/csunix/dksreddy/work/base/src/python/'
sys.path.append(base_py)
sys.path.append(base_py + 'vis')
sys.path.append(base_py + 'utils/math')
from utils import *
from logic import *
from Levenshtein import median
from xpermutations import xcombinations
from prettytable import PrettyTable as PT

class Blanket(object):
    def __init__(self,ins):
        spr = []
        tmpr = []
        objs = set([])
        self.obj_ints = []
        #self.code = []
        self.code = ''
        spr_rel = ['con','sur','rel_1']
        temp_rel = ['before','after','during','meets','starts','overlaps']
        
        # Get all spatial relations
        for rel in spr_rel:
            try:
                spr.append(ins[rel])
            except KeyError:
                pass
            
        # Get all temporal relations            
        for rel in temp_rel:
            try:
                tmpr.append(ins[rel])
            except KeyError:
                pass
                
        spr = list(flatten(spr))
        tmpr = list(flatten(tmpr))
        # Get all objects
        
        for rel in spr:
            objs = objs.union(rel.args[0:2])
        
        # get interactions of all possible obj combinations    
        for c in xcombinations(list(objs), 2): 
            ints = {}
            ints['rel'] = []
            ints['sp_rel'] = []
            ints['temp_rel'] = []
                        
            for rel in ins['zone']:
                if rel in c:          
                    zrel = Expr('zone',rel)  
                    if zrel not in ints['rel']: 
                        ints['rel'].append(zrel) 
            for rel in ins['loader']:
                if rel in c:
                    lrel = Expr('loader',rel)  
                    if lrel not in ints['rel']: 
                        ints['rel'].append(lrel)                     
            for rel in ins['transporter']:
                if rel in c:
                    trel = Expr('transporter',rel)  
                    if trel not in ints['rel']: 
                        ints['rel'].append(trel)                     
            for rel in ins['aircraft']:
                if rel in c:
                    arel = Expr('aircraft',rel)  
                    if arel not in ints['rel']: 
                        ints['rel'].append(arel) 
                                    
            c = set(c)
            ints['objs'] = c
            for rel in spr:
                if set(rel.args[0:2]) == c:
                    ints['sp_rel'].append(rel)
                    ints['rel'].append(rel)
            
            # Collect all intervals        
            intv = set([])
            for rel in ints['sp_rel']:
                intv = intv.union([rel.args[-1]])
            # Add interval relations that have interval in the intervals of spatial
            # relations of these two objs
            for rel in tmpr:
                if set(rel.args).issubset(intv):
                    ints['temp_rel'].append(rel)
                    ints['rel'].append(rel)
            
            self.obj_ints.append(ints)            
            code = ''
            for rel in ints['rel']:
                #code = code + rel.op[0]
                self.code = self.code + rel.op[0]
               
            #if code != '': self.code.append(code)           
                              
skip_events = ['Container_Back_Loading','Refuelling','Container_Front_Loading','Container_Front_Unloading']
#skip_events.append('Handler_Deposites_Chocks')
#skip_events.append('Aircraft_Arrival')
skip_events.append('Aircraft_Departure')
skip_events.append('Jet_Bridge_Positioning')
skip_events.append('Jet_Bridge_Parking')
skip_events.append('VRAC_Back_Loading')
skip_events.append('VRAC_Back_Unloading')
            
#skip_events = ['GPU_Arrival','Container_Back_Loading','Refuelling','Aircraft_Departure','Container_Front_Unloading']

data_path = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/new_gt_with_zone_IBL_1protos/' 
#file_name = 'msh2.p'
file_name = 'msh_all.p'

ins = pickle.load(open(data_path + file_name))
blankets = {}
codes = {}
medians = {}
pt = PT(["Event", "#pos examples", "TP", "FP"])
pt.align["Event"] = "l" # Left align event names

for event in ins.keys():    
    blankets[event] = []
    codes[event] = []    
    #print event
    if event in skip_events:
        continue
    for ex in ins[event]:
        blankets[event].append(Blanket(ex))      
    for instance in blankets[event]:
        if instance.code != '':
            codes[event].append(instance.code)
    medians[event] = median(codes[event])    
    #print event

print 'read solution'
