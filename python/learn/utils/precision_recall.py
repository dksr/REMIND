import numpy as np
import os
import sympy
import sys

from copy import deepcopy

sys.path.append('/home/csunix/visdata/cofriend/working_code/lib/python2.7/site-packages/')

from base.vis.prettytable  import PrettyTable as PT


def relative_overlap(detect,occur):
    from datetime import timedelta
    
    [x1,y1] = detect
    [x2,y2] = occur
    if x2 < x1 and y2 > x1 and y1 < y2:
        return 1
    if x1 < x2 and y2 < x1 and y2 < y1:
        return 1
    den = max([x1,x2,y1,y2]) - min([x1,x2,y1,y2])
    if isinstance(den, timedelta):
        # if detect and occur are tuples of  timestamps
        den = den.seconds
    num = min([y1,y2]) - max([x1,x2])
    if isinstance(num, timedelta):
        num = num.seconds
        
    if num < 0:
        num = 0
    if den > 0:
        return num/float(den)
    else:
        return 0
    
def precision_recall(sol,GT,GTNames,required_RO=0.2):
    """
    Sol is a dictionary where sol[turnaround][eventname] =  list of [start,end] pairs
    GT is dictionary of ground truth in same format as sol
    GTNames is a list of all eventnames in the vocab (just for convenience as not all turnarounds contain all events but we should check anyway.
    Required_RO is the relative overlap required for a hit _ default 0.2 as in VIRAT challenge

    Returns:
    scores: a dictionary of [precision,recall,TP+FN] pairs
    misses: dictionary which stores a list of turnarounds where the GT was not covered for each event.
    """
    #scores = np.zeros([GTNames.__len__(),4]) 
    pt = PT(["Event", "Recall", "Precision", "TP", "FP"])
    pt.align["Event"] = "l" 
    format = "%.2f" 
    try:
        GTNames.remove('Aircraft_Positioned')
        GTNames.remove('Catering')
        GTNames.remove('GPU_Removing')
    except ValueError:
        pass
    #scores = np.zeros([GTNames.__len__(),2]) 
    scores = {}
    misses = dict()
    tempGT = deepcopy(GT)
    for i,event in enumerate(GTNames):
        TP=0;FP=0;FN=0;sq_prec=0;n=0
        misses[event] = []
        scores[event] = {}
        for turnaround in sol.keys():
            gt_hits = np.zeros(1)
            this_prec=0
            good_detects = 0
            try:   
                FP += sol[turnaround][event].__len__()              
                gt_hits = np.zeros([sol[turnaround][event].__len__(),tempGT[turnaround][event].__len__()])
                for d,detect in enumerate(sol[turnaround][event]):      
                    #calculate figures for ROC                   
                    try:                       
                        for o,occur in enumerate(tempGT[turnaround][event]):
                            if relative_overlap(detect,occur) > required_RO:
                                gt_hits[d,o] = 1
                    except KeyError:
                        pass
                if (gt_hits.shape > np.array([1,1])).all():
                    good_detects = np.array(sympy.Matrix(gt_hits).rref())[1].__len__()
                elif (gt_hits > 0).any():
                    good_detects = 1

                TP+=good_detects
                FP-=good_detects
            except KeyError:
                pass
            try:
                FN+=(tempGT[turnaround][event].__len__()-good_detects)
                #calculate the squared precision for summing to get variance
                try:
                    this_prec = good_detects/float(sol[turnaround][event].__len__())
                    n += 1
                    sq_prec += this_prec**2
                except ZeroDivisionError:pass

                for occur in tempGT[turnaround][event]:
                    occur_covered=0
                    try:
                        for d,detect in enumerate(sol[turnaround][event]):
                            if relative_overlap(detect,occur) > required_RO:
                                occur_covered=1

                    except KeyError:
                        pass
                    if not occur_covered:
                        misses[event].append(turnaround)

            except KeyError:
                pass               
                #print('no %s in %s'%(event,turnaround))  
        if TP > 0 or FN > 0:
           #recall
            scores[event]['recall'] = TP / float(TP+FN)
            try:
                #precision
                scores[event]['precision'] = TP / float(TP+FP)
            except ZeroDivisionError:
                scores[event]['precision'] = 0
            pt.add_row([event, format % scores[event]['recall'], format % scores[event]['precision'], TP, FP])

            #total number of true
            #scores[i,2]=TP+FN
            #precision_var
            #scores[i,3] = 100*(sq_prec - n*(scores[i,0])**2) /float(n)
    avg = {}
    tot_recall    = 0
    tot_precision = 0
    for e in scores:
        try:
            tot_recall    += scores[e]['recall']
            tot_precision += scores[e]['precision']
        except KeyError:
            continue        
    avg['recall'] = float(tot_recall)/len(scores)
    avg['precision'] = float(tot_precision)/len(scores)    
    return [scores,misses,avg,pt]


