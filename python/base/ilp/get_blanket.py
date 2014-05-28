#############################################################################
#   get_blanket.py
#
#   Created: 12/06/09
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


from base.base_constants   import RBB, GBB, YBB, BBB, CBB, BBT, RBT, CBT, YBT, MBT, GBT, \
                                  GT, YT, MT, RT, CT, RESET
from base.utils.base_utils import *
from base.ilp.logic import *

log = logging.getLogger("lam.base.ilp.get_blanket")

def get_ints(intv):
    # Returns interval as list of start and end
    return [intv.args[0].op, intv.args[1].op]

def get_blanket(self, intv, ints_list, zone):
    """This is the sliding window generator"""
    ind = 0   
    count = 1
    
    # bg_ints is a list of sorted intervals in list form.
    bg_ints = ints_list
    [X1, Y1] = intv            
    #[X1, Y1] = [X1.op, Y1.op]
    blanket = {'int':[]}
    # Get ints within this intv
    start = 0
    i = j = 0
    for ex in bg_ints:
        # Find all intv within and overlaping the window interval
        [X2, Y2, tmp] = ex
        if X2 == Y2:
            continue
        #[X2, Y2] = [X2.op, Y2.op]
        if X1 > X2 and X1 < Y2 and start is 0:
            i = bg_ints.index(ex)
            start = 1
        elif X1 > X2 and X1 > Y2:
            i = bg_ints.index(ex)
        elif X2 > X1 and X2 < Y1 and Y2 > Y1:    
            j = bg_ints.index(ex)
    if j is 0 :
        temp_int_list = bg_ints[i:]
    else:
        temp_int_list = bg_ints[i:j]
    # Get only the intv expression list as the list is already sorted
    for intv in temp_int_list:
        blanket['int'].append(intv[2])
                
    # Now get all the spatial relations that have these selected intervals   
    
    exclude_keys = ['zone','obj','int','loader','transporter','aircraft']
    tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
    exclude_keys = list(flatten([tempr,exclude_keys]))
    for key in self.bg_KB.clauses.keys():
        if key not in exclude_keys:
            for ex in self.bg_KB.clauses[key]:
                if ex.args[-1] in blanket['int']:                            
                    try:
                        blanket[key].append(ex)
                    except KeyError:
                        blanket[key] = [ex]
    
    # get objs connected to given zone
    objs_con_zone = set([zone])
    for key in blanket:
        if key not in exclude_keys:        
            for fact in blanket[key]:
                if fact.args[0].op == zone:
                    objs_con_zone = objs_con_zone.union([fact.args[1]])
                elif fact.args[1].op == zone:   
                    objs_con_zone = objs_con_zone.union([fact.args[0]])
    
    # find facts where two objests are not in obj list connected to deictic zones        
    remove_facts = []
    for key in blanket:
        if key not in exclude_keys:        
            for fact in blanket[key]:            
                if fact.args[0] not in objs_con_zone and fact.args[1] not in objs_con_zone:
                    remove_facts.append(fact)
    # remove the facts
    for fact in remove_facts:
        blanket[fact.op].remove(fact)

    valid_ints = {}
    for key in blanket.keys():
        if key not in exclude_keys:
            for fact in blanket[key]:
                valid_ints[fact.args[-1]] = 1
           
    # Now remove all ints that are not present in spatial relations
    # This code is because some bug in matlab code. Spurious ints are inserted in
    # the .pl file.
    
    duplicate_ints = blanket['int'][:]  
    for intv in duplicate_ints:
        if intv not in valid_ints:
            blanket['int'].remove(intv)        
    
    keys = ['zone', 'loader', 'aircraft', 'transporter'] 
    for key in keys:
        try:
            blanket[key] = self.bg_KB.clauses[key][:]
        except KeyError:
            pass
    
    # Now freshly calculate the temporal relations among them.
    # Should I avoid relations with diectic interval here?
    # In that case need to change the connectivity check.            
    for intv in blanket['int']:
        [X1, Y1] = intv.args
        [X1, Y1] = [X1.op, Y1.op]
        temp_intv = blanket['int'][:]
        temp_intv.remove(intv)
        for new_intv in temp_intv:
            [X2, Y2] = new_intv.args
            [X2, Y2] = [X2.op, Y2.op]
            if Y1 < X2 - 1: #and (X2 - Y1) < 150:       #FIXME
                try: 
                    blanket['before'].append(Expr('before',[intv,new_intv]))
                except KeyError:
                    blanket['before'] = [Expr('before',[intv,new_intv])]
            elif X1 > X2 and Y1 < Y2:
                try:
                    blanket['during'].append(Expr('during',[intv,new_intv]))
                except KeyError:
                    blanket['during'] = [Expr('during',[intv,new_intv])]
            elif X2 > X1 and X2 < Y1 and Y1 < Y2:
                try:
                    blanket['overlaps'].append(Expr('overlaps',[intv,new_intv]))
                except KeyError:
                    blanket['overlaps'] = [Expr('overlaps',[intv,new_intv])]
            elif X2 == Y1 + 1 or X2 == Y1:
                # This is meets or touch
                try:
                    blanket['meets'].append(Expr('meets',[intv,new_intv]))
                except KeyError:
                    blanket['meets'] = [Expr('meets',[intv,new_intv])]
            elif X1 == X2: # and Y1 < Y2:
                # 'start and finish are symmetric, so avoid one relation.
                try:
                    if Expr('starts',[new_intv,intv]) not in blanket['starts']:                        
                        blanket['starts'].append(Expr('starts',[intv,new_intv]))
                except KeyError:  
                    blanket['starts'] = [Expr('starts',[intv,new_intv])]
            elif Y1 == Y2: # and (X1 < X2 or X2 < X1):                        
                try:
                    if Expr('finishes',[new_intv,intv]) not in blanket['finishes']:
                        blanket['finishes'].append(Expr('finishes',[intv,new_intv]))
                except KeyError:                            
                    blanket['finishes'] = [Expr('finishes',[intv,new_intv])]
    return blanket


