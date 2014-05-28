#############################################################################
#
#   Author   : Krishna Sandeep Reddy Dubba
#   Email    : scksrd@leeds.ac.uk
#   Institute: University of Leeds, UK
#
#############################################################################

"""Main class for hypothesis

"""
import copy
import logging
import os
import platform
import sys
import time
import random
import re

import base.utils.psutil as psutil
from base.utils.base_utils import *
from base.base_constants import *
from learn.ilp.logic import *

log = logging.getLogger("lam.base.ilp.hyp")

class Clause(Expr):
    """Class definition for hypothesis"""
    def __init__(self, head, body, hyp_id, types={}):
        # Sample input: hyp = Hyp(e,[[f,g],[g,f]]) where e,f,g are valid
        # expressions and definite clauses.
        self.head = head
        self.body = []
        # score is [score, pos_ex_covered, tot_neg_ex_covered, tot_pos_ex]
        self.score = [-100000, [], 0, 0]
        self.all_vars = []
        self.all_vars_avail = []
        self.prunable = False
        self.pruned = False
        self.scored = False
        self.expandable  = True
        self.goal_tested = False
        self.bottom_clause_ind = -1
        self.spatial_predicate_count = 0
        self.spatial_expandable  = True
        self.temporal_expandable = True
        self.parent_score = [-100000, [], 0, 0]
        self.generic_types = types
        self.hyp_id        = hyp_id
        self.kids          = []
        self.pos_inst      = []
        self.neg_inst      = []
        
        # There can be many terms in the body. So add all of them.
        if body  != None:
            for term in body:
                self.body.append(term)

        self.predicates = []
        
    def get_string(self):
        return Clause.__repr__(self)

    def get_head(self):
        return self.head

    def get_body(self):
        return self.body

    def get_score(self):
        score = [self.score[0]]
        score.append(len(self.score[1]))
        score.append(self.score[2])
        score.append(self.score[3])
        return score
        
    def get_all_predicates(self):
        """Returns all predicates as a list, also includes head predicate"""
        if len(self.predicates) is not 0:
            return self.predicates
        # First get the list of predicates from the body
        self.predicates = map(lambda x: x.op, self.body)
        # Now add the head predicate
        self.predicates.append(self.head.op)
        return self.predicates   
      
    def get_all_args(self):
        """Will only work for upto depth one. Need to improve """
        all_args = set([])
        all_args = all_args.union(self.head.args)
        for term in self.body:
            all_args = all_args.union(term.args)
        return all_args

    def get_all_args_avail(self):
        """Repitition is allowed unlike get_all_args where args are unique."""
        all_args = self.head.args[:]
        for term in self.body:
            all_args.append(term.args)
        return list(flatten(all_args))

    def get_all_vars(self):
        """Returns all unique variables as a list"""
        # If all_vars already computed return it.
        if len(self.all_vars) is not 0:
            return self.all_vars
        self.all_vars = unique(self.get_all_vars_avail())
        return self.all_vars
       
    def get_all_vars_avail(self):
        """Returns all unique variables as a list"""
        # Not sure why sometimes self.all_vars_avail is getting values from
        # If all_vars already computed return it.
        if len(self.all_vars_avail) is not 0:
            return self.all_vars_avail
        self.all_vars_avail.append(list(variables(self.head)))
        for term in self.body:
            self.all_vars_avail.append(list(variables(term)))
        # Flatten the list of lists and return as list instead of generator    
        self.all_vars_avail = list(flatten(self.all_vars_avail))
        return self.all_vars_avail
        
    def __repr__(self):
        if len(self.body) < 1: return str(self.head) + ' :- '      
        terms = [str(term) for term in self.body]    
        body_str = "%s%s" %(', '.join(terms),'.')
        return "%s%s%s"%(self.head.op,' :- ', body_str)

    def __eq__(self, other):
        """x and y are equal iff their heads and clauses are equal."""
        return (other is self) or (isinstance(other, Clause)
            and self.head == other.head and self.body == other.body)

    def __hash__(self):
        """Need a hash method so Hyps can live in dicts."""
        # Normal set objects are unhashable, so use frozenset
        return hash(frozenset(self.body))
        #return hash(self.head) ^ hash(tuple(self.body))

    def copy(self):
        """Creates and returns a duplicate hypothesis"""
        head = copy.copy(self.head)
        body = self.body[:]
        return Clause(head, body, self.hyp_id, self.generic_types)
    
    def pyswip_covers(self, prolog, prolog_modules, use_prolog, test, neg):        
        """Prolog modules are supplied as pos/neg examples. Just query the hyp in these modules
        and number instances that satisfy the query is the pos/neg score"""
        
        result_ind    = []
        # Stop after finding 10 results that satisfy the query
        max_res = 5
        semi_max_res = 2
                   
        if len(prolog_modules) is 0:
            return result_ind
        
        goals = map(repr, self.body)
        #apm = psutil.avail_phymem()/(1024)
        #log.info(YBT + 'AVAIL_PHY_MEM: ' + BBB + repr(neg) + '   ' + repr(apm) + RESET)
        # module should be added before goal and goal should be surrounded by round braces
        # ex: 'test2:(c(X), c(Y), c(Z))' and module name should start with small letter
        # Here blanket is just for debugging purpose and is by default empty unless I want to debug
        count = 0
        ocount = 0
        
        for (module, blanket) in prolog_modules:
            #blanket_info = re.findall('.*pos_(\d*)_(\d*).*', module)
            #if len(blanket_info) is not 0:
                ## This happens for pos blankets
                #vid = eval(blanket_info[0][0])
                #ex_ins = eval(blanket_info[0][1])
            ocount += 1
            pro_module = module + ':'            
            q = '(' + ", ".join(goals) + ')'
            q = pro_module + q
            log.info('query_hyp:')
            log.info(q)
            try:
                if neg:
                    apm1 = psutil.avail_phymem()#/(1024)
                    #log.info(YBT + 'AVAIL_PHY_MEM: ' + BBB + repr(neg) + '   ' + repr(apm1) + RESET)
                    
                    res = list(prolog.query(q, maxresult=max_res))
                    
                    #log.info(GBT + 'Pyswip Succe' + RESET)      
                    #apm2 = psutil.avail_phymem()#/(1024)
                    #if apm1 != apm2:
                        #log.info(BBB +  repr(len(res)) + RESET)
                    #else:
                        #log.info(GBT +  repr(len(res)) + RESET)
                    #log.info(YBT + 'AVAIL_PHY_MEM: ' + BBB + repr(neg) + '   ' + repr(apm2) + RESET)
                    if len(res) is not 0:    
                        if not test:
                            result_ind.append(len(res))
                        else:
                            result_ind.extend(res)                                        
                else:
                    res = list(prolog.query(q, maxresult=semi_max_res))
                    #res = list(prolog.query(q))
                    if len(res) is not 0: 
                        #result_ind.append({count:res})
                        result_ind.append({module:res})
                    count += 1
                del res        
                #log.info(GBT + 'Pyswip Succe in for hyp: ' + repr(self.body) + RESET)      
            except Exception:
                #if test:
                    #log.info(RBT + 'Pyswip Error' + RESET)  
                    #log.info(RBT + 'Pyswip Error in for hyp: ' + repr(self.body) + RESET)  
                pass
        
        return result_ind
    
    def reset_score(self):
        self.score = [-100000, [], 0, 0]
        
    def prove(self, KB):
        """Tries to prove the clause in the KB. Uses fol_bc_ask from logic.py.
        While giving to this function we need to change the format of the clause.
        """
        goals = []
        goals.append(self.head)
        goals.append(self.body)
        return fol_bc_ask(KB, goals)
    
    def toXML(self, xml_file=None):
        """ Write hyp to an xml file """
        import xml.dom.minidom
        
        doc = xml.dom.minidom.Document()
        # Create the <wml> base element
        xml_hyp = doc.createElement("hyp")
        doc.appendChild(xml_hyp)
        
        # Create the main <head> element
        head = doc.createElement("head")
        head.setAttribute("predicate", self.head.op)
        # Should I add args of head here?
        xml_hyp.appendChild(head)
        
        # Create the main <head> element
        body = doc.createElement("body")
        for i in self.body:
            atom = doc.createElement("atom")
            atom.setAttribute("predicate", i.op)
            for j in i.args:
                arg = doc.createElement("arg")
                if len(j.args) == 0:
                    arg.setAttribute("value", j.op)
                else:
                    # This is for interval element                    
                    arg.setAttribute("value", j.op)
                    for k in j.args:
                        sub_arg = doc.createElement("subarg")
                        sub_arg.setAttribute("value", k.op)
                        arg.appendChild(sub_arg)
                atom.appendChild(arg)
            body.appendChild(atom)   
        xml_hyp.appendChild(body)

        # minidoms 'toprettyxml' is not good enough. So this is just a wrapper  to fix those. Remove extra newlines etc.
        pretty_print = lambda doc: '\n'.join([line for line in doc.toprettyxml(indent=' '*2).split('\n') if line.strip()])
        
        if xml_file is None:
            log.info(pretty_print(doc))
            return doc
        file_object = open(xml_file, "w")
        file_object.write(pretty_print(doc))
        file_object.close()
    
    def toOWL(self, hypid, xml_file=None):
        """ Write hyp to an xml file useful to convert to .owl file."""
        import xml.dom.minidom
        
        def fixed_writexml(self, writer, indent="", addindent="  ", newl="\n"):
            # indent = current indentation
            # addindent = indentation to add to higher levels
            # newl = newline string
            writer.write(indent+"<" + self.tagName)
        
            attrs = self._get_attributes()
            a_names = attrs.keys()
            a_names.sort()
        
            for a_name in a_names:
                writer.write(" %s=\"" % a_name)
                xml.dom.minidom._write_data(writer, attrs[a_name].value)
                writer.write("\"")
            if self.childNodes:
                if len(self.childNodes) == 1 \
                  and self.childNodes[0].nodeType == xml.dom.minidom.Node.TEXT_NODE:
                    writer.write(">")
                    self.childNodes[0].writexml(writer, indent, addindent, newl)
                    writer.write("</%s>%s" % (self.tagName, newl))
                    return
                writer.write(">%s"%(newl))
                for node in self.childNodes:
                    node.writexml(writer,indent+addindent,addindent,newl)
                writer.write("%s</%s>%s" % (indent,self.tagName,newl))
            else:
                writer.write("/>%s"%(newl))
        # replace minidom's function with ours
        xml.dom.minidom.Element.writexml = fixed_writexml

        parts = ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H')
        locs  = ('l1', 'l2', 'l3', 'l4', 'l5', 'l6', 'l7', 'l8')
        ags   = ('a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8')
        event_locs = ('el1', 'el2', 'el3', 'el4', 'el5', 'el6', 'el7', 'el8')
        event_ags  = ('ea1', 'ea2', 'ea3', 'ea4', 'ea5', 'ea6', 'ea7', 'ea8')
        
        parts_ind = 0
        doc = xml.dom.minidom.Document()
        xml_hyp = doc.createElement("hyp")
        doc.appendChild(xml_hyp)
        hyp_id = doc.createElement('id')
        hyp_id_text = doc.createTextNode(str(hypid))
        hyp_id.appendChild(hyp_id_text)
        xml_hyp.appendChild(hyp_id)
                
        owlClass = doc.createElement("owlclass")
        xml_hyp.appendChild(owlClass)
        swrl_rule = doc.createElement("swrl")
        xml_hyp.appendChild(swrl_rule)
        conditions = doc.createElement("conditions")
        owlClass.appendChild(conditions)
        
        event_var = '?v:e'
        hasLoc    = 'has-location'
        hasAgent  = 'has-agent'
        hasPart   = 'has-part-'
        hasStart  = 'constraints:has-start-time'
        hasFinish = 'constraints:has-finish-time'
        swrl_text = self.head.op + str(hypid) + '(' + event_var + ') ^ '
        
        interval_map = {}
        location_map = {}
        agent_map    = {}
        e_location_map = {}
        e_agent_map = {}
        swrl_equalities = []
        temp_switch = False
        loc_ind = 0
        ag_ind  = 0
        e_loc_ind = 0
        e_ag_ind  = 0
        for atom in self.body:
            if atom.op not in temp_rel:
                sub_event_var = event_var + repr(parts_ind)
                condition_name = hasPart + parts[parts_ind]
                cond_hasPart = doc.createElement(condition_name)
                cond_hasPart_text = doc.createTextNode(atom.op)
                cond_hasPart.appendChild(cond_hasPart_text)
                conditions.appendChild(cond_hasPart)
                swrl_text += condition_name + '(' + event_var + ', ' + sub_event_var + ') ^ '
                parts_ind += 1
                
                for arg in atom.args:
                    if arg.op in zones:
                        # For zones arg
                        log.info('Processing zone: ' + repr(arg))
                        condition_name = hasLoc
                        cond_hasLoc = doc.createElement(condition_name)
                        cond_hasLoc_text = doc.createTextNode(arg.op)
                        cond_hasLoc.appendChild(cond_hasLoc_text)
                        conditions.appendChild(cond_hasLoc)
                        zone = str.lower(arg.op)                
                        loc_var = 'l' + repr(loc_ind)
                        loc_ind += 1                        
                        swrl_text += hasLoc + '(' + sub_event_var + ', ?v:' + loc_var + ') ^ '
                        
                        try:
                            location_map[zone].append('?v:' + loc_var)
                        except KeyError:
                            location_map[zone] = ['?v:' + loc_var]
                        
                        if zone not in e_location_map:
                            event_loc_var = 'el' + repr(e_loc_ind)
                            e_location_map[zone] = event_loc_var
                            e_loc_ind += 1
                            swrl_text += hasLoc + '(' + event_var + ', ?v:' + event_loc_var + ') ^ '
                            swrl_equalities.append(('?v:' + loc_var, '?v:' + event_loc_var))

                    elif arg.op != 'int':
                        log.info('Processing vehicle: ' + repr(arg))
                        # For vehicle arg
                        condition_name = hasAgent
                        cond_hasAgent  = doc.createElement(condition_name)
                        # Supply only the last part of the type hierarchy
                        cond_hasAgent_text = doc.createTextNode(arg.op.split('::')[-1])
                        cond_hasAgent.appendChild(cond_hasAgent_text)
                        conditions.appendChild(cond_hasAgent)
                        obj = str.lower(arg.args[0].op)
                        agent = 'a' + repr(ag_ind)
                        ag_ind += 1
                        swrl_text += hasAgent + '(' + sub_event_var + ', ?v:' + agent + ') ^ '
                        
                        try:
                            agent_map[obj].append('?v:' + agent)
                        except KeyError:
                            agent_map[obj] = ['?v:' + agent]
                            
                        if agent not in e_agent_map:
                            event_ag_var = event_ags[e_ag_ind]
                            e_agent_map[agent] = event_ag_var
                            e_ag_ind += 1
                            swrl_text += hasAgent + '(' + event_var + ', ?v:' + event_ag_var + ') ^ '
                            swrl_equalities.append(('?v:' + agent, '?v:' + event_ag_var))
                    else:
                        log.info('Processing interval: ' + repr(arg))
                        # For temporal arg
                        interval_map.update({arg: sub_event_var})
                        #swrl_text += hasStart + '(' + sub_event_var + ', ?v:' + str.lower(arg.args[0].op) + ') ^ '
                        #swrl_text += hasFinish + '(' + sub_event_var + ', ?v:' + str.lower(arg.args[1].op) + ') ^ '
        
            else:
                if not temp_switch:
                    temp_switch = True
                    swrl_text = swrl_text.strip(' ^ ')
                    swrl_text += ' -> '
                swrl_text += 'allen:' + atom.op + '(' + interval_map[atom.args[0]] + ', ' + interval_map[atom.args[1]] + ') ^ '
                # Add allen's relation between aggregate and its parts. This will work only if there is only one temporal 
                # relation in the hyp otherwise it is not possible to get end points of the intervals.
                if atom.op == 'before':
                    swrl_text += 'allen:starts'   + '(' + event_var + ', ' + interval_map[atom.args[0]] + ') ^ '
                    swrl_text += 'allen:finishes' + '(' + event_var + ', ' + interval_map[atom.args[1]] + ') ^ '
                elif atom.op == 'overlaps':
                    swrl_text += 'allen:starts'   + '(' + event_var + ', ' + interval_map[atom.args[0]] + ') ^ '
                    swrl_text += 'allen:finishes' + '(' + event_var + ', ' + interval_map[atom.args[1]] + ') ^ '    
                elif atom.op == 'during':
                    swrl_text += 'allen:starts'   + '(' + event_var + ', ' + interval_map[atom.args[1]] + ') ^ '
                    swrl_text += 'allen:finishes' + '(' + event_var + ', ' + interval_map[atom.args[1]] + ') ^ '        
                
        for pair in swrl_equalities:
            swrl_text += 'swrlb:equal(' + pair[0] + ', ' + pair[1] + ') ^ '
        for ag in agent_map:
            first_ag = agent_map[ag][0]
            for i in xrange(1, len(agent_map[ag])):
                second_ag = agent_map[ag][i]
                swrl_text += 'swrlb:equal(' + first_ag + ', ' + second_ag + ') ^ '
                
        for loc in location_map:
            first_loc = location_map[loc][0]
            for i in xrange(1, len(location_map[loc])):
                second_loc = location_map[loc][i]
                swrl_text += 'swrlb:equal(' + first_loc + ', ' + second_loc + ') ^ '
                
        swrl_text = swrl_text.strip(' ^ ')        
        swrl_rule.setAttribute('name' , self.head.op)
        swrl_rule.setAttribute('value' , swrl_text)

        # minidoms 'toprettyxml' is not good enough. So this is just a wrapper  to fix those. Remove extra newlines etc.
        pretty_print = lambda doc: '\n'.join([line for line in doc.toprettyxml(indent=' '*2).split('\n') if line.strip()])
        
        if xml_file is None:
            log.info(pretty_print(doc))
            return doc
        file_object = open(xml_file, "w")
        doc.writexml(file_object)
        file_object.close()        
