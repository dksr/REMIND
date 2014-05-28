#!/usr/bin/env python

import cPickle as pickle
import logging
import os
import pyximport; pyximport.install()
import sys

base_py = '/home/csunix/dksreddy/work/base/src/python/'
sys.path.append(base_py)
sys.path.append(base_py + 'utils')
sys.path.append(base_py + 'utils/math')
sys.path.append(base_py + 'vis')

from cUtils import unique
from k_fold_cross_validation import k_fold_cross_validation
from Logging import initialize_logging
from logic import *
from optparse import OptionParser
from prettytable import PrettyTable as PT
from Timer import Timer
from utils import *
from xpermutations import permutations

def clause_distance(clause_dict1, clause_dict2):
    logger = logging.getLogger('project')    
    lgg_clause_ind = 1
    lgg_dict_ind   = 2
    lgg_clause_dis_ind = 3
    min_dis = 1000
    min_case = []
    all_matches = []
    struct_dis = 0
    try: 
        del clause_dict1['int']
        del clause_dict2['int']
    except KeyError:
        pass
    all_keys = set(clause_dict1.keys()).union(set(clause_dict2.keys()))
    for key in all_keys:
        l1 = unique(clause_dict1.get(key,[]))
        l2 = unique(clause_dict2.get(key,[]))
        l1 = filter_before(l1)
        l2 = filter_before(l2)
        # Find structural distance. Add this at the end to min_dis
        struct_dis += 5 * abs(len(l1) - len(l2))
        if len(l1) != 0 and len(l2) != 0:
            if len(l1) > 15:
                l1 = l1[0:len(l1)/(len(l1)/10)]
            if len(l2) > 15:
                l2 = l2[0:len(l2)/(len(l2)/10)]
            if len(l1) + len(l2) > 8:
                l1 = l1[0:len(l1)/3]
                l2 = l2[0:len(l2)/3]
          
            print len(l1), '  ', len(l2)
            if len(l1) > len(l2):
                # zip only needs top len(l2) elements. So no need to have
                # full permutations.
                list1 = list(flatten(list(permutations(l1, len(l2)))))
                list2 = l2
                
            elif len(l1) <= len(l2):
                list1 = l1
                list2 = list(flatten(list(permutations(l2, len(l1)))))
                
            l = [list1, list2]
            
            all_matches.append(zip(*l))
    pos_cases = combinations_from_multiple_lists(all_matches)
    # This case occurs if one of the example is empty.
    # Just return min_dis, but this return distance should actually
    # depend on the structure of the other example
    if len(pos_cases) == 1 and len(pos_cases[0]) is 0:
        return [min_dis, None] 
    dis_list = []
    for case in pos_cases:
        clause_dict = {}
        clause1 = [match[0] for match in case]
        clause2 = [match[1] for match in case]
        
        for match in case:
            clause_dict[match[0]] = match[1]
        lgg_clause = match_clauses(clause_dict, sol_lgg=[], sub_dict={}, dis=0)
        
        dis = lgg_clause[lgg_clause_dis_ind]
        dis_list.append(dis)
        if dis < min_dis:
            min_dis = dis
            min_case = case        
    return [min_dis + struct_dis, struct_dis, min_case]
    #return [min_dis, struct_dis, min_case]

def filter_before(bef_list):
    # Reduce before relations by restricting the interval
    if len(bef_list) is 0 or bef_list[0].op != 'before':
        return bef_list
    new_bef_list = []
    for rel in bef_list:
        [int1, int2] = rel.args
        [X1, Y1] = int1.args
        [X2, Y2] = int2.args
        if (X2.op - Y1.op) < 50:       #FIXME
            new_bef_list.append(rel)
    return new_bef_list
            
def combinations_from_multiple_lists(a):
    r=[[]]
    for x in a:
        if len(x) is not 0:
            t = []
            for y in x:
                for i in r:
                    t.append(i+[y])
            r = t
    return r

def train(train_data):
    all_distances = []
    for ex1 in train_data:
        dis = []
        struct_dis = []
        for ex2 in train_data:
            if ex1 == ex2:
                continue
            dis.append(clause_distance(ex1, ex2)[0])
            temp_dis = clause_distance(ex1, ex2)[1]
            #struct_dis.append(clause_distance(ex1, ex2)[1])
            if temp_dis is not None:            
                struct_dis.append(temp_dis)
        #all_distances.append(float(sum(dis))/(len(train_data)-1))
        
        all_distances.append(float(sum(struct_dis))/(len(train_data)-1))
    min_dis_ex = all_distances.index(min(all_distances))
    hyp = train_data[min_dis_ex]
    max_dis = max(all_distances)
    min_dis = min(all_distances)
    avg_dis = mean(all_distances)
    return [hyp, max_dis, avg_dis, min_dis]