def get_event_blanket(video_dict):
    """This generates temporal blanket for the whole turn around where events are objects
    OR in other words finds temporal and spatial relations among events when a dict whose 
    keys are events and values are list of intervals when they occured.        
    """
    ind = 0   
    count = 1
    
    blanket = {}
    bg_ints = []
    blz_events = ['Aircraft_Arrival', 'Aircraft_Departure', 'VRAC_Back_Loading', 'VRAC_Back_Unloading']
    flz_events = ['GPU_Arrival']
    fz_events  = ['Push_Back_Positioning', 'Handler_Deposites_Chocks']
    events_by_zones = [blz_events, flz_events, fz_events]
    blz = 'obj_119084'
    flz = 'obj_119085'
    fz  = 'obj_119086'
    
    for evnt in video_dict.keys():
        # Change the first alphabet to lower case or it will be considered
        # as variable in logic.py
        evnt_name = evnt[0].lower() + evnt[1:]
        blanket[evnt_name] = []
        ind = 0
        for intv in video_dict[evnt]:
            if not isinstance(intv, Expr):
                intv_expr = Expr('int', [intv[0], intv[1]])
            else: 
                intv_expr = intv    
            # If there are more than one instance of an event in the turnaround,
            # subscript them with number
            if len(video_dict[evnt]) > 1:
                evn = evnt_name + '_' + repr(ind)
                ind += 1
            else:
                evn = evnt_name

            # Add events to blanket.
            # Ex: holds(gPU_Arrival, int(12, 45)).
            blanket[evnt_name].append(Expr(evnt_name, [evn, intv_expr]))
            # Now add ints
            try:    
                blanket['int'].append(intv_expr)
            except KeyError:
                blanket['int'] = [intv_expr]
            
          
    #blz_events = ['Aircraft_Arrival', 'Aircraft_Departure', 'VRAC_Back_Loading', 'VRAC_Back_Unloading']
    #flz_events = ['GPU_Arrival']
    #fz_events  = ['Push_Back_Positioning', 'Handler_Deposites_Chocks']
    # Get spatial relations between the events. Taking care of the order of events.
    # Example run in the comments
    processed_events = []
    ind = -1;
    for i in events_by_zones:    
        # This is comment. For i in [blz_events, flz_events, fz_events] 
        ind += 1
        for j in events_by_zones[ind:]:
            # For j in [flz_events, fz_events]
            for k in i:
                # For k in ['Aircraft_Arrival', 'Aircraft_Departure', 'VRAC_Back_Loading', 'VRAC_Back_Unloading']
                if k in video_dict.keys():
                    for l in j:
                        # For l in ['GPU_Arrival']
                        if l == k:
                            continue
                        if l in video_dict.keys() and set([k,l]) not in processed_events:
                            # Flag is always true here as I am taking care of the events order
                            processed_events.append(set([k,l]))
                            [spr, flag] = spr_between_events(k, l)
                            evnt_k = k[0].lower() + k[1:]
                            evnt_l = l[0].lower() + l[1:]
                            for evnt1 in blanket[evnt_k]:
                                for evnt2 in blanket[evnt_l]:    
                                    try:
                                        blanket[spr].append(Expr(spr,[evnt1.args[0], evnt2.args[0]]))     
                                    except KeyError:
                                        blanket[spr] = [Expr(spr,[evnt1.args[0], evnt2.args[0]])]    
                
    # Now freshly calculate the temporal relations among them.
    for intv in blanket['int']:
        [X1, Y1] = intv.args
        [X1, Y1] = [X1.op, Y1.op]
        temp_intv = blanket['int'][:]
        temp_intv.remove(intv)
        plain_intv = [X1, Y1]
        for new_intv in temp_intv:
            [X2, Y2] = new_intv.args
            [X2, Y2] = [X2.op, Y2.op]
            new_plain_intv = [X2, Y2]
            if Y1 < X2 - 1: #and (X2 - Y1) < 150:       #FIXME
                try: 
                    blanket['before'].append(Expr('before',[plain_intv,new_plain_intv]))
                except KeyError:
                    blanket['before'] = [Expr('before',[plain_intv,new_plain_intv])]
            elif X1 > X2 and Y1 < Y2:
                try:
                    blanket['during'].append(Expr('during',[plain_intv,new_plain_intv]))
                except KeyError:
                    blanket['during'] = [Expr('during',[plain_intv,new_plain_intv])]
            elif X2 > X1 and X2 < Y1 and Y1 < Y2:
                try:
                    blanket['overlaps'].append(Expr('overlaps',[plain_intv,new_plain_intv]))
                except KeyError:
                    blanket['overlaps'] = [Expr('overlaps',[plain_intv,new_plain_intv])]
            elif X2 == Y1 + 1 or X2 == Y1:
                # This is meets or touch
                try:
                    blanket['meets'].append(Expr('meets',[plain_intv,new_plain_intv]))
                except KeyError:
                    blanket['meets'] = [Expr('meets',[plain_intv,new_plain_intv])]
            elif X1 == X2: # and Y1 < Y2:
                # 'start and finish are symmetric, so avoid one relation.
                try:
                    if Expr('starts',[new_plain_intv,plain_intv]) not in blanket['starts']:                        
                        blanket['starts'].append(Expr('starts',[plain_intv,new_plain_intv]))
                except KeyError:  
                    blanket['starts'] = [Expr('starts',[plain_intv,new_plain_intv])]
            elif Y1 == Y2: # and (X1 < X2 or X2 < X1):                        
                try:
                    if Expr('finishes',[new_plain_intv,plain_intv]) not in blanket['finishes']:
                        blanket['finishes'].append(Expr('finishes',[plain_intv,new_plain_intv]))
                except KeyError:                            
                    blanket['finishes'] = [Expr('finishes',[plain_intv,new_plain_intv])]
     
    return blanket

