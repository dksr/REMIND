#############################################################################
#   get_temporal_blanket.py
#
#   Created: 06/09/09
#   Author : Krishna Sandeep Reddy Dubba    
#   Email  : scksrd@leeds.ac.uk
#   Purpose: 
#
#   This program is part of the CO-FRIEND project, partially funded by the
#   European Commission under the 7th Framework Program.
#
#   See http://www.co-friend.net
#
#   (C) University of Leeds - Co-friend Consortium
#############################################################################

import logging
import os
import sys

from base.utils.base_utils import *
from base.ilp.logic import *

log = logging.getLogger("lam.base.ilp.get_temporal_blanket")

def get_temporal_blanket(bg_KB, ex_KB):
    """This is the positive examples cookie cutter"""
    ind = 0   
    count = 1
        
    blankets = []
    # After finding blankets, bg_KB is changed in to one of these 
    # blankets based on which example we are dealing with.
    bg_ints = set(bg_KB.clauses['int'])
    deictic_ints  = []
    deictic_zones = []        
    
    # get list of deictic ints. Assume it is at the end of pos examples
    for ex in ex_KB:
        deictic_ints.append(ex.args[-1])
        deictic_zones.append(ex.args[0])
        
    for intv in deictic_ints:
        if intv in bg_ints:
            bg_ints.remove(intv)
            
    for ex in ex_KB:
        # Assuming 'int' is the last argument
        [X1, Y1] = ex.args[-1].args            
        [X1, Y1] = [X1.op, Y1.op]

        # put the deictic interval first.
        # Should I avoid relations with diectic interval here?
        blankets.append({'int':[]})

        # Add deictic interval to the blanket
        blankets[ind]['dint'] = ex.args[-1]
        
        # Get all interval related to the diectic intervals

        for bg_int in bg_ints:
            [X2, Y2] = bg_int.args
            [X2, Y2] = [X2.op, Y2.op]
            if X2 != Y2:
                if X2 > X1 and Y2 < Y1:                  # during
                    blankets[ind]['int'].append(bg_int)
                elif X1 > X2 and Y1 < Y2:                # during
                    blankets[ind]['int'].append(bg_int)    
                elif X2 > X1 and Y2 > Y1 and X2 < Y1:    # overlaps
                    blankets[ind]['int'].append(bg_int)
                elif X2 < X1 and Y2 < Y1 and X1 < Y2:    # overlaps
                    blankets[ind]['int'].append(bg_int)
                elif X1 == X2 and Y2 < Y1:               # starts
                    blankets[ind]['int'].append(bg_int)
                elif X2 > X1 and Y1 == Y2:               # finishes
                    blankets[ind]['int'].append(bg_int)
                    
        # Now get all the spatial relations that have these selected intervals   
        exclude_keys = ['zone','obj','int','dsur','dcon','drel_1']
        tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
        exclude_keys = set(flatten([tempr,exclude_keys]))
        valid_ints = set(blankets[ind]['int'])
        
        # Get objs connected to deictic regions
        objs_con_deictic_zone = set([])
        deictic_spr = set(['dsur', 'dcon'])
        for key in bg_KB.clauses.keys():
            if key in deictic_spr:
                for e in bg_KB.clauses[key]:
                    if e.args[-1] in valid_ints:                    
                        if e.args[0] in deictic_zones:
                            objs_con_deictic_zone = objs_con_deictic_zone.union([e.args[1]])
                        elif e.args[1] in deictic_zones:   
                            objs_con_deictic_zone = objs_con_deictic_zone.union([e.args[0]])                            
        
        for key in bg_KB.clauses.keys():
            if key not in exclude_keys:
                for e in bg_KB.clauses[key]:
                    # 'and' replaced by 'or' to increase spatial relations in blankets
                    if e.args[-1] in valid_ints and (e.args[0] in objs_con_deictic_zone \
                       or e.args[1] in objs_con_deictic_zone):
                        try:
                            blankets[ind][key].append(e)
                        except KeyError:
                            blankets[ind][key] = [e]
        
        keys = set(['dint', 'obj', 'loader', 'aircraft', 'transporter', 'ground_power_unit', \
                    'conveyor_belt', 'mobile_stair', 'person'])
        for key in keys:
            try:
                blankets[ind][key] = bg_KB.clauses[key][:]
            except KeyError:
                pass
               
        blankets[ind]['zone'] = []  
        # The contents of blankets[ind]['zone'] affect the bottom clause
        # Just copy the zones that are connected to the diectic region
        for fact in bg_KB.clauses['zone']:
            if fact.args[0] in objs_con_deictic_zone:
                blankets[ind]['zone'].append(fact)
                
        ind += 1     
    return blankets   


