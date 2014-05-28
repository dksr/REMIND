#############################################################################
#
#   Author   : Krishna Sandeep Reddy Dubba
#   Email    : scksrd@leeds.ac.uk
#   Institute: University of Leeds, UK
#
#############################################################################

"""Main file for ILP implementation
"""
import copy
import cPickle as pickle
import gc
import logging
import os
import platform
import random
import sys
import time
import weakref

from pyswip import Prolog

import base.utils.psutil                 as psutil
from base.base_constants                 import RBB, GBB, YBB, BBB, CBB, RBT, CBT, YBT, MBT, GBT, \
                                                GT, YT, MT, RT, CT, RESET
from base.utils.base_utils               import *
from base.utils.math_utils.xpermutations import xuniqueCombinations
from base.utils.odict                    import OrderedDict
from base.utils.search                   import Problem
from base.utils.Timer                    import Timer    
from learn.ilp.logic                      import *  
from learn.ilp.hyp                        import *
import learn.ilp.hyp_prune as config

# While displaying the result if the output is written to a file, 
# then display the 'tail' of the growing output file in the terminal.
# '%> tail -25 -f outfile.txt

# In score: Need to get h from static analysis of bottom-clause

# Use MapReduce:
# in generating successor i.e. map(some function, candidate)
    
log = logging.getLogger("lam.base.ilp.ilp_zone")