def get_event_blanket_bak(video_dict):
    """This generates temporal blanket for the whole turn around where events are objects
    OR in other words finds temporal and spatial relations among events when a dict whose 
    keys are events and values are list of intervals when they occured.        
    """
    ind = 0   
    count = 1
    
    blanket = {}
    bg_ints = []
    blz_events = ['Aircraft_Arrival', 'Aircraft_Departure', 'VRAC_Back_Loading', 'VRAC_Back_Unloading']
    flz_events = ['GPU_Arrival']
    fz_events  = ['Push_Back_Positioning', 'Handler_Deposites_Chocks']
    events_by_zones = [blz_events, flz_events, fz_events]
    blz = 'obj_119084'
    flz = 'obj_119085'
    fz  = 'obj_119086'
    
    for evnt in video_dict.keys():
        # Change the first alphabet to lower case or it will be considered
        # as variable in logic.py
        evnt_name = evnt[0].lower() + evnt[1:]
        blanket[evnt_name] = []
        ind = 0
        for intv in video_dict[evnt]:
            if not isinstance(intv, Expr):
                intv_expr = Expr('int', [intv[0], intv[1]])
            else: 
                intv_expr = intv    
            # If there are more than one instance of an event in the turnaround,
            # subscript them with number
            if len(video_dict[evnt]) > 1:
                evn = evnt_name + '_' + repr(ind)
                ind += 1
            else:
                evn = evnt_name

            # Add events to blanket.
            # Ex: holds(gPU_Arrival, int(12, 45)).
            blanket[evnt_name].append(Expr(evnt_name, [evn, intv_expr]))
          
    #blz_events = ['Aircraft_Arrival', 'Aircraft_Departure', 'VRAC_Back_Loading', 'VRAC_Back_Unloading']
    #flz_events = ['GPU_Arrival']
    #fz_events  = ['Push_Back_Positioning', 'Handler_Deposites_Chocks']
    # Get spatial relations between the events. Taking care of the order of events.
    # Example run in the comments
    processed_events = []
    ind = -1;
    for i in events_by_zones:    
        # This is comment. For i in [blz_events, flz_events, fz_events] 
        ind += 1
        for j in events_by_zones[ind:]:
            # For j in [flz_events, fz_events]
            for k in i:
                # For k in ['Aircraft_Arrival', 'Aircraft_Departure', 'VRAC_Back_Loading', 'VRAC_Back_Unloading']
                if k in video_dict.keys():
                    for l in j:
                        # For l in ['GPU_Arrival']
                        if l == k:
                            continue
                        if l in video_dict.keys() and set([k,l]) not in processed_events:
                            # Flag is always true here as I am taking care of the events order
                            processed_events.append(set([k,l]))
                            [spr, flag] = spr_between_events(k, l)
                            evnt_k = k[0].lower() + k[1:]
                            evnt_l = l[0].lower() + l[1:]
                            for evnt1 in blanket[evnt_k]:
                                for evnt2 in blanket[evnt_l]:    
                                    try:
                                        blanket[spr].append(Expr(spr,[evnt1.args[0], evnt2.args[0]]))     
                                    except KeyError:
                                        blanket[spr] = [Expr(spr,[evnt1.args[0], evnt2.args[0]])]    
                
    # Now freshly calculate the temporal relations among them.
    for intv in blanket['int']:
        [X1, Y1] = intv.args
        [X1, Y1] = [X1.op, Y1.op]
        temp_intv = blanket['int'][:]
        temp_intv.remove(intv)
        for new_intv in temp_intv:
            [X2, Y2] = new_intv.args
            [X2, Y2] = [X2.op, Y2.op]
            if Y1 < X2 - 1: #and (X2 - Y1) < 150:       #FIXME
                try: 
                    blanket['before'].append(Expr('before',[intv,new_intv]))
                except KeyError:
                    blanket['before'] = [Expr('before',[intv,new_intv])]
            elif X1 > X2 and Y1 < Y2:
                try:
                    blanket['during'].append(Expr('during',[intv,new_intv]))
                except KeyError:
                    blanket['during'] = [Expr('during',[intv,new_intv])]
            elif X2 > X1 and X2 < Y1 and Y1 < Y2:
                try:
                    blanket['overlaps'].append(Expr('overlaps',[intv,new_intv]))
                except KeyError:
                    blanket['overlaps'] = [Expr('overlaps',[intv,new_intv])]
            elif X2 == Y1 + 1 or X2 == Y1:
                # This is meets or touch
                try:
                    blanket['meets'].append(Expr('meets',[intv,new_intv]))
                except KeyError:
                    blanket['meets'] = [Expr('meets',[intv,new_intv])]
            elif X1 == X2: # and Y1 < Y2:
                # 'start and finish are symmetric, so avoid one relation.
                try:
                    if Expr('starts',[new_intv,intv]) not in blanket['starts']:                        
                        blanket['starts'].append(Expr('starts',[intv,new_intv]))
                except KeyError:  
                    blanket['starts'] = [Expr('starts',[intv,new_intv])]
            elif Y1 == Y2: # and (X1 < X2 or X2 < X1):                        
                try:
                    if Expr('finishes',[new_intv,intv]) not in blanket['finishes']:
                        blanket['finishes'].append(Expr('finishes',[intv,new_intv]))
                except KeyError:                            
                    blanket['finishes'] = [Expr('finishes',[intv,new_intv])]
     
    return blanket