#____________________________________________________________________________________

class Modes(object):
    def __init__(self, recall, mode_expr, type=True):
        """Class for mode declarations. Takes expression as body of the mode
        Second argument should be 'False' for Body mode. Default is True for Head Mode"""
        self.recall = recall
        self.ishead = type
        self.mode = mode_expr
        self.predicate = mode_expr.op
        self.subst   = [] 
        self.modes = []
        # self.modes is a list of tuples like ('+', variable_type)
        # Variable type is liek Zone, Vehicle etc.
        # '#' in Progol is '$' 
        for arg in self.mode.args:
            if arg.op.find('-') != -1:
                self.modes.append(('-', arg.op[0:-1]))
            elif arg.op.find('+') != -1:
                self.modes.append(('+', arg.op[0:-1]))
            elif arg.op.find('$') != -1:
                # This is the case for '#' in Progol. '#' in python has problems
                self.modes.append(('$', arg.op[0:-1]))
            else:
                log.error('Variables in Mode declaration should end with [+-$]')
                raise Exception('Variables in Mode declaration should end with [+-$]')
            
            
class Hyp(Clause):
    """Class definition for hypothesis"""
    def __init__(self, clauses):
        # Sample input: hyp = Hyp(e,[[f,g],[g,f]]) where e,f,g are valid expressions
        # and definite clauses.
        self.head = clauses[0].head
        self.clauses = []
        self.score = 0

        # There can be many clauses for a single hyp. So add all of them to the
        # clauses structure
        for clause in clauses:
            self.clauses.append(clause)
        
        self.str = Hyp.__repr__(self)

    def get_head(self):
        return self.head

    def get_clauses(self):
        return self.clauses

    def __repr__(self):
        if len(self.clauses) < 1: return ''
        clauses_str = []
        for clause in self.clauses:
            clauses_str.append(clause.str)
        return "%s"%('\n'.join(clauses_str))

    def __eq__(self, other):
        """x and y are equal iff their heads and clauses are equal."""
        return (other is self) or (isinstance(other, Hyp)
            and self.head == other.head and self.clauses == other.clauses)

    def __hash__(self):
        """Need a hash method so Hyps can live in dicts."""
        return hash(self.head) ^ hash(tuple(self.clauses))

    def copy(self):
        """Creates and returns a duplicate hypothesis"""
        head = copy.copy(self.head)
        clauses = self.clauses[:]
        return Hyp(head, clauses)

    def covers(self, example, KB):
        """Tries to see if the hyp covers the example in the KB. Uses fol_bc_ask from logic.py.
        It does for each clause in the hyp and returns the results in a list of True, Flase.
        """
        result = []
        for clause in self.clauses:
            result.append(clause.covers(example,KB))
        return result

    def covers_n(self, ex_KB, KB):
        """Returns list of lists of indices of covered examples """
        result = []
        for clause in self.clauses:
            result.append(clause.covers_n(ex_KB,KB))
        return result

    def calc_score(self, pos_KB, neg_KB, KB):
        """Calculates the score of the Clause. Right now it is just based on
        the examples covered"""
        for clause in self.clauses:
            self.score = self.score + clause.score(pos_KB, neg_KB, KB)
        return self.score

