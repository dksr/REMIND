#############################################################################
#
#   Author   : Krishna Sandeep Reddy Dubba
#   Email    : scksrd@leeds.ac.uk
#   Institute: University of Leeds, UK
#
#############################################################################

import logging
import os
import ConfigParser
from base.base_constants import *
from base.ilp.hyp_vigil import get_relation_predicates, sp_rel, temp_rel

try:
    ROOT_DIR = os.environ['COF_LEARN_ROOT']        
except KeyError:
    ROOT_DIR = '/home/csunix/scksrd/work/cof_learn/'    
cfg_prsr = ConfigParser.ConfigParser()
cfg_prsr.read(ROOT_DIR + '/config.cfg')       

MAX_TERMS    = eval(cfg_prsr.get('PARAMETERS', 'max_terms'))
SP_MAX_TERMS = eval(cfg_prsr.get('PARAMETERS', 'sp_max_terms'))
TEMP_REL_MANDATORY = eval(cfg_prsr.get('PARAMETERS', 'temporal_rel_mandatory'))
        
search_nodes    = 400
max_proof_depth = 50
max_res_depth   = 500

log = logging.getLogger("lam.prune")

def prune(hyp):
    # Returns True or False based on if the Hyp satisfies the prune statements
    if hyp is None:
        return True
    if hyp.prunable is True:
        return True
    if hyp.pruned is True:
        return hyp.prunable
    if len(hyp.body) < 3:
        # If length of hyp body is less than 3, i.e. trivial hyp with just two terms in body
        hyp.prunable = True
        hyp.pruned = True
        return True
    
    if len(hyp.body) == MAX_TERMS:
        # If length of hyp body is equal to max_terms allowed
        hyp.temporal_expandable = False
        hyp.spatial_expandable = False
        hyp.pruned = True

    spr_terms = get_relation_predicates(hyp, 'spatial')
    hyp.spatial_predicate_count = len(spr_terms)
    if hyp.spatial_predicate_count >= SP_MAX_TERMS:
        hyp.spatial_expandable = False
        hyp.pruned = True
    
    all_preds = hyp.get_all_predicates()    
    if TEMP_REL_MANDATORY and len(frozenset(all_preds).intersection(temp_rel)) == 0:
        # If hyp does not have a temporal predicate
        hyp.prunable = True
        hyp.pruned = True
        return True              
        
    # All the intervals in temporal relations are to be in spatial relations.    
    temp_terms = get_relation_predicates(hyp, 'temporal')

    if len(temp_terms) != 0 and len(spr_terms) > 1:

        temp_int_args = set([])
        spr_int_args  = set([])
        for term in temp_terms:
            # In temporal relations all args are intervals. So add all.
            temp_int_args = temp_int_args.union(term.args)
            
        for term in spr_terms:
            # In spatial relation only third arg is interval. So add only last arg.        
            spr_int_args = spr_int_args.union([term.args[-1]])
        # Don't add the interval from head as it is diectic interval    
        # spr_int_args = spr_int_args.union([hyp.head.args[-1]]) 
                    
        if not temp_int_args.issubset(spr_int_args):
            hyp.prunable = True
            hyp.pruned = True
            return True     

    # Reject hyp that has relations between objects    
    for j in hyp.body:
        if j.op not in temp_rel:
            if j.args[0].op == 'obj' and j.args[1].op == 'obj':
                hyp.pruned = True
                hyp.prunable = True
                return True                    
        
    all_args = hyp.get_all_args_avail()
    arg_type_map = {}
    for arg in all_args:     
        if len(arg.args) == 1:
            # Consider only objects.
            if arg.op not in arg_type_map:
                arg_type_map[arg.op] = {}          
            arg_type_map[arg.op][arg.args[0]] = 1
            
    for typ in arg_type_map:
        if typ == 'person' and len(arg_type_map[typ]) < 2:
            hyp.pruned = True
            hyp.prunable = True
            return True
        if typ == 'obj' and len(arg_type_map[typ]) < 2:
            hyp.pruned = True
            hyp.prunable = True
            return True    
            
    ## hyp.prunable is by default False    
    hyp.pruned = True
    return False

def integrity_check(hyp_body):
    # Returns True or False based on if the Hyp satisfies the prune statements
    return hyp_body


if __name__ == "__main__":
    print "Hello";