def get_event_blanket_for_test(video_dict):
    """This generates temporal blanket for the whole turn around where events are objects
    OR in other words finds temporal and spatial relations among events when a dict whose 
    keys are events and values are list of intervals when they occured.        
    """
    ind = 0   
    count = 1
    
    blanket = {}
    bg_ints = []
    blz_events = ['Aircraft_Arrival', 'Aircraft_Departure', 'VRAC_Back_Loading', 'VRAC_Back_Unloading']
    flz_events = ['GPU_Arrival']
    fz_events  = ['Push_Back_Positioning', 'Handler_Deposites_Chocks']
    events_by_zones = [blz_events, flz_events, fz_events]
    blz = 'obj_119084'
    flz = 'obj_119085'
    fz  = 'obj_119086'
    
    for evnt in video_dict.keys():
        # Change the first alphabet to lower case or it will be considered
        # as variable in logic.py
        evnt_name = evnt[0].lower() + evnt[1:]
        blanket[evnt_name] = []
        ind = 0
        for intv in video_dict[evnt]:
            if not isinstance(intv, Expr):
                intv_expr = Expr('int', [intv[0], intv[1]])
            else: 
                intv_expr = intv    
            # If there are more than one instance of an event in the turnaround,
            # subscript them with number
            if len(video_dict[evnt]) > 1:
                evn = evnt_name + '_' + repr(ind)
                ind += 1
            else:
                evn = evnt_name

            # Add events to blanket.
            # Ex: holds(gPU_Arrival, int(12, 45)).
            blanket[evnt_name].append(Expr(evnt_name, [evn]))
            try:  
                # This is to avoid using '#' in the mode declarations.
                blanket['holds'].append(Expr('holds', [evn, intv_expr]))
            except KeyError:
                blanket['holds'] = [Expr('holds', [evn, intv_expr])]
            
            try:    
                blanket['int'].append(intv_expr)
            except KeyError:
                blanket['int'] = [intv_expr]
                
    # Now freshly calculate the temporal relations among them.
    for intv in blanket['int']:
        [X1, Y1] = intv.args
        [X1, Y1] = [X1.op, Y1.op]
        temp_intv = blanket['int'][:]
        temp_intv.remove(intv)
        for new_intv in temp_intv:
            [X2, Y2] = new_intv.args
            [X2, Y2] = [X2.op, Y2.op]
            if Y1 < X2 - 1: #and (X2 - Y1) < 150:       #FIXME
                try: 
                    blanket['before'].append(Expr('before',[intv,new_intv]))
                except KeyError:
                    blanket['before'] = [Expr('before',[intv,new_intv])]
            elif X1 > X2 and Y1 < Y2:
                try:
                    blanket['during'].append(Expr('during',[intv,new_intv]))
                except KeyError:
                    blanket['during'] = [Expr('during',[intv,new_intv])]
            elif X2 > X1 and X2 < Y1 and Y1 < Y2:
                try:
                    blanket['overlaps'].append(Expr('overlaps',[intv,new_intv]))
                except KeyError:
                    blanket['overlaps'] = [Expr('overlaps',[intv,new_intv])]
            elif X2 == Y1 + 1 or X2 == Y1:
                # This is meets or touch
                try:
                    blanket['meets'].append(Expr('meets',[intv,new_intv]))
                except KeyError:
                    blanket['meets'] = [Expr('meets',[intv,new_intv])]
            elif X1 == X2: # and Y1 < Y2:
                # 'start and finish are symmetric, so avoid one relation.
                try:
                    if Expr('starts',[new_intv,intv]) not in blanket['starts']:                        
                        blanket['starts'].append(Expr('starts',[intv,new_intv]))
                except KeyError:  
                    blanket['starts'] = [Expr('starts',[intv,new_intv])]
            elif Y1 == Y2: # and (X1 < X2 or X2 < X1):                        
                try:
                    if Expr('finishes',[new_intv,intv]) not in blanket['finishes']:
                        blanket['finishes'].append(Expr('finishes',[intv,new_intv]))
                except KeyError:                            
                    blanket['finishes'] = [Expr('finishes',[intv,new_intv])]
     
    return blanket

