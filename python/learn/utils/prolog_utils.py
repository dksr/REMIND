"""Some Prolog utilities to work with pyswip module"""

import logging
from base.base_constants   import RBB, GBB, YBB, BBB, CBB, BBT, RBT, CBT, YBT, MBT, GBT, \
                                  GT, YT, MT, RT, CT, RESET

log = logging.getLogger("lam.learn.utils.prolog_utils")

def assert_example_to_prolog(example_data, prolog, module, exclude_keys=[]):
    """Asserts the facts in the example data to Prolog"""
    
    module = module + ':'
    
    for key in example_data.keys():
        if key not in exclude_keys:
            for item in example_data[key]:
                prolog.assertz(module + repr(item))
    log.debug(module + ' example ' + GBT + 'asserted ' + RESET + 'to Prolog')
    
def retract_blanket_from_prolog(example_data, prolog, module):
    """Retracts the facts in the example data from Prolog"""
        
    from base.ilp.logic import non_recur_deduce, subst
    
    module = module + ':'
    for key in example_data:
        if len(example_data[key]) == 0:
            continue
        sample_fact = example_data[key][0]
        subst_dict = non_recur_deduce(sample_fact)
        generalized_fact = subst(subst_dict, sample_fact)
        q = 'retractall(' + module + repr(generalized_fact) + ')'
        prolog.query(q)
    log.info(module + ' example ' + RBT + 'retracted ' + RESET + 'from Prolog')
    