def get_temporal_blanket_ped(bg_KB, ex_KB, ignore_deictic_zone=False):
    """This is the positive examples cookie cutter"""
    ind = 0   
    count = 1
        
    blankets = []
    # After finding blankets, bg_KB is changed in to one of these 
    # blankets based on which example we are dealing with.
    bg_ints = set(bg_KB.clauses['int'])
    deictic_ints  = []
        
    for intv in deictic_ints:
        if intv in bg_ints:
            bg_ints.remove(intv)
            
    for ex in ex_KB:
        zones    = [i.op for i in ex.args[0].args]
        # Assuming 'int' is the last argument
        [X1, Y1] = ex.args[-1].args
        [X1, Y1] = [X1.op, Y1.op]

        # put the deictic interval first.
        # Should I avoid relations with diectic interval here?
        blankets.append({'int':[]})

        # Add deictic interval to the blanket
        blankets[ind]['dint'] = ex.args[-1]
        
        # Get all interval related to the diectic intervals

        for bg_int in bg_ints:
            [X2, Y2] = bg_int.args
            [X2, Y2] = [X2.op, Y2.op]
            
            # This if condition is not necessary as some primitive events are instantaneous, 
            # so lasts only one second and so X2 == Y2 in this case            
            #if X2 != Y2:
            if X2 > X1 and Y2 < Y1:                  # during
                blankets[ind]['int'].append(bg_int)
            elif X1 > X2 and Y1 < Y2:                # during
                blankets[ind]['int'].append(bg_int)    
            elif X2 > X1 and Y2 > Y1 and X2 < Y1:    # overlaps
                blankets[ind]['int'].append(bg_int)
            elif X2 < X1 and Y2 < Y1 and X1 < Y2:    # overlaps
                blankets[ind]['int'].append(bg_int)
            elif X1 == X2 and Y2 < Y1:               # starts
                blankets[ind]['int'].append(bg_int)
            elif X2 > X1 and Y1 == Y2:               # finishes
                blankets[ind]['int'].append(bg_int)
                    
        # Now get all the spatial relations that have these selected intervals   
        exclude_keys = ['zone','obj','int','dsur','dcon','drel_1']
        tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
        exclude_keys = set(flatten([tempr,exclude_keys]))
        valid_ints = set(blankets[ind]['int'])
        
        for key in bg_KB.clauses.keys():
            if key not in exclude_keys:
                for e in bg_KB.clauses[key]:
                    # intv should be in deictic interval and if there are more than three args
                    # i.e. more than two objs, the second obj should be in valid zones.
                    if ignore_deictic_zone:
                        # If ignore deictic zone is true don't check if zone in relational fact 
                        # is present in required zones
                        if e.args[-1] in valid_ints:
                            try:
                                blankets[ind][key].append(e)
                            except KeyError:
                                blankets[ind][key] = [e]
                    else:
                        if e.args[-1] in valid_ints and (len(e.args) < 3 or e.args[1].op in zones):
                            try:
                                blankets[ind][key].append(e)
                            except KeyError:
                                blankets[ind][key] = [e]
                            
        keys = set(['dint', 'obj', 'zone'])
        for key in keys:
            try:
                blankets[ind][key] = bg_KB.clauses[key][:]
            except KeyError:
                pass
                                                             
        ind += 1     
    return blankets   