def spr_between_events(event1, event2):
    # This returns the spatial relation between the events.
    # The order is important to reduce number of relations.
    # If the order is correct it returns spatial relation and also returns 
    # whether order is True(correct) or False(swapped).
    
    # blz_events = ['Aircraft_Arrival', 'Aircraft_Departure', 'VRAC_Back_Loading', 'VRAC_Back_Unloading']
    # flz_events = ['GPU_Arrival']
    # fz_events  = ['Push_Back_Positioning', 'Handler_Deposites_Chocks']

    blz = 'obj_119084'
    flz = 'obj_119085'
    fz  = 'obj_119086'
    
    event_zone_codes = {'GPU_Arrival':              fz,
                        'Handler_Deposites_Chocks': fz,
                        'Aircraft_Arrival':         blz,
                        'Jet_Bridge_Positioning':   fz,
                        'Container_Front_Unloading':flz,
                        'Container_Front_Loading':  flz,
                        'Push_Back_Positioning':    fz,
                        'Container_Back_Loading':   blz,
                        'Jet_Bridge_Parking':       fz,
                        'Aircraft_Departure':       blz,
                        'VRAC_Back_Unloading':      blz,
                        'Refuelling':               12,
                        'VRAC_Back_Loading':        blz}
                        
    if   set([event1, event2]) == set(['Aircraft_Arrival','Aircraft_Departure']):
        return 'same', True    
    elif set([event1, event2]) == set(['VRAC_Back_Unloading','VRAC_Back_Loading']):
        return 'same', True    
    elif set([event1, event2]) == set(['Container_Front_Unloading','Container_Front_Loading']):
        return 'same', True    
    elif set([event1, event2]) == set(['Jet_Bridge_Parking','Jet_Bridge_Positioning']):
        return 'same', True
    
    zone1 = event_zone_codes[event1]
    zone2 = event_zone_codes[event2]   
    if zone1 == zone2:
        return 'overlap', True    
    elif [zone1, zone2] == [blz, flz]:
        return 'north', True
    elif [zone1, zone2] == [flz, blz]:
        return 'north', False
    elif [zone1, zone2] == [flz, fz]:    
        return 'west', True
    elif [zone1, zone2] == [fz, flz]:    
        return 'west', False
    elif [zone1, zone2] == [blz, fz]:    
        return 'northwest', True
    elif [zone1, zone2] == [fz, blz]:    
        return 'northwest', False

def get_event_list_from_blanket(blanket):
    # get event list from blanket.
    # Assumes 'holds' predicate is present
    # Element in list is of form [int1, int2, event_name]
    event_list = []
    for key in blanket.keys():
        if key != 'holds':
            continue
        for fact in blanket[key]:
            event = fact[0].op
            int1  = fact[1].args[0].op
            int2  = fact[1].args[1].op
            event_list.append([int1, int2, event])
    return event_list    

def write_blankets(blankets, write_file):
    """For global model learning"""
    blanket_file = open(write_file, 'w')
    blanket_file.write(':- style_check(-discontiguous).\n')
    blanket_file.write('before(X1,Y1,X2,Y2) :- Y1 < X2 - 1.\n')
    data = {}

    def format_expr(exp):
        exp = exp.str.replace(', ',',')
        exp.replace(',ob',', ob')
        return exp.replace(',i',', i') + '.\n'
    ind = 0
                   
    # Collect the data from all the blankets for each predicate    
    for ex in blankets:
        for key in ex.keys():
            try:
                data[key] = data[key].union(set(ex[key]))
            except KeyError:
                data[key] = set(ex[key])
            
    # Now print the data in a file. No need of ints.        
    exclude_keys = ['holds']
    blz = 'obj_119084'
    flz = 'obj_119085'
    fz  = 'obj_119086'
    event_zone_codes = {'GPU_Arrival':              fz,
                    'Handler_Deposites_Chocks': fz,
                    'Aircraft_Arrival':         blz,
                    'Jet_Bridge_Positioning':   fz,
                    'Container_Front_Unloading':flz,
                    'Container_Front_Loading':  flz,
                    'Push_Back_Positioning':    fz,
                    'Container_Back_Loading':   blz,
                    'Jet_Bridge_Parking':       fz,
                    'Aircraft_Departure':       blz,
                    'VRAC_Back_Unloading':      blz,
                    'Refuelling':               blz,
                    'VRAC_Back_Loading':        blz}
    
    for key in data.keys():
        if key in exclude_keys:
            for item in data[key]:
                event = item.args[0]
                for ev in event_zone_codes.keys():
                    evnt_name = event.op[0].upper() + event.op[1:]
                    if ev in evnt_name:
                        e_name = ev[0].lower() + ev[1:]
                        new_item = Expr(e_name, item.args)
                        blanket_file.write(format_expr(new_item))
                           
    blanket_file.close()                
    log.debug('blanket file written')
    