class ILP(Problem):
    def __init__(self, constants, color_map_file, event_name, modeh, modeb, train_pos_ex, pos_blankets, train_neg_vid_data, prolog, use_prolog=1, read_pic=False):

        # pos and neg examples are lists in a dictionary with only one key 
        # From config file name get other file names
        self.use_prolog  = use_prolog
        self.cmap_file  = open(color_map_file, 'w')
        self.event_name  = event_name
        
        #config = __import__(self.config_file)
     
        # parameters:
        # These and prune and integrity_check functions, we get by importing
        # the config file
        self.VAR_DEPTH, self.MAX_TERMS, self.SP_MAX_TERMS, self.NUM_REFINE_OPS, \
            self.MAX_BC_LENGTH, self.MIN_SCORE_TO_EXPAND_HYP, self.EG_TO_TRY = constants
        self.search_nodes    = config.search_nodes 
        self_max_proof_depth = config.max_proof_depth
        self_max_res_depth   = config.max_res_depth
        self.modeh           = modeh
        self.modeb           = modeb
        self.hyp_kids        = {}
        self.hyp_names       = {}
        self.hyps            = {}
        self.hyp_count       = 0
        self.timer           = Timer()
        self.spatial_mode    = True
        self.pos_ex_intv     = []
        self.pos_weightage   = 45
        self.neg_weightage   = 5
        self.pos_eval_time   = 0
        self.neg_eval_time   = 0
        
        self.bg_KB    = FolKB()
        self.pos_ex   = train_pos_ex
        self.blankets = pos_blankets
        
        # For Minds eye dataset        
        #for ins in train_pos_vid_data:
            #self.blankets.append(ins)
         
        # self.neg_blankets is just list of prolog file names
        self.neg_blankets = []
        for vid_data in train_neg_vid_data:
            for ins in vid_data:
                self.neg_blankets.append(ins)
        
        if self.use_prolog:
            self.prolog = prolog
            
        # Prune and integrity functions are from the config file. Write prune in 
        # config file similar to the refine function in this class.
        self.prunable        = config.prune
        self.integrity_check = config.integrity_check
         
        self.score      = []
        self.min_score  = [-100000, [], []]
        self.var_count  = 0
        self.count      = 0
        self.refine_ops = []
        
        
    def generate_initial_clause(self, eg_to_try_index=None):
        if eg_to_try_index != None:
            self.EG_TO_TRY = eg_to_try_index
        # Get first positive example
        if self.bottom_clause is not None:
            self.initial = [Clause(self.bottom_clause.head, [])]
            return (self.EG_TO_TRY, True)
        else:
            # blanket index is provided by ilp class. If this example does not
            # give non empty body, then next one is tried
            for example in self.pos_ex.clauses[self.modeh[0].predicate]:
                if self.EG_TO_TRY >= len(self.blankets):
                    break
                self.full_bottom_clause = self.get_bottom_clause(example, self.EG_TO_TRY)
                if len(self.full_bottom_clause.body) is not 0 and len(self.full_bottom_clause.body) < self.MAX_BC_LENGTH:
                    # store temporal and non-temporal terms of bottom clause
                    self.temporal_bc = []
                    self.spatial_bc  = []
                    for term in self.full_bottom_clause.body:
                        if term.op in temp_rel:
                            self.temporal_bc.append(term)
                        else:
                            self.spatial_bc.append(term)
                    self.bottom_clause = Clause(self.full_bottom_clause.head, self.spatial_bc, 0)        
                    break
                self.EG_TO_TRY += 1
            # Initial clause is only head from bottom_clause, no body
            if self.bottom_clause is not None:
                self.initial = [Clause(self.bottom_clause.head, [], 0)]
                return (self.EG_TO_TRY, True)
            else:     
                log.warn(RBB + 'Could not find a BOTTOM CLAUSE :-(' + RESET)
        return (self.EG_TO_TRY, False)
    
        
    def get_bottom_clause(self, example, blanket_index):
        def raise_stop_iter_excp():
            raise StopIteration
        # Always choose the first blanket. Relevant blankets are removed after each iteration
        # in the multiple hypothesis learning
        # Blanket is list of prolog_module name and blanket, so use index 1 to get blanket
        self.bg_KB.clauses = self.blankets[blanket_index][1]
        prolog_mod         = self.blankets[blanket_index][0]
        inTerms = {}
        ded_theta = deduce(example)
        # get head of bottom clause
        bot_cl_head = subst(ded_theta, example)
        bot_cl_body = OrderedDict()
        bot_cl_body_dup = []
        # unify or fol_bc_ask in pos example kb?
        theta_head = unify(bot_cl_head, example, {})
       
        
        # inTerms is dict. Key is the type of the variables like Zone, Vehicle etc.
        # Each key has a tuple as value which has two lists.
        # One for variables and one for its corresponding values. Variable list is useful
        # for constructing the term to add to the bottom clause body.
        
        # Assuming that keys() and values() methods for dict give results in the same order.
        
        ind = 0
        var_ind = 0
        val_ind = 1
        
        for hmode in self.modeh:
            for (mode, m_type) in hmode.modes:
                if mode == '+':
                    var = bot_cl_head.args[ind]
                    if len(var.args) is 0:
                        val = theta_head[var]
                    else:
                        val = subst(theta_head, var)
                    if m_type not in inTerms:
                        inTerms[m_type] = ([], [])
                    if val not in inTerms[m_type][val_ind]:
                        inTerms[m_type][val_ind].append(val)
                        inTerms[m_type][var_ind].append(var)
                ind += 1        
                
        #for bmode in self.modeb:
            # Initialize to empty list. Otherwise learning multiple hyp 
            # we get here more than once and the if case in line 193 will
            # fail if not initialized to empty list
            #bmode.subst = []
    
        for i in xrange(0, self.VAR_DEPTH):
            for bmode in self.modeb:
                sub_count = 0
                bm_args = []
                bmode.subst = []               
                arg_count = 0
                # Get all the substitutions possible for a body mode declaration
                for (mode, m_type) in bmode.modes:
                    if mode == '+' and m_type in inTerms:
                        bmode.subst.append(inTerms[m_type][val_ind])
                    elif mode == '-':
                        if len(self.bg_KB.clauses[m_type]) is 0:
                            break
                        # Take a sample from the args of a sample of this relation.
                        # This will ensure that the args are consistant with relation
                        # Ex some relations' int arg has same time points while some have
                        # different time points
                        if bmode.predicate in sp_rel:
                            try:
                                bmode_rel_sample = self.bg_KB.clauses[bmode.predicate][0]
                                sample_ex = bmode_rel_sample.args[arg_count]
                            except KeyError:
                                sample_ex = self.bg_KB.clauses[m_type][random.randint(0, len(self.bg_KB.clauses[m_type])-1)]
                        else:
                            sample_ex = self.bg_KB.clauses[m_type][random.randint(0, len(self.bg_KB.clauses[m_type])-1)]
                        
                        if len(sample_ex.args) > 1:
                            variablised_sample = subst(deduce(sample_ex), sample_ex)
                            bmode.subst.append([variablised_sample])
                        else:
                            if deduce.counter < 24:
                                bmode.subst.append([built_in_vars[deduce.counter]])
                            else:
                                bmode.subst.append([Expr('V_%d' % deduce.counter)])
                            deduce.counter += 1
                    elif mode == '$':
                        # Assuming m_type predicates have only one argument
                        m_type_constants = [i.args[0] for i in self.bg_KB.clauses[m_type]]
                        bmode.subst.append(m_type_constants)
                    else: 
                        # This might be the case 'mode == '+' and m_type NOT in inTerms'
                        break
                    arg_count += 1
                # Length not equal because inTerms does not yet have terms of some types.
                # So skip this mode declaration. Might consider in next iteration.
                if len(bmode.subst) != len(bmode.modes):
                    continue
                    
                # Repeat this block for num of subst of +vars with terms from inTerms
                for subst_temp in car_product(bmode.subst):
                    # What if bmode_subst has same lists. Ex: incase of temporal rels
                    # This results in bm_args of type (a,a). In temporal rels this adds
                    # addditional starts relation for (a,a). Though I am taking care of this 
                    # think about it.
                    bm_args = list(subst_temp)
                    #bm_theta = fol_bc_ask(self.bg_KB, [Expr(bmode.predicate, bm_args)])
                    # Using prolog query instead of pythons fol_bc_ask
                    query = prolog_mod + ':(' + str(Expr(bmode.predicate, bm_args)) + ')'
                    log.debug('query: ' + query)
                    bm_theta = self.prolog.query(query)
                            
                    # Repeat recall times this loop.
                    loop_count = bmode.recall
                    j = 0
                    while j < loop_count:
                        try:
                            wrong_type = False
                            try:
                                sub_res = bm_theta.next()
                            except Exception:                                
                                raise_stop_iter_excp()
                            # Need to convert strings to expressions as prolog gives result's keys and values as strings
                            try:
                                sub = dict([(expr(k[0]), expr(k[1])) for k in sub_res.items()])
                            except AttributeError:
                                # If the query has no instances, then prolog returns a list of single string ['[]']
                                sub = {}
                                log.debug(query + ' has no instances in prolog database for bottom_clause')
                            # Check query result types
                            ind = 0
                            for (mode, m_type) in bmode.modes:
                                val = subst(sub, bm_args[ind])
                                ind += 1
                                # val.op is series of type heirarchy like obj::veh::gpu. So we check only if
                                # obj is in it. We may use full heirarchy in mode declarations but this increases
                                # the number of mode declarations
                                if mode == '-' and m_type not in val.op and \
                                    (Expr(m_type, val) not in self.bg_KB.clauses[m_type] \
                                     or val not in self.bg_KB.clauses[m_type]):
                                    # Last condition is for zones, they don't have any op value, but
                                    # so their op won't match with 'zone' but are defined in bg_KB with
                                    # key 'zone'.
                                    wrong_type = True
                                    raise StopIteration
                        except StopIteration:
                            if wrong_type:
                                # Try next solution as this solution got a wrong type
                                # Can't avoid as not possible to check type of solution 
                                # automatically in prolog query. May be should fix in fol_bc_ask.
                                continue
                            else:
                                break
                        ind = 0
                        j += 1
                        for (mode, m_type) in bmode.modes:
                            if mode == '-':
                                val = subst(sub, bm_args[ind])
                                if m_type not in inTerms:
                                    inTerms[m_type] = ([], [])
                                if val not in inTerms[m_type][val_ind]:
                                    inTerms[m_type][val_ind].append(val)
                                    # Get unique vars for this value, update the would-be term
                                    # args and add these vars as corresponding vars for values.
                                    bm_args[ind] = variablizer(val)
                                    inTerms[m_type][var_ind].append(bm_args[ind])
                                else:
                                    # If there, get the corresponding variable and replace the
                                    # one in bm_args with it. This will maintain same variable 
                                    # for same constant through out the clause.
                                    index = inTerms[m_type][val_ind].index(val)
                                    bm_args[ind] = inTerms[m_type][var_ind][index]
                            elif mode == '+':
                                # get value(constant) index from inTerms
                                val_index = inTerms[m_type][val_ind].index(bm_args[ind])
                                # Use this to get the corresponding variable from inTerms
                                bm_args[ind] = inTerms[m_type][var_ind][val_index]        
                            ind += 1        
                        # Add the new term got with new bm_args to bottom clause body                        
                        to_add = Expr(bmode.predicate, bm_args)
                        if to_add not in bot_cl_body:
                            bot_cl_body.update(OrderedDict(((to_add, 1),)))
                            bot_cl_body_dup.append(to_add)
                        bm_args = list(subst_temp)
                        
        self.inTerms = inTerms
        removed_starts = []
        for term in bot_cl_body_dup:
            if term.op == 'starts':
                if term.args[0] == term.args[1]:
                    bot_cl_body.pop(term)
                else:
                    for term2 in bot_cl_body_dup:
                        if term2.op == 'starts' and term != term2 and set(term.args).issubset(set(term2.args)):
                            if term not in removed_starts:
                                removed_starts.append(term2)
                                bot_cl_body.pop(term2)

        removed_finishes = []                            
        for term in bot_cl_body_dup:
            if term.op == 'finishes':
                if term.args[0] == term.args[1]:
                    bot_cl_body.pop(term)
                else:
                    for term2 in bot_cl_body_dup:
                        if term2.op == 'finishes' and term != term2 and set(term.args).issubset(set(term2.args)):
                            if term not in removed_finishes:
                                removed_finishes.append(term2)
                                bot_cl_body.pop(term2)      
                            
        bc = Clause(bot_cl_head, bot_cl_body.keys(), 0)
        log.info('')
        log.info('Prolog Module: ' + prolog_mod)
        log.info('')
        log.debug('')
        log.debug('Blanket: ' + repr(self.bg_KB.clauses))
        log.debug('')
        if len(bc.body) < 200:
            log.info(CBB + 'BOTTOM CLAUSE: ' + repr(len(bc.body)) + RESET)
            log.info(bc)        
        else:
            log.info(CBB + 'BOTTOM CLAUSE too big to log with length: ' + repr(len(bc.body)) + RESET)        
        return bc
  
    def successor(self, hyp):
        # Each state is a set of hypotheses
        new_state = []
        # Store the append function locally to increase speed
        append = new_state.append
        #for hyp in state:
        # Select randomly one of the refinement operators
        for i in xrange(0, self.NUM_REFINE_OPS):
            new_hyp = self.refine(hyp, i)
            if len(new_hyp) == 0:
                log.debug('No refined hyps')
            for item in new_hyp:
                append((i, item))
        del new_hyp    
        return new_state
     
    def goal_test(self, opened, best_hyp):
        """Need to find the best way to decide the goal. See Bratko's code and progol"""
        # best_hyp is the candidate state. 
        if best_hyp.temporal_expandable:
            # This hyp is still expandable, so try it
            return False 
        
        valid_hyp = 0
        count = 0
        for hyp in opened.A:
            if not hyp[1].state.prunable:
                valid_hyp += 1
                if best_hyp.score[0] > hyp[1].state.score[0]:
                    count += 1        
        if count == valid_hyp and count is not 0:
            # return success. best_hyp is better than all hyps in opened
            return best_hyp.score
        return False
     
    def test_coverage(self,  hyp):
        # Return the uncovered postive examples
        return self.pos_ex
     
    def path_cost(self, c, state1, action, state2):
        # Call the super class function. It just increments 'c'
        # as path in this case does not matter
        # Problem.path_cost(c, state1, action, state2), something wrong if I use this line
        return c + 1
     
    def calc_score(self, hyp, test=False):
        """Calculates the score of the Clause. Right now it is just based on
        the examples covered and clause attributes. Fix the scoring function."""
        # Also take size of the hypothesis into consideration.
        if not hyp.pruned:
            self.prunable(hyp)
        if hyp.prunable is True:
            return hyp.score
        if hyp.scored is True:
            return hyp.score
        
        log.debug('Scoring:' + repr(hyp))
        self.hyp_count += 1
        if not test:
            t0 = time.clock()
            pos_cover = hyp.pyswip_covers(self.prolog, self.blankets, self.use_prolog, test, neg=0)
            self.pos_eval_time += (time.clock() - t0)
            
        #t0 = time.clock()
        #pos_cover = hyp.pyswip_covers(self.prolog, self.blankets, self.use_prolog, test, neg=0)
        #self.pos_eval_time += (time.clock() - t0)    
    
        t0 = time.clock()        
        neg_cover = hyp.pyswip_covers(self.prolog, self.neg_blankets, self.use_prolog, test, neg=1)
        self.neg_eval_time += (time.clock() - t0)        
        
        num_vars = len(hyp.get_all_vars())
        num_predicates = len(hyp.get_all_predicates())
        # Should I have num_vars here or should I remove?
        # score = p - n - c - h. Last term is to be found by static analysis of 
        # bottom clause (page 16).  See reduce.c of Progol.
        
        neg_unique_cover = {}
        pos_cov_intvs = []
        if test:
            log.info('Test scoring:')
            pos_cover = []
            count = 0
            for ins in neg_cover:
                #ins_ints = [i for i in ins.values() if type(i) is int]
                ins_ints = [eval(i[1:]) for i in ins.values() if type(i) is str and i.startswith('t') and i[1] in '1234567890']
                intv = (min(ins_ints), max(ins_ints))
                if intv not in neg_unique_cover:
                    log.debug('recognized intv: ' + repr(intv))
                    if len(self.pos_ex_intv) != 0:
                        hit = False
                        # This 'if' is satisfied only while testing
                        for pos_intv in self.pos_ex_intv:
                            log.debug('ground truth intv: ' + repr(pos_intv))
                            [X1, Y1] = [intv[0], intv[1]]
                            [X2, Y2] = [pos_intv[0], pos_intv[1]]
                            if Y1 < X2 or X1 > Y2:
                                # retrieved interval does not coincide with the positive interval, so this
                                # is clearly false positive                                
                                continue                                
                            else:
                                # if not test, we will have ins in a list, so to be consistant, put [ins]
                                log.debug('Adding to pos cover')
                                pos_cover.append({(count,count):[ins]})
                                hit = True
                                break
                        if not hit:
                            log.debug('Adding to neg cover')
                            neg_unique_cover.update({intv:1})        
                    else:    
                        neg_unique_cover.update({intv:1})
        else:
            neg_unique_cover = neg_cover

        # Get number of postive hits. This should be less for a good hyp
        # pos_cover is of the form [{(vid, ex):[res1, res2]}, {(vid, ex):[res1, res2, res3]}, ...]
        pos_hits = sum([len(i.values()[0]) for i in pos_cover])
                
        # Get overlap ratio of intervals of positive hits and groundtruth
        # This is ratio of itersection and union of two intervals
        duration_ratio = 0
        for item in pos_cover:
            # There is only one value in the dict, so take the first one
            for res_ins in item.values()[0]:
                #ins_ints = [i for i in ins.values() if type(i) is int]
                ins_ints = [eval(i[1:]) for i in res_ins.values() if type(i) is str and i.startswith('t') and i[1] in '1234567890']
                intv = (min(ins_ints), max(ins_ints))
                for pos_intv in self.pos_ex_intv:
                    [X1, Y1] = [intv[0], intv[1]]
                    [X2, Y2] = [pos_intv[0], pos_intv[1]]
                    intersection_start = max(X1, X2)
                    intersection_end   = min(Y1, Y2)
                    union_start        = min(X1, X2)
                    union_end          = max(Y1, Y2)
                    if (union_end - union_start) != 0:
                        duration_ratio += float(intersection_end - intersection_start)/(union_end - union_start)
        if duration_ratio != 0 and pos_hits != 0:                
            duration_ratio = duration_ratio/pos_hits
        
        if len(pos_cover) >= 1:
            hyp.score = [self.pos_weightage*len(pos_cover) \
                         - self.neg_weightage*len(neg_unique_cover) \
                         - 2 * pos_hits \
                         - 10 * num_vars \
                         + 5 * duration_ratio]
            #hyp.score = [self.pos_weightage*len(pos_cover) - len(neg_unique_cover) + 2 * num_predicates]  # - num_vars  
                      # - 3*(len(self.bottom_clause.get_all_predicates()) - num_predicates)]                         
            # Also add the indices of examples covered.        
        else:
            hyp.score = [-10000]
            hyp.expandable = False
        if test:
            #pos_cover_res = [i.values()[0] for i in pos_cover]    
            #hyp.score.append(pos_cover_res)               # subst instances for pos examples covered
            hyp.score.append(pos_cover)
            hyp.score.append(neg_unique_cover)            # subst instances for neg examples covered
        else:
            pos_cover_ind = [i.keys()[0] for i in pos_cover]
            hyp.score.append(pos_cover_ind)               # How many pos examples are covered        
            hyp.score.append(len(neg_unique_cover))       # How many neg examples are covered            
        hyp.score.append(len(self.blankets))              # Total positive examples
        if len(pos_cover) > 5 and hyp.score[0] > 0:
            log.info(YBT + 'HYP_COUNT: ' + repr(self.hyp_count) + RESET)
            log.info(repr(hyp.score) + ': ' + repr(hyp.body))
            #apm = psutil.avail_phymem()/(1024*1024)
            #log.info(YBT + 'AVAIL_PHY_MEM: ' + BBB + repr(apm) + RESET)
        elif len(pos_cover) is 1:
            log.debug(repr(hyp.score) + ': ' + repr(hyp.body))
        log.info(repr(hyp.score) + ': ' + repr(hyp.body))    
            
        hyp.scored = True
        log.debug(hyp.score)
        #del pos_cover
        #del neg_cover
        #del neg_unique_cover
        return hyp.score

    def f(self, n):
        """Used by graph_search to order nodes in its list.
        Return the first element of score"""
        return self.calc_score(n.state)[0]
    
    def refine(self, hyp, selection):
        """ Refines and returns a Clause.
        Refining types:
        Substitute a constant in place of a variable
        Equate two variables
        Swap two variables
        Add a literal from bottom_clause to the hyp body
        Generalize the type of a variable
        All these make the returned Clause more specific
        Uses dynamic function selection.
        """        
        def refine_by_eq_vars(hyp):
            """ Refines and returns a Clause.
            Equates two variables in body and head.
            """
            all_vars  = list(hyp.get_all_vars())
            if len(all_vars) < 2:
                return None
            # Select two variables randomly and refine accordingly    
            samples = random.sample(all_vars,2)
            theta = {samples[0]:samples[1]}
            new_head = subst(theta, hyp.head)
            new_body = []
            for term in hyp.body:
                new_body.append(subst(theta, term))
            if self.integrity_check(new_body) is True:
                return None                    
            return {Clause(new_head, new_body):1}

        def refine_by_eq_vars_in_body(hyp):
            """ Refines and returns a Clause.
            Equates two variables only in body not in head.
            """
            all_vars = list(hyp.get_all_vars())
            if len(all_vars) < 2:
                return {}
            samples = random.sample(all_vars,2)
            theta = {samples[0]:samples[1]}
            # Not new head but the same old head
            new_head = copy.copy(hyp.head)
            new_body = []
            for term in hyp.body:
                new_body.append(subst(theta, term))
            if self.integrity_check(new_body) is True:
                return {}
            return {Clause(new_head, new_body):1}
            
        def refine_by_expansion(hyp):
            """ Refines and returns a Clause.
            Adds a background literal to the clause
            """
            if not hyp.pruned:
                self.prunable(hyp)                
            # Checking MAX_TERMS parameter constraint
            if len(hyp.body) >= self.MAX_TERMS:
                return {}
            if self.spatial_mode and not hyp.spatial_expandable:
                # Now doing in two phases, so the second if condition doesn't hold
                # Can't increase the length, so return failure
                return {}
            elif not self.spatial_mode and len(hyp.body) >= self.MAX_TERMS:
                return {}
            elif hyp.spatial_predicate_count != 0 and hyp.scored \
                 and (not hyp.prunable) and len(hyp.score[1]) < self.MIN_SCORE_TO_EXPAND_HYP:
            #elif hyp.spatial_predicate_count != 0 and hyp.scored and (not hyp.prunable):
                return {}
            # Try as many times as there are terms before returning None
            new_clauses = {}
                                            
            for ind in xrange(hyp.bottom_clause_ind + 1, len(self.bottom_clause.body)):
                term = self.bottom_clause.body[ind]
                if term.op in sp_rel and hyp.spatial_predicate_count >= self.SP_MAX_TERMS:
                    continue
                new_body = hyp.body[:]
                new_body.append(term)
                # Check connectivity. This will reduce number of hypotheses tried.                    
                if check_connectivity(new_body):
                    # Here increase the hyp.bottom_clause_ind to self.bottom_clause.body.index(term)
                    temp_clause = Clause(hyp.head, new_body, self.hyp_count)                     
                    temp_clause.bottom_clause_ind = ind
                    temp_clause.spatial_expandable = hyp.spatial_expandable
                    temp_clause.spatial_predicate_count = hyp.spatial_predicate_count
                    new_clauses[temp_clause] = 1
                    
                    #self.cmap_file.write(repr(self.hyp_count) + '\t0\t1\t0\n')
                    #self.hyp_names[repr(self.hyp_count)] = repr(new_body)
                    #hyp.kids.append(self.hyp_count)  
                    #self.hyp_count += 1
            #if hyp.hyp_id in self.hyp_kids:
                #self.hyp_kids[hyp.hyp_id] = self.hyp_kids[hyp.hyp_id].union(hyp.kids)
            #else:    
                #self.hyp_kids[hyp.hyp_id] = set(hyp.kids)

            return new_clauses 
            
        def refine_by_type(hyp):
            def generalize_type(arg):
                new_arg = copy.copy(arg)
                # Here we don't check whether it is possible to generalize
                # We blindly try to generalize. So check before calling this function
                new_arg.op = '::'.join(new_arg.op.split('::')[:-1])
                return new_arg    
            
            neg_score_ind = 2
            if hyp.score[neg_score_ind] > 15 or len(hyp.body) < 3:
                return {}
     
            new_clauses = {}     
            args = hyp.get_all_args()
            
            for arg in args:
                # arg.op.split('::')[:-1] means split the op based on '::' and leave the lost element
                if len(arg.op.split('::')[:-1]) > 0:
                    new_arg  = generalize_type(arg)
                    new_body = hyp.body[:]
                    new_body = subst({arg:new_arg}, new_body)
                    new_hyp  = Clause(hyp.head, new_body, self.hyp_count) 
                    if hash(new_hyp) in self.hyps:
                        continue
                    #self.cmap_file.write(repr(self.hyp_count) + '\t1\t0\t0\n')
                    #self.hyp_names[repr(self.hyp_count)] = repr(new_body)
                    #hyp.kids.append(self.hyp_count)
                    new_hyp.specific_typed = True
                    new_hyp.bottom_clause_ind = hyp.bottom_clause_ind
                    new_hyp.parent_score = hyp.score[0]
                    new_hyp.spatial_expandable = hyp.spatial_expandable                 
                    new_clauses[new_hyp] = 1
                    self.hyp_count += 1
            #if hyp.hyp_id in self.hyp_kids:
                #self.hyp_kids[hyp.hyp_id] = self.hyp_kids[hyp.hyp_id].union(hyp.kids)
            #else:    
                #self.hyp_kids[hyp.hyp_id] = set(hyp.kids)

            return new_clauses
        
        # For the time being, we only use this refinement operator
        self.refine_ops = [refine_by_expansion, refine_by_type]
        #self.refine_ops = [refine_by_expansion]
                                                   
        if selection > len(self.refine_ops):
            raise Exception, "Trying to execute non existant hypothesis refinement operator"
        # Using dynamic function capability get the refinement operator from
        # the list and run it
 
        log.debug('Refining: ' + repr(hyp.body))
        
        refine_func = self.refine_ops[selection]

        #wingdbstub.debugger.StartDebug()
        #time.sleep(2)
        #wingdbstub.debugger.Break()
        
        ref_hyp = refine_func(hyp)
        old_hyp = ref_hyp.keys()[:]
        prunable_hyp = False
        # Make sure we return atlest one hyp that is not prunable
        while True:
            if len(old_hyp) is 0:
                break
            for hp in old_hyp:
                if self.prunable(hp) is False:
                    # Ok, atleast one hyp is not prunable, break here
                    prunable_hyp = True
            if prunable_hyp:
                break
            # All the refined hyp found are prunable, so useless. Find some more refined hyp
            # from these where atleast one is not prunable or repeat this process.
            new_ref_hyp = {}                       
            for hp in old_hyp:
                # We are adding refined hyp of hyp, so no need of this in the future.
                del ref_hyp[hp]
                new_hyps = refine_func(hp)
                new_hyps_dup = new_hyps.keys()[:]    
                
                #for key in new_hyps_dup:
                    #try: 
                        ## Only body of Clause is used for hashing. Not sure why only key as key 
                        ## does not work properly :-(
                        #if self.hyps[hash(key)] == 1:
                            #del new_hyps[key] 
                            #continue
                        #else:
                            #self.hyps[hash(key)] = 1
                    #except KeyError:
                        #self.hyps[hash(key)] = 1
                        
                new_ref_hyp.update(new_hyps)
            ref_hyp.update(new_ref_hyp)
            old_hyp = new_ref_hyp.keys()[:]    
            
        del old_hyp
        del hyp
        return ref_hyp
    
    def get_my_hyp(self, hyp):
        """ Use this to catch a candidate clause, for testing only """
        myset = frozenset(['enter_zone','con','sur','overlaps','meets'])
        myvars = map(expr, 'ABCDIJOP')
        myvars = frozenset(myvars)
        all_preds = hyp.get_all_predicates()
        all_vars = hyp.get_all_vars_avail()
        if len(frozenset(all_preds).intersection(myset)) == 4 and (frozenset(all_vars) == myvars):
            return True
        return False