def roc(sol,GT,GTNames,required_RO=0.2):
    """
    Sol is a dictionary where sol[turnaround][eventname] =  list of [start,end] pairs
    GT is dictionary of ground truth in same format as sol
    GTNames is a list of all eventnames in the vocab (just for convenience as not all turnarounds contain all events but we should check anyway.
    Required_RO is the relative overlap required for a hit _ default 0.2 as in VIRAT challenge

    Returns:
    scores: a dictionary of [precision,recall,TP+FN] pairs
    misses: dictionary which stores a list of turnarounds where the GT was not covered for each event.
    """
    #scores = np.zeros([GTNames.__len__(),4]) 
    pt = PT(["Event", "TPR", "FPR"])
    format = "%.2f" 
    try:
        GTNames.remove('Aircraft_Positioned')
        GTNames.remove('Catering')
        GTNames.remove('PBB_Removing')
    except ValueError:
        pass
    #scores = np.zeros([GTNames.__len__(),2]) 
    scores = {}
    misses = dict()
    tempGT = deepcopy(GT)
    for i,event in enumerate(GTNames):
        TP=0;FP=0;FN=0;sq_prec=0;n=0
        misses[event] = []
        scores[event] = {}
        for turnaround in sol.keys():
            gt_hits = np.zeros(1)
            this_prec=0
            good_detects = 0
            try:   
                FP += sol[turnaround][event].__len__()              
                gt_hits = np.zeros([sol[turnaround][event].__len__(),tempGT[turnaround][event].__len__()])
                for d,detect in enumerate(sol[turnaround][event]):      
                    #calculate figures for ROC                   
                    try:                       
                        for o,occur in enumerate(tempGT[turnaround][event]):
                            if relative_overlap(detect,occur) > required_RO:
                                gt_hits[d,o] = 1
                    except KeyError:
                        pass
                if (gt_hits.shape > np.array([1,1])).all():
                    good_detects = np.array(sympy.Matrix(gt_hits).rref())[1].__len__()
                elif (gt_hits > 0).any():
                    good_detects = 1

                TP+=good_detects
                FP-=good_detects
            except KeyError:pass
            try:
                FN+=(tempGT[turnaround][event].__len__()-good_detects)
                #calculate the squared precision for summing to get variance
                try:
                    this_prec = good_detects/float(sol[turnaround][event].__len__())
                    n += 1
                    sq_prec += this_prec**2
                except ZeroDivisionError:pass

                for occur in tempGT[turnaround][event]:
                    occur_covered=0
                    try:
                        for d,detect in enumerate(sol[turnaround][event]):
                            if relative_overlap(detect,occur) > required_RO:
                                occur_covered=1

                    except KeyError:
                        pass
                    if not occur_covered:
                        misses[event].append(turnaround)

            except KeyError:
                pass               
                #print('no %s in %s'%(event,turnaround))  
        if TP > 0 or FP > 0:
           # True positive reate
            scores[event]['tpr'] = TP / float(TP+FN)
            try:
                #precision
                scores[event]['fpr'] = FP / float(TN+FP)
            except ZeroDivisionError:
                scores[event]['fpr'] = 0
            pt.add_row([event, format % scores[event]['tpr'], format % scores[event]['fpr']])

            #total number of true
            #scores[i,2]=TP+FN
            #precision_var
            #scores[i,3] = 100*(sq_prec - n*(scores[i,0])**2) /float(n)
    print pt
    #print GTNames
    return [scores,misses]

if __name__ == "__main__":
    import cPickle as pickle
    event_names = {   'AFT_Bulk_LoadingUnloading_Operation': 1, 
                       'AFT_CN_LoadingUnloading_Operation': 1, 
                       'FWD_CN_LoadingUnloading_Operation': 1, 
                       'FWD_Bulk_LoadingUnloading_Operation': 1, 
                       'Left_Refuelling': 1, 
                       'GPU_Positioning': 1, 
                       'GPU_Removing': 1, 
                       'PB_Positioning': 1, 
                       'Catering': 1, 
                       'Aircraft_Arrival': 1, 
                       'Aircraft_Positioned': 1, 
                       'Aircraft_Departure': 1, 
                       'PBB_Positioning': 1,
                       'PBB_Removing': 1, 
                      }
    GTNames = event_names.keys()
    #sol_file = '/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/sed_recognition_data_20110301_pr_format.p'
    #sol = pickle.load(open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/sed_recognition_data_20110301_pr_format.p'))
    sol = pickle.load(open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/relational_ped_data_type_correct_20101229_pr.p'))
    #sol = pickle.load(open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/par14_type_no_persons_sfe_db_gt_noVOZ_lujoined_20101229_pr.p'))
    #sol = pickle.load(open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/par21_type_sfe_db_gt_noVOZ_lujoined_2_pr.p'))
    #sol = pickle.load(open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/par25_rcc3_type_no_persons_correct_break_craftnotheavy_2_max_scores_pr.p'))    
    #GT = pickle.load(open('/home/csunix/visdata/cofriend/release/arc1_code/lam/data/db/GT/db_lujoined_gt_pickle.p'))
    #sol = pickle.load(open('/home/csunix/visdata/cofriend/working_code/data/db/GT/scenoir_learned_models_recognitions.p'))    
    #sol = pickle.load(open('/home/csunix/visdata/cofriend/working_code/data/db/sed_recognition_timestamps_20110301.p'))    
    GT = pickle.load(open('/home/csunix/visdata/cofriend/working_code/data/db/GT/db_lujoined_gt_timestamps_pickle.p'))
    precision_recall(sol,GT,GTNames,required_RO=0.2)