def write_blankets_ILP(blankets, write_file):
    """For global model learning using ILP"""
    blanket_file = open(write_file, 'w')
    blanket_file.write(':- style_check(-discontiguous).\n')
    blanket_file.write('before(X1,Y1,X2,Y2) :- Y1 < X2 - 1.\n')
    data = {}

    def format_expr(exp):
        exp = exp.str.replace(', ',',')
        exp.replace(',ob',', ob')
        return exp.replace(',i',', i') + '.\n'

    exclude_keys = ['zone','obj','int']
    tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
    exclude_keys = list(flatten([tempr,exclude_keys]))
               
    # Collect the data from all the blankets for each predicate    
    for ex in blankets:
        for key in ex.keys():
            if key not in exclude_keys:
                try:
                    data[key] = data[key].union(set(ex[key]))
                except KeyError:
                    data[key] = set(ex[key])
            
    # Now print the data in a file. No need of ints.        
    blz = 'obj_119084'
    flz = 'obj_119085'
    fz  = 'obj_119086'
    event_zone_codes = {'GPU_Arrival':              fz,
                    'Handler_Deposites_Chocks': fz,
                    'Aircraft_Arrival':         blz,
                    'Jet_Bridge_Positioning':   fz,
                    'Container_Front_Unloading':flz,
                    'Container_Front_Loading':  flz,
                    'Push_Back_Positioning':    fz,
                    'Container_Back_Loading':   blz,
                    'Jet_Bridge_Parking':       fz,
                    'Aircraft_Departure':       blz,
                    'VRAC_Back_Unloading':      blz,
                    'Refuelling':               12,
                    'VRAC_Back_Loading':        blz}
    for key in data.keys():
        for item in data[key]:
            event_name = item.op[0].upper() + item.op[1:]
            if event_name in event_zone_codes.keys():
                blanket_file.write(format_expr(item))
                       
    blanket_file.close()                
    log.debug('blanket file written')

def write_blankets_zone(blanket, module, write_file):
    blanket_file = open(write_file, 'w')
    blanket_file.write(':- style_check(-discontiguous).\n')
    data = {}

    exclude_keys = ['obj','dobjs','int','dint','str_int','zone','start_end','size']
    tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
    exclude_keys = list(flatten([tempr,exclude_keys]))
    
    blanket_file.write('before(int(X1,Y1), int(X2,Y2))   :- Y1 < X2 - 1.\n'              )
    blanket_file.write('during(int(X1,Y1), int(X2,Y2))   :- X1 > X2, Y1 < Y2.\n'         )
    blanket_file.write('overlaps(int(X1,Y1), int(X2,Y2)) :- X2 > X1, X2 < Y1, Y1 < Y2.\n')
    blanket_file.write('meets(int(X1,Y1), int(X2,Y2))    :- X2 =:= Y1 + 1.\n'            )
    blanket_file.write('meets(int(X1,Y1), int(X2,Y2))    :- X2 =:= Y1.\n'                )
    blanket_file.write('starts(int(X1,Y1), int(X2,Y2))   :- X1 =:= X2.\n'                )
    blanket_file.write('finishes(int(X1,Y1), int(X2,Y2)) :- Y1 =:= Y2.\n'                )
    
    def format_expr(exp):
        exp = repr(exp).replace(', ',',')
        exp.replace(',ob',', ob')
        return exp.replace(',i',', i') + '.\n'
    ind = 0
    abolish_list = []               
    # Collect the data from all the blankets for each predicate    
    
    #for key in blanket:
        #data[key] = blanket[key]
        #if len(blanket[key]) is not 0:
            #abolish_list.append('abolish(' + key + ',' + repr(len(blanket[key][0].args)) + ')')        
            
    # Now print the data in a file. No need of ints.        
    data = blanket
    for key in data.keys():        
        if key not in exclude_keys:
            for item in data[key]:
                item_str = module + ':' + format_expr(item)
                blanket_file.write(item_str)
                           
    blanket_file.close()
    log.debug('blanket file written')   
    return abolish_list

def assert_blanket_to_prolog(blanket, prolog, module):
    # p.assertz('test1:(c(X):-a(X),b(X))')
    # prolog.assertz(module + ':- style_check(-discontiguous)'
    module = module + ':'
    exclude_keys = ['obj', 'int', 'dint', 'unknown', 'zone', 'start_end', 'str_int', 'size']
    tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
    exclude_keys = list(flatten([tempr,exclude_keys]))
    
    prolog.assertz(module + 'before(int(X1,Y1), int(X2,Y2))   :- Y1 < X2 - 1'               )
    prolog.assertz(module + 'during(int(X1,Y1), int(X2,Y2))   :- X1 > X2, Y1 < Y2'          )
    prolog.assertz(module + 'overlaps(int(X1,Y1), int(X2,Y2)) :- X2 > X1, X2 < Y1, Y1 < Y2' )
    prolog.assertz(module + 'meets(int(X1,Y1), int(X2,Y2))    :- X2 =:= Y1 + 1'             )
    #prolog.assertz(module + 'meets(int(X1,Y1), int(X2,Y2))    :- X2 =:= Y1'                 )
    prolog.assertz(module + 'starts(int(X1,Y1), int(X2,Y2))   :- X1 =:= X2'                 )
    prolog.assertz(module + 'finishes(int(X1,Y1), int(X2,Y2)) :- Y1 =:= Y2'                 )
    
    for key in blanket.keys():
        if key not in exclude_keys:
            for item in blanket[key]:
                prolog.assertz(module + repr(item))
    log.info(module + ' blanket ' + GBT + 'asserted ' + RESET + 'to Prolog')
    