def check_connectivity_include_head(head, body):
    """For any term in body, it should have atleast one variable that occurs
    in the head or any term before it. If that is not the case reject the hypotheses."""
    all_vars = set(head.args[:])
    for term in body:
        args = set(term.args)
        if len(all_vars.intersection(args)) == 0:
            return False
        else:
            all_vars = all_vars.union(args)
    return True        


temp_rel = set([])
temp_rel.add('meets')
temp_rel.add('before')
temp_rel.add('starts')
temp_rel.add('during')   
temp_rel.add('finishes')
temp_rel.add('overlaps')

sp_rel = set([])
sp_rel.add('sur')
sp_rel.add('con')
sp_rel.add('rel_1')
sp_rel.add('vehicle_Stopped')
sp_rel.add('vehicle_Removing')
sp_rel.add('vehicle_Positioned')
sp_rel.add('vehicle_Leaves_Zone')
sp_rel.add('vehicle_Enters_Zone')
sp_rel.add('vehicle_Positioning')
sp_rel.add('vehicle_Inside_Zone')
sp_rel.add('vehicle_Stopped_Inside_Zone')

def check_connectivity(body):
    """For any term in body, it should have atleast one variable that occurs
    in any term in the body before it. If that is not the case reject the hypotheses."""
    if len(body) > 1:    
        all_vars = set([])
        for term in body:
            if term.op not in temp_rel:
                # If spatial predicate, atleast one object in it should have appeared before
                args = set([arg for arg in term.args if len(arg.args) == 0])

                if len(args) == 0:
                    # Something wrong. Does objects have a type predicate? Then do this:
                    for arg in term.args:
                        if arg.op != 'int':
                            args = args.union(arg.args)
                
                temp_args = set([arg for arg in term.args if len(arg.args) != 0])
                # Now check if any one non temporal arg is already there in the set of all args already seen
                if len(all_vars) is not 0 and len(all_vars.intersection(args)) == 0:
                    return False            
            else:
                # if term is temporal predicate. We check if all args have appeared previously
                args = set(term.args)
                temp_args = set([])    # we don't need temp_args here
                # Now check if all temporal args are already there in the set of all args already seen
                if not args.issubset(all_vars):
                    return False            
            if len(all_vars) is not 0 and len(all_vars.intersection(args)) == 0:
                return False
            else:
                all_vars = all_vars.union(args)
                all_vars = all_vars.union(temp_args)
                
    return True      