rel_names = ['re', 'de', 'at', 'ap', 'pu', 'st', 'primitive_bend', 'primitive_catch' , 'primitive_dig_stand_long',\
             'primitive_fall' ,'primitive_jump','primitive_kick','primitive_raise','primitive_reach','primitive_run',\
             'primitive_swing_horizontal','primitive_swing_vertical','primitive_throw','primitive_walk',\
             'primitive_wave','r_s', 'r_n', 'r_e', 'r_w', 'r_ne', 'r_nw', 'r_se', 'r_sw', 'r_eq',\
             'p', 'eq', 'pi', 'po', 'dis', 'ul', 'ur', 'dl', 'dr', 'sl', 'fa', 'sw', 'hu', 'la', 'sa',]

sp_rel = set(rel_names)

sp_rel = set([])
sp_rel.add('con')
sp_rel.add('sur')
sp_rel.add('rel_1')
sp_rel.add('vehicle_Stopped')
sp_rel.add('vehicle_Removing')
sp_rel.add('vehicle_Positioned')
sp_rel.add('vehicle_Leaves_Zone')
sp_rel.add('vehicle_Enters_Zone')
sp_rel.add('vehicle_Positioning')
sp_rel.add('vehicle_Inside_Zone')
sp_rel.add('vehicle_Stopped_Inside_Zone')