def assert_blanket_to_prolog_str_int(blanket, prolog, module):
    # p.assertz('test1:(c(X):-a(X),b(X))')
    # prolog.assertz(module + ':- style_check(-discontiguous)'
    module = module + ':'
    tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps', 'size']
    exclude_keys = ['obj', 'int', 'dint', 'unknown', 'zone', 'start_end', 'str_int']
    exclude_keys = list(flatten([tempr,exclude_keys]))    
    
    for key in blanket.keys():
        if key not in exclude_keys:
            for item in blanket[key]:
                prolog.assertz(module + repr(item))
    log.debug(module + ' blanket ' + GBT + 'asserted ' + RESET + 'to Prolog')
    

def retract_blanket_from_prolog(blanket_keys, prolog, module):
    module = module + ':'
    tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
    spr   = ['sur', 'con', 'rel_1']
    
    for key in blanket_keys:
        if key in tempr:
            q = 'retractall(' + module + key + '(int(X1,Y1), int(X2,Y2)))'
        elif key in spr:
            q = 'retractall(' + module + key + '(X, Y, int(U, V)))'
        elif key == 'int':
            q = 'retractall(' + module + key + '(X, Y))'
        elif key == 'obj':
            q = 'retractall(' + module + key + '(X))'            
        list(prolog.query(q))
    log.info(module + ' blanket ' + RBT + 'retracted ' + RESET + 'from Prolog')
    
def get_intv_from_interpretation(interpretation):
    """Get interval that defines the interpretation. Basically min and max of all time points
    in the input interpretation"""
    exclude_keys = ['zone','obj','int','loader','transporter','aircraft']
    tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
    exclude_keys = list(flatten([tempr,exclude_keys]))
    ints = {}
    for fact in interpretation:
        if fact.op not in exclude_keys:
            intv = fact.args[-1]
            int1 = intv.args[0].op
            int2 = intv.args[1].op
            ints.update({int1:1})
            ints.update({int2:1})
    return [min(ints.keys()), max(ints.keys())]   

def get_video_wise_ped_data(bg_KB, vid_intv, temp_rels=False):
    """This is the cookie cutter used to get blanket for whole video from FOLKB of several videos.
    We use the interval of the video as deictic interval and get everything within it"""
 
    blanket = {}
    bg_ints = unique(bg_KB.clauses['int'])
    deictic_ints  = [vid_intv]
    blanket['int'] = []
    
    for ex in deictic_ints:
        # Assuming 'int' is the last argument
        [X1, Y1] = ex 
        # Get all interval related to the diectic intervals
        for bg_int in bg_ints:
            if bg_int not in blanket['int']:
                [X2, Y2] = bg_int.args
                [X2, Y2] = [X2.op, Y2.op]
                # This if condition to ignore interval of length zero!
                if X2 > X1 and Y2 < Y1:    # during
                    blanket['int'].append(bg_int)
                elif X1 > X2 and Y1 < Y2:    # during
                    blanket['int'].append(bg_int)    
                elif X1 == X2 and Y2 < Y1:   # starts
                    blanket['int'].append(bg_int)
                elif X2 > X1 and Y1 == Y2:   # finishes
                    blanket['int'].append(bg_int)
                    
        # Now get all the spatial relations that have these selected intervals   
        exclude_keys = ['zone','obj','int']
        tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
        exclude_keys = list(flatten([tempr,exclude_keys]))
        valid_ints = {}
        for key in bg_KB.clauses.keys():
            if key not in exclude_keys:
                for e in bg_KB.clauses[key]:
                    if e.args[-1] in blanket['int']:                            
                        try:
                            blanket[key].append(e)
                        except KeyError:
                            blanket[key] = [e]
                        valid_ints[e.args[-1]] = 1
        # Now remove all ints that are not present in spatial relations
        # This code is because some bug in matlab code. Spurious ints are inserted in
        # the .pl file.
        duplicate_ints = blanket['int'][:]  
        for intv in duplicate_ints:
            if intv not in valid_ints:
                blanket['int'].remove(intv)        

        keys = set(['dint', 'obj', 'loader', 'aircraft', 'transporter', 'ground_power_unit', \
                    'conveyor_belt', 'mobile_stair', 'person'])        
        for key in keys:
            try:
                blanket[key] = bg_KB.clauses[key][:]
            except KeyError:
                pass
        blanket['start_end'] = vid_intv    
    return blanket