def test(hyp, max_dis, avg_dis, min_dis, test_data, test_type):
    logger = logging.getLogger('project')    
    if test_type is 'pos':
        threshold = max_dis
    else:
        threshold = avg_dis
            
    score = 0
    dis = []
    sdis = []
    ind = 0    
    for ex in test_data:                
        logger.debug("testing example: " + repr(ind)) 
        dis.append(clause_distance(hyp, ex)[0])
        if dis[-1] <= threshold:
            score += 1    
        ind += 1    
    logger.debug(dis)
    return float(score)/len(test_data)


# **************************** MAIN ***********************
def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    # Setup command line options
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-l", "--logdir", dest="logdir", default=".", help="log DIRECTORY (default ./)")
    parser.add_option("-f", "--logfile", dest="logfile", default="project.log", help="log FILE (default project.log)")
    parser.add_option("-v", "--loglevel", dest="loglevel", default="debug", help="logging level (debug, info, error)")    
    parser.add_option("-q", "--quiet", action="store_true", dest="quiet", help="do not log to console")
    parser.add_option("-n", "--filequiet", action="store_true", dest="fquiet", help="do not log to file")
    parser.add_option("-c", "--clean", dest="clean", action="store_true", default=False, help="remove old log file")
    
    # Process command line options
    (options, args) = parser.parse_args(argv)

    # Setup logger format and output locations
    logger = initialize_logging(options)

    ti = Timer()
    
    skip_events = []
    skip_events = ['Container_Back_Loading','Refuelling','Container_Front_Loading','Container_Front_Unloading']
    #skip_events.append('Handler_Deposites_Chocks')
    #skip_events.append('Aircraft_Arrival')
    #skip_events.append('Aircraft_Departure')
    skip_events.append('Jet_Bridge_Positioning')
    skip_events.append('Jet_Bridge_Parking')
    #skip_events.append('VRAC_Back_Loading')
    #skip_events.append('VRAC_Back_Unloading')
    #skip_events.append('Push_Back_Positioning')
    
    #skip_events = ['GPU_Arrival','Container_Back_Loading','Refuelling','Aircraft_Departure','Container_Front_Unloading']
    
    data_path = '/usr/not-backed-up/cofriend/data/progol/clean_qtc/new_gt_with_zone_IBL_1protos/' 
    #file_name = 'msh2.p'
    file_name = 'msh_all.p'
    
    ins = pickle.load(open(data_path + file_name))
    result = {}
    
    #Visualize results as a table
    pt = PT(["Event", "#pos examples", "TP", "FP"])
    pt.align["Event"] = "l" # Left align event names
     
    for event in ins.keys():    
        if event in skip_events:
            continue
        logger.info(event)
        ti.start()
        pos_score = 0
        neg_score = 0
         
        # Get negative test data
        all_events = ins.keys()
        all_events.remove(event)
        for ev in skip_events:
            all_events.remove(ev)
        neg_test_data = [ins[i] for i in all_events]
        neg_test_data = list(flatten(neg_test_data))
        
        for train_data, pos_test_data in k_fold_cross_validation(ins[event], len(ins[event])):
            [hyp, max_dis, avg_dis, min_dis] = train(train_data)
            logger.info('-----------------')
            logger.info('Avg: ' + repr(avg_dis) +  '   Max: ' + repr(max_dis))
            pos_score += test(hyp, max_dis, avg_dis, min_dis, pos_test_data, 'pos')
            neg_score += test(hyp, max_dis, avg_dis, min_dis, neg_test_data, 'neg')
        pt.add_row([event, len(ins[event]), float(pos_score)/len(ins[event]), float(neg_score)/len(ins[event])])
        result[event] = [float(pos_score)/len(ins[event]), float(neg_score)/len(ins[event])]    
        ti.stop()
        duration = ti.getTimeStr()
        logger.info("Time Taken: " + duration)
    logger.info(pt)
    
if __name__ == "__main__":
    sys.exit(main(['-l', '/tmp/', '-c', '-v', 'info', '-fq', '-f', 'clause_matching.log']))

        