def check_temporal_connectivity(body):
    """THIS GIVES HELL NUMBER OF HYPS
    For any term in body except spatial term, it should have atleast one variable that occurs
    in any term in the body before it. For temporal terms all args should already appear in hyp
    If that is not the case reject the hypotheses."""
    if len(body) > 1:    
        all_vars = set([])
        for term in body:
            if term.op not in temp_rel:
                # If spatial predicate, collect args
                args = set([arg for arg in term.args if len(arg.args) == 0])
                temp_args = set([arg for arg in term.args if len(arg.args) != 0])
            else:
                # if term is temporal predicate. We check if all args have appeared previously
                args = set(term.args)
                temp_args = set([])    # we don't need temp_args here
                # Now check if all temporal args are already there in the set of all args already seen
                if len(all_vars) is not 0 and not args.issubset(all_vars):
                    return False            
            if term.op not in sp_rel and len(all_vars) is not 0 and len(all_vars.intersection(args)) == 0:
                return False
            else:
                all_vars = all_vars.union(args)
                all_vars = all_vars.union(temp_args)                
    return True      

if __name__ == '__main__':
    #from sample_kb import *        
    num_refine_ops = 1
    a = Expr('rel_1',['T',' J', Expr('int',['U', 'V'])])    
    b = Expr('loader',['T'])
    c = Expr('before',[Expr('int',['U', 'V']), Expr('int',['W', 'X'])])
    d = Expr('rel_1',['T',' J', Expr('int',['W', 'X'])])
    bod = [a,b,c]
    print check_connectivity(bod)
    bod = [a,d,b,c]
    print check_connectivity(bod)
    clusters = 4
    #config_f = 'ul_cof_all_cam2_clean_qtc_protos_' + repr(clusters) +'_type_with_events'
    config_f = 'la_cof_all_cam2_clean_qtc_protos_' + repr(clusters) +'_type'
    ilp = ILP(config_f, 0)
    #ilp = ILP('tz')
    # Need to call this in a loop until all positive examples are covered.
    # Then append all the solutions into a hypothesis. 
    solution_hyp = []
    inTerms = {}
    no_sol_count = 0
    sol = {}    
    print 'bottom clause doing'
    # Repeat until all positive examples are covered
    while len(ilp.pos_ex.clauses[ilp.modeh[0].predicate]) != 0:
        # A different initial clause is generated based on pos_ex remaining
        ilp.bottom_clause = None
        ilp.generate_initial_clause()
        try:
            sol['pos_ex']
        except KeyError:
            sol['pos_ex'] = ilp.pos_ex                        
        #print ilp.bottom_clause
        solution_clause = ilp_best_first_graph_search(ilp, ilp.f)
        solution_clause = solution_clause.state
        (score, pos_cov, neg_cov) = solution_clause.score
        if len(pos_cov) is not 0:
            solution_hyp.append(solution_clause)
            for key in ilp.inTerms.keys():
                try:
                    inTerms[key].append(ilp.inTerms[key])
                except KeyError:
                    inTerms[key] = [ilp.inTerms[key]]                                           
            remove_exp = []
            remove_blankets = []        
            # Collect all positive examples that are to be removed and then remove
            for i in pos_cov:
                remove_exp.append(ilp.pos_ex.clauses[ilp.modeh[0].predicate][i])
                remove_blankets.append(ilp.blankets[i])          
            for exp in remove_exp:       
                ilp.pos_ex.retract(exp)
            for blanket in remove_blankets:
                ilp.blankets.remove(blanket)
        else:
            no_sol_count += 1
            if no_sol_count > 5:
                break
    
    print '**********************************'    
    pp(solution_hyp)
    print ' $[', solution_hyp[0].score[1], ', ', len(solution_hyp[0].score[2]), ']'
    file_name = ilp.data_path + config_f + '_sol_new.p';
    
    sol['hyp'] = solution_hyp
    sol['inTerms'] = inTerms
    sol['neg_ex'] = ilp.neg_ex    
    pickle.dump(sol, open(file_name,'w'), 1);
    print 'over'