def get_video_wise_ped_data_str_int(bg_KB, vid_intv, temp_rels=False):
    """This is the cookie cutter used to get blanket for whole video from FOLKB of several videos.
    We use the interval of the video as deictic interval and get everything within it"""
 
    blanket = {}
    bg_ints = unique(bg_KB.clauses['int'])
    deictic_ints  = [vid_intv]
    blanket['str_int'] = []
    blanket['int'] = []
        
    for ex in deictic_ints:
        # Assuming 'int' is the last argument
        [X1, Y1] = ex         
        # Get all interval related to the diectic intervals
        
        for bg_int in bg_ints:
            if bg_int not in blanket['int']:
                [X2, Y2] = bg_int.args
                [X2, Y2] = [X2.op, Y2.op]
                str_intv = Expr('int', [''.join(['t', str(X2)]), ''.join(['t',str(Y2)])])
                blanket['str_int'].append(str_intv)
                # This if condition to ignore interval of length zero!
                if X2 > X1 and Y2 < Y1:      # during
                    blanket['int'].append(bg_int)
                elif X1 > X2 and Y1 < Y2:    # during
                    blanket['int'].append(bg_int)    
                elif X1 == X2 and Y2 < Y1:   # starts
                    blanket['int'].append(bg_int)
                elif X1 == X2 and Y2 > Y1:   # starts
                    blanket['int'].append(bg_int)
                elif X2 > X1 and Y1 == Y2:   # finishes
                    blanket['int'].append(bg_int)
                elif X2 < X1 and Y1 == Y2:   # finishes
                    blanket['int'].append(bg_int)
                elif X1 == X2 and Y1 == Y2:  # equals
                    blanket['int'].append(bg_int)
                        
        # Now get all the spatial relations that have these selected intervals   
        exclude_keys = ['zone','obj','int','str_int']
        tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
        exclude_keys = list(flatten([tempr,exclude_keys]))
        valid_ints = {}
        for key in bg_KB.clauses.keys():
            if key not in exclude_keys:
                for e in bg_KB.clauses[key]:
                    intv = e.args[-1]
                    if intv in blanket['int']:                          
                        [X1, Y1] = intv.args
                        [X1, Y1] = [X1.op, Y1.op]
                        # Get the string version of the interval
                        str_intv = Expr('int', [''.join(['t', str(X1)]), ''.join(['t',str(Y1)])])
                        spr = Expr(e.op, e.args[:-1] + [(str_intv)])
                        try:
                            blanket[key].append(spr)
                        except KeyError:
                            blanket[key] = [spr]
                        valid_ints[intv] = 1
        # Now remove all ints that are not present in spatial relations
        # This code is because some bug in matlab code. Spurious ints are inserted in
        # the .pl file.
        duplicate_ints = blanket['int'][:]  
        for intv in duplicate_ints:
            if intv not in valid_ints:
                blanket['int'].remove(intv)        

        keys = set(['dint', 'obj', 'loader', 'aircraft', 'transporter', 'ground_power_unit', \
                    'conveyor_belt', 'mobile_stair', 'person'])        
        for key in keys:
            try:
                blanket[key] = bg_KB.clauses[key][:]
            except KeyError:
                pass
            except TypeError:
                log.debug('Found dict for this key instead of list. Converting to list: ' + repr(key))
                bg_KB.clauses[key] = bg_KB.clauses[key].keys()
                blanket[key] = bg_KB.clauses[key][:]
                pass
        blanket['start_end'] = vid_intv    
    return blanket       

def get_video_wise_data(bg_KB, vid_intv, temp_rels=False):
    """This is the cookie cutter used to get blanket for whole video from FOLKB of several videos.
    We use the interval of the video as deictic interval and get everything within it"""
 
    blankets = {}
    bg_ints = unique(bg_KB.clauses['int'])
    deictic_ints  = [vid_intv]
    
    for ex in deictic_ints:
        # Assuming 'int' is the last argument
        [X1, Y1] = ex 
        
        blankets['int'] = []
        # Get all interval related to the diectic intervals

        for bg_int in bg_ints:
            [X2, Y2] = bg_int.args
            [X2, Y2] = [X2.op, Y2.op]
            # This if condition to ignore interval of length zero!
            if X2 != Y2:
                if X2 > X1 and Y2 < Y1:    # during
                    blankets['int'].append(bg_int)
                elif X1 > X2 and Y1 < Y2:    # during
                    blankets['int'].append(bg_int)    
                elif X1 == X2 and Y2 < Y1:   # starts
                    blankets['int'].append(bg_int)
                elif X2 > X1 and Y1 == Y2:   # finishes
                    blankets['int'].append(bg_int)
                    
        # Now get all the spatial relations that have these selected intervals   
        exclude_keys = ['zone','obj','int']
        tempr = ['before', 'meets', 'during', 'finishes', 'starts', 'equals', 'overlaps']
        exclude_keys = list(flatten([tempr,exclude_keys]))
        valid_ints = {}
        for key in bg_KB.clauses.keys():
            if key not in exclude_keys:
                for e in bg_KB.clauses[key]:
                    if e.args[-1] in blankets['int']:                            
                        try:
                            blankets[key].append(e)
                        except KeyError:
                            blankets[key] = [e]
                        valid_ints[e.args[-1]] = 1
        # Now remove all ints that are not present in spatial relations
        # This code is because some bug in matlab code. Spurious ints are inserted in
        # the .pl file.
        duplicate_ints = blankets['int'][:]  
        for intv in duplicate_ints:
            if intv not in valid_ints:
                blankets['int'].remove(intv)        

        keys = set(['dint', 'obj', 'loader', 'aircraft', 'transporter', 'ground_power_unit', \
                    'conveyor_belt', 'mobile_stair', 'person'])        
        for key in keys:
            try:
                blankets[key] = bg_KB.clauses[key][:]
            except KeyError:
                pass
    return blankets       