def get_temporal_blanket_ped_str_int(bg_KB, ex_KB, ignore_deictic_zone=False):
    """This is the positive examples cookie cutter"""
    ind = 0   
    count = 1
        
    blankets = []
    # After finding blankets, bg_KB is changed in to one of these 
    # blankets based on which example we are dealing with.
    bg_ints = set(bg_KB.clauses['int'])
    log.info(repr(ex_KB))
    deictic_ints  = []
    
    for intv in deictic_ints:
        if intv in bg_ints:
            bg_ints.remove(intv)
            
    for ex in ex_KB:        
        zones    = [i.op for i in ex.args[0].args]
        log.info(repr(zones))
        # Assuming 'int' is the last argument. But if there is only one argument, then .args returns the innermost arguments
        # Bloody bug need to fix this
        try:
            [X1, Y1] = ex.args[-1].args
        except ValueError:
            [X1, Y1] = ex.args
        [X1, Y1] = [X1.op, Y1.op]
        
        # put the deictic interval first.
        # Should I avoid relations with diectic interval here?
        blankets.append({'int':[]})

        # Add deictic interval to the blanket
        blankets[ind]['dint'] = ex.args[-1]
        blankets[ind]['str_int'] = []
        
        # This one is for opra. Because in opra we don't have a way to get objs in deictic interval.
        blankets[ind]['dobjs'] = []
        blankets[ind]['size'] = 0
        
        # Get all interval related to the diectic intervals
        for bg_int in bg_ints:
            [X2, Y2] = bg_int.args
            [X2, Y2] = [X2.op, Y2.op]
            str_intv = Expr('int', [''.join(['t', str(X2)]), ''.join(['t',str(Y2)])])
            blankets[ind]['str_int'].append(str_intv)
            # This if condition is not necessary as some primitive events are instantaneous, 
            # so lasts only one second and so X2 == Y2 in this case            
            #if X2 != Y2:
            if X2 > X1 and Y2 < Y1:                  # during
                blankets[ind]['int'].append(bg_int)
            elif X1 > X2 and Y1 < Y2:                # during
                blankets[ind]['int'].append(bg_int)    
            elif X2 > X1 and Y2 > Y1 and X2 < Y1:    # overlaps
                blankets[ind]['int'].append(bg_int)
            elif X2 < X1 and Y2 < Y1 and X1 < Y2:    # overlaps
                blankets[ind]['int'].append(bg_int)
            elif X1 == X2 and Y2 < Y1:               # starts
                blankets[ind]['int'].append(bg_int)
            elif X1 == X2 and Y2 > Y1:               # starts
                blankets[ind]['int'].append(bg_int)
            elif X2 > X1 and Y1 == Y2:               # finishes
                blankets[ind]['int'].append(bg_int)
            elif X2 < X1 and Y1 == Y2:               # finishes
                blankets[ind]['int'].append(bg_int)     
            elif X1 == X2 and Y1 == Y2:              # equals 
                blankets[ind]['int'].append(bg_int)
                    
        # Now get all the spatial relations that have these selected intervals   
        exclude_keys = ['zone','obj','int','dsur','dcon','drel_1','str_int']
        tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
        exclude_keys = set(flatten([tempr,exclude_keys]))
        valid_ints = set(blankets[ind]['int'])
        log.info('Valid ints: ' + repr(valid_ints))
        
        for key in bg_KB.clauses.keys():
            if key not in exclude_keys:
                for e in bg_KB.clauses[key]:
                    log.debug('processing ' + repr(e) + ' for blankets')
                    intv = e.args[-1]
                    [X1, Y1] = intv.args
                    [X1, Y1] = [X1.op, Y1.op]
                    # Get the string version of the interval
                    str_intv = Expr('int', [''.join(['t', str(X1)]), ''.join(['t',str(Y1)])])
                    spr = Expr(e.op, e.args[:-1] + [(str_intv)])
                    # intv should be in deictic interval and if there are more than three args
                    # i.e. more than two objs, the second obj should be in valid zones.
                    if ignore_deictic_zone:
                        # If ignore deictic zone is true don't check if zone in relational fact 
                        # is present in required zones
                        if intv in valid_ints:
                            log.info('Adding ' + repr(e) + ' to blankets')
                            blankets[ind]['size'] += 1
                            try:
                                blankets[ind][key].append(spr)
                            except KeyError:
                                blankets[ind][key] = [spr]
                    else:
                        if intv in valid_ints and (len(e.args) < 3 or (e.args[0].op in zones or e.args[1].op in zones)):
                            log.info('Adding ' + repr(e) + ' to blankets')
                            blankets[ind]['size'] += 1
                            try:
                                blankets[ind][key].append(spr)
                            except KeyError:
                                blankets[ind][key] = [spr]
                            blankets[ind]['dobjs'].append(e.args[0])    

        keys = set(['dint', 'obj', 'zone'])
        for key in keys:
            try:
                blankets[ind][key] = bg_KB.clauses[key][:]
            except KeyError:
                pass
            except TypeError:
                log.debug('Found dict for this key instead of list. Converting to list: ' + repr(key))
                bg_KB.clauses[key] = bg_KB.clauses[key].keys()
                blankets[ind][key] = bg_KB.clauses[key][:]
                pass
    return blankets   