temp_rel = set([])
temp_rel.add('overlaps')
temp_rel.add('meets')
temp_rel.add('before')
temp_rel.add('starts')
temp_rel.add('finishes')
temp_rel.add('during')            

zones = ('era', \
         'pbb_zone',    \
         'left_tk_zone',\
         'left_fwd_pd_zone', \
         'left_aft_pd_zone',\
         'right_aft_ts_zone', \
         'right_aft_pd_zone', \
         'right_aft_bulk_ts_zone',\
         'right_aft_bl_zone',\
         'right_aft_ld_zone',\
         'right_fwd_ld_zone',\
         'right_fwd_pd_zone',\
         'right_fwd_ts_zone',\
         'gpu_zone', \
         'departure_zone',\
         'arrival_zone')
                                               
def get_relation_predicates(hyp, relation_type):
    terms = []
    if relation_type is 'spatial':
        target_rel = sp_rel
    elif relation_type is 'temporal':
        target_rel = temp_rel        
    for term in hyp.body:
        if term.op in target_rel:
            terms.append(term)
    return terms        
            

if __name__ == '__main__':
    e = expr('enter_zone(X)')
    f = expr('con(X, Y)')
    g = expr('sur(X, Y, int(U,V))')
    
    ex = expr('enter_zone(za)')
    c1 = Clause(e,[f,g], 0)
    var = c1.get_all_vars_avail()
    
    ans = c1.covers(ex, ilp_test_kb)
    pos = c1.covers_n(pos_ex, ilp_test_kb)
    neg = c1.covers_n(neg_ex, ilp_test_kb)
    cost = c1.calc_score(pos_ex,neg_ex, ilp_test_kb)
    print pos
    print neg
    print cost
    c2 = Clause(e,[g,f])
    hyp = Hyp([c1,c2])
    print c1
    print c2
    print hyp
    print hyp.head
    print hyp.clauses
    print hyp.clauses[0].head
    print hyp.clauses[0].body
    print hyp.clauses[0].body[0].args

    
