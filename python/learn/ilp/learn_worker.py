#############################################################################
#
#   Author   : Krishna Sandeep Reddy Dubba
#   Email    : scksrd@leeds.ac.uk
#   Institute: University of Leeds, UK
#
#############################################################################

def learn_event_par_worker(argv=None, all_prolog_modules=None):

    def m_process_worker(input_queue, output_queue, ilp_best_first_graph_search):
        mp_ilp = input_queue.get()
        (solution_clause, STATUS) = ilp_best_first_graph_search(mp_ilp, mp_ilp.f)
        output_queue.put((solution_clause, STATUS))        
        
    def filter_temporal_bc(spatial_bc_body, temporal_bc_body):        
        """Get all temporal terms from temporal_bc_body that has intervals in any spatial relation
        in spatial_bc_body
        """
        from base.ilp.hyp import sp_rel
        
        temporal_args = {}
        valid_temporal_terms = []
        # Collect all temporal intervals from spatial relations
        for term in spatial_bc_body:
            if term.op in sp_rel:
                temporal_args.update({term.args[-1]:1})
        valid_temporal_args = {}            
        # Now check if the two intervals of temporal term are in the collected temporal intervals
        for term in temporal_bc_body:
            if term.args[0] != term.args[1] and term.args[0] in temporal_args and term.args[1] in temporal_args:
                # redundant temporal relation for (b,a) is present for interval (a,b). So discard one relation. 
                if tuple(term.args) not in valid_temporal_args:
                    valid_temporal_args.update({tuple(term.args):1})
                    valid_temporal_args.update({(term.args[1],term.args[0]):1})                
                    valid_temporal_terms.append(term)
            
        return valid_temporal_terms        

    def get_solution_hyp(class_label, modeh, modeb, test_data_key, train_pos_ex_dict, train_pos_ex_data, \
                         train_neg_ex_data, prolog, solution_hyp, inTerms, sol, constants, DEBUG=True):
        # Removed data_f as we don't need bg_KB now
        import copy
        import gc
        import os
        import random        
        import re
       
        from multiprocessing     import Process, Queue, current_process, freeze_support
       
        from base.utils.search   import ilp_best_first_graph_search
        from base.utils.cpu_load import mem_avail
        from learn.ilp.hyp       import Clause
        from learn.ilp.ilp       import ILP
        
        pos_blankets = []
        pos_blankets_dict = {}        
        #for vid in train_pos_vid_data:
            #for ins in vid:
                #module = ins[0]
                #blanket_info = re.findall('.*pos_(\d*)_(\d*)', module)[0]
                #vid_num = eval(blanket_info[0])
                #ex_ins  = eval(blanket_info[1])
                #pos_blankets_dict.update({(vid_num, ex_ins):ins})
        
        for ins in train_pos_ex_data:
            module  = ins[0]
            ex_num = module
            pos_blankets_dict.update({ex_num:ins})
                
        pos_blankets = pos_blankets_dict.values()  
        i = 0 #test_data_list[0]
        solution_hyp[event][i] = []    
        inTerms[event][i]      = {}
        sol[i]                 = {}
        pos_eval_time          = 0
        neg_eval_time          = 0
        # Need to call this in a loop until all positive examples are covered.
        # Then append all the solutions into a hypothesis. 
        no_sol_count = 0
        # Repeat until all positive examples are covered
        input_data_queue  = Queue()
        output_data_queue = Queue()
        
        train_pos_ex = FolKB(train_pos_ex_dict.values())
        train_pos_ex.clauses[modeh[0].predicate] = train_pos_ex_dict.values()
        while len(train_pos_ex.clauses[modeh[0].predicate]) != 0:
            ilp = ILP(constants[:-1], None, class_label, modeh, modeb, train_pos_ex, pos_blankets, train_neg_ex_data, prolog)
            
            log.info('')
            log.info(MBT + 'Examples yet to cover: ' + RESET + RBB + repr(len(ilp.pos_ex.clauses[ilp.modeh[0].predicate])) + RESET)
            #apm = mem_avail()
            apm = psutil.avail_phymem()/(1024*1024)
            log.info(YBT + 'AVAILABLE MEMORY: ' + BBB + repr(apm) + RESET)
            # A different initial clause is generated based on pos_ex remaining
            ilp.bottom_clause = None
               
            # no_sol_count gives the number of example for which bottom_clause has non zero length body
            (no_sol_count, initial_clause_flag) = ilp.generate_initial_clause(no_sol_count)
            if not initial_clause_flag:
                log.info(RBB + class_label + ' test_vid-' + repr(i) + ': Could not find proper solution. No proper' \
                         + ' bottom clause was constructed :-(' + RESET)
                break 
        
            ilp.bottom_clause = ilp.full_bottom_clause   
            apm = psutil.avail_phymem()/(1024*1024)
            log.info(YBT + 'AVAILABLE MEMORY: ' + BBB + repr(apm) + RESET)
            log.info(os.uname()[1])
            (solution_clause, STATUS) = ilp_best_first_graph_search(ilp, ilp.f)
            if DEBUG:
                (solution_clause, STATUS) = ilp_best_first_graph_search(ilp, ilp.f)
            else: 
                input_data_queue.put(ilp)
                log.info(GBT + 'Finding hyp in a seperate process ...' + RESET)
                Process(target=m_process_worker, args=(input_data_queue, output_data_queue, ilp_best_first_graph_search)).start()
                (solution_clause, STATUS) = output_data_queue.get()
        
            solution_clause = solution_clause.state
            if STATUS == OUT_OF_MEMORY:
                break
                          
            (score, pos_cov, neg_cov, tot_pos) = solution_clause.score
            if len(pos_cov) is not 0:
                no_sol_count = 0
                solution_hyp[class_label][i].append(solution_clause)
                for key in ilp.inTerms.keys():
                    try:
                        inTerms[class_label][i][key].append(ilp.inTerms[key])
                    except KeyError:
                        inTerms[class_label][i][key] = [ilp.inTerms[key]]                                           
                remove_exp      = []
                # Collect all positive examples that are to be removed and then remove
                for k in pos_cov:
                    #remove_exp.append(train_pos_ex.clauses[modeh[0].predicate][k])
                    train_pos_ex_dict.pop(k)
                    pos_blankets_dict.pop(k)
                if len(train_pos_ex_dict.values()) is 0:
                    # All examples are covered.
                    # Delete ILP to save memory 
                    pos_eval_time += ilp.pos_eval_time
                    neg_eval_time += ilp.neg_eval_time
                    break
                # Update the pos examples and blankets
                train_pos_ex.clauses[modeh[0].predicate] = train_pos_ex_dict.values()
                pos_blankets = pos_blankets_dict.values()
            else:
                no_sol_count += 1
                if no_sol_count == len(train_pos_ex.clauses[modeh[0].predicate]):
                    log.info(RBT + event + ' test_vid-' + repr(i) + ': Could not find proper solution :-(' + RESET)
                    # Delete ILP to save memory 
                    pos_eval_time += ilp.pos_eval_time
                    neg_eval_time += ilp.neg_eval_time
                    break
            # Delete ILP to save memory 
            pos_eval_time += ilp.pos_eval_time
            neg_eval_time += ilp.neg_eval_time

        if not isinstance(solution_hyp[class_label][i], int):
            sol[i]['hyp'] = solution_hyp[class_label][i]        # First store hyp with train_score
        else:
            log.info(RBB + class_label + ' test_vid-' + repr(i) + ': Solution hypotheis is empty')
            sol[i]['hyp'] = []            
        return [solution_hyp, inTerms, sol, (pos_eval_time, neg_eval_time)]        

    
    ######   MAIN  ########
    import ConfigParser
    import cPickle as pickle    
    import gc
    import logging
    import os
    import sys
    import time
    from os.path import join
    from optparse import OptionParser
    
    try:
        ROOT_DIR = os.environ['LEARN_ROOT']        
    except KeyError:
        ROOT_DIR = '/home/csunix/visdata/cofriend/sandeep/Dropbox/code/my_code/'    
        
    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(ROOT_DIR + '/config.cfg')       
    release   = eval(cfg_parser.get('PARAMETERS', 'release'))    
    host      = os.uname()[1].split('.')[0]
    
    if release:
        py_version   = str(sys.version[:3])
    else:
        py_version   = cfg_parser.get('PARAMETERS', 'py_version')
        
    sys.path.append(join(ROOT_DIR,     'lib/python' + py_version +'/site-packages'))
        
    from pyswip import Prolog, PrologError
    import base.utils.psutil as psutil
    from base.ilp.logic          import FolKB, Expr
    from base.base_constants     import RBB, GBB, YBB, BBB, RBT, CBT, YBT, MBT, GBT, \
                                        GT, YT, MT, RT, CT, RESET, OUT_OF_MEMORY, NORMAL
    from base.utils.Logging      import initialize_logging
    from base.utils.cpu_load     import mem_avail
    from learn.ilp.ilp           import ILP
    from learn.utils.prolog_utils import assert_example_to_prolog
    
    # Setup command line options
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-d", "--dpath",     dest="out_dir",     default="", help="output directory (default '')")
    parser.add_option("-t", "--tag",       dest="tag",         default="", help="name tag (default '')")    
    parser.add_option("-y", "--class",     dest="class_label", default="", help="Class label name name")
    parser.add_option("-l", "--logdir",    dest="logdir",    default=".", help="log DIRECTORY (default ./)")
    parser.add_option("-f", "--logfile",   dest="logfile",   default="project.log", help="log FILE (default project.log)")
    parser.add_option("-v", "--loglevel",  dest="loglevel",  default="debug", help="logging level (debug, info, error)")    
    parser.add_option("-m", "--module",    dest="module",    default="", help="logger name (empty for main script or root logger)")    
    parser.add_option("-q", "--quiet",     dest="quiet",     default=False, action="store_true", help="do not log to console")
    parser.add_option("-n", "--filequiet", dest="fquiet",    default=False, action="store_true", help="do not log to file")
    parser.add_option("-c", "--clean",     dest="clean",     default=False, action="store_true", help="remove old log file")
    parser.add_option("-p", "--parallel",  dest="parallel",  default=False, action="store_true", help="Parallel Processing")    
    parser.add_option("-b", "--efile",     dest="efile",     default="", help="examples file")    
    parser.add_option("-k", "--kf_count",  dest="kf_count",  default="1", help="K-fold validation count")    
    parser.add_option("-a", "--train_list",dest="train_list",default="[]", help="train_data_key_list")    
    parser.add_option("-s", "--test_list", dest="test_list", default="[]", help="test_data_key_list")
    
    # Process command line and config file options
    (options, args) = parser.parse_args(argv)
    
    # Setup logger format and output locations
    log = initialize_logging(options.__dict__)
    start_time = time.asctime()
    log.info(" ")
    log.info(" ")
    log.info("START TIME: " + BBB + start_time + RESET)
    log.info("HOST      : " + host)
    log.info("CLASS     : " + options.class_label)  
  
    try:
        class_label       = options.class_label
        tag               = options.tag
        OUT_ROOT_DIR      = options.out_dir        
        all_examples_file = options.efile
        k_fold_count      = eval(options.kf_count)      
        # Train and test list are not supplied as input here. Just dummy initialization
        train_data_list    = eval(options.train_list)
        test_data_list     = eval(options.test_list)
        
        learn_cmd = 'python' + ' ' + os.path.abspath(__file__) + \
                            ' -l ' + options.logdir + ' -m base -v ' + options.loglevel + ' -f ' + options.logfile + \
                            ' -y ' + class_label + ' -t ' + tag + ' -d ' + options.out_dir + ' -k ' + options.kf_count + \
                            ' -a "' + options.train_list + '" -s "' + options.test_list + '" -e ' + options.efile + ' -q'
        
        log.info('Command used to run:')
        log.info(BBB + learn_cmd + RESET)
        log.info('')

        train_neg_ex_data = []
        train_pos_ex_data = []
                
        log.info('--------------------------------------------------------------')    
        log.info(GBB + event + ': K_FOLD ITERATION - ' + RESET + repr(k_fold_count))
        log.info('--------------------------------------------------------------')    
        log.debug('Training examples: ' + options.train_list)
        log.debug(MBT + 'Test examples  : ' + RESET + GBB + options.test_list + RESET)
        log.info('')
        
        sol_file = join(OUT_ROOT_DIR, 'remote_sols_' + class_label, class_label + '_sol_100extfactor_db' + tag + '_tv_' + repr(k_fold_count) + '.p')
        if not os.path.isdir(join(OUT_ROOT_DIR, 'remote_sols_' + class_label)):
            os.makedirs(join(OUT_ROOT_DIR, 'remote_sols_' + class_label))
        
        var_depth    = eval(cfg_parser.get('PARAMETERS', 'var_depth'))        
        max_terms    = eval(cfg_parser.get('PARAMETERS', 'max_terms'))
        sp_max_terms = eval(cfg_parser.get('PARAMETERS', 'sp_max_terms'))
        max_bc_length    = eval(cfg_parser.get('PARAMETERS', 'max_bc_length'))
        num_refine_ops   = eval(cfg_parser.get('PARAMETERS', 'num_refine_ops'))
        min_pos_examples = eval(cfg_parser.get('PARAMETERS', 'min_pos_examples'))
        temp_rel_mandatory  = eval(cfg_parser.get('PARAMETERS', 'temporal_rel_mandatory'))
        # Should we combine the spatial and temporal terms while constructing the hyp?
        combine_spatial_temporal = eval(cfg_parser.get('PARAMETERS', 'combine_spatio_temporal'))   
        min_score_to_expand_hyp  = eval(cfg_parser.get('PARAMETERS', 'min_score_to_expand_hyp'))
        MAIL_FLAG = eval(cfg_parser.get('PARAMETERS', 'mail_flag'))
        ONLY_ERROR_MAIL = eval(cfg_parser.get('PARAMETERS', 'only_error_mail'))
        mail_id = cfg_parser.get('MAIL', 'to_mail')  
        EVALUATION               = eval(cfg_parser.get('PARAMETERS', 'evaluation'))
       
        rel_data_file = cfg_parser.get('INPUT', 'rel_file')
 
        constants = (var_depth, max_terms, sp_max_terms, num_refine_ops, max_bc_length, \
                     min_score_to_expand_hyp, combine_spatial_temporal)
        
        log.info("TAG       : " + tag)
        log.info("VAR_DEPTH         : " + repr(var_depth))        
        log.info("MAX_TERMS         : " + repr(max_terms))
        log.info("RELEASE_VERSION?  : " + repr(release))
        log.info("MAX_SPATIAL_TERMS : " + repr(sp_max_terms))
        log.info("MIN_POS_EXAMPLES  : " + repr(min_pos_examples))
        log.info("NUM_REFINE_OPS    : " + repr(num_refine_ops))
        log.info("MAX_BOTTOM_CLAUSE_LENGTH: " + repr(max_bc_length))
        log.info("MIN_SCORE_TO_EXPAND_HYP : " + repr(min_score_to_expand_hyp))
        log.info("TEMPORAL_REL_MANDATORY  : " + repr(temp_rel_mandatory))
        log.info("COMBINE_SPATIO_TEMPORAL : " + repr(combine_spatial_temporal))             
        log.info("")
        log.info("")
        log.info(YBT + "Data PATHS:" + RESET)
        log.info("ROOT_DIR             : " + ROOT_DIR)
        log.info("OUT_ROOT_DIR         : " + OUT_ROOT_DIR)
        log.info("SOLUTION_FILE        : " + sol_file)
        log.info("RELATIONAL_DATA_FILE : " + all_blankets_file)        
        log.info("")

        f_all_examples_file = open(all_examples_file)
        all_prolog_modules  = pickle.load(f_all_examples_file)
        f_all_blankets_file.close()
        
        (modeh, modeb)      = all_prolog_modules['modes']
        pos_ex              = all_prolog_modules['pos_ex']
        test_pos_ex         = all_prolog_modules['test_pos_ex']
        pos_prolog_modules  = all_prolog_modules['pos']
        neg_prolog_modules  = all_prolog_modules['neg']
        test_prolog_modules = all_prolog_modules['test']        
        
        apm = psutil.avail_phymem()/(1024*1024)
        log.info(YBT + 'AVAILABLE MEMORY: ' + BBB + repr(apm) + RESET)
        
        # Initialize prolog engine
        prolog = Prolog()
        str2num_file = os.path.join(ROOT_DIR, 'bin', 'str2num.pl')
        prolog.consult(str2num_file)
        
        train_data_list = pos_prolog_modules.keys()
        train_data_list.extend(neg_prolog_modules.keys())
        test_data_list = test_prolog_modules.keys()
       
        temp_train_pos_ex_data = []
        train_pos_ex_dict = {}
        for ex in train_data_list:
            if ex in pos_ex:
                for ins in pos_ex[ex]:
                    train_pos_ex_dict.update({ex:ins})
            else:
                log.debug('Pos example for vid ' + repr(ex) + ' not present')
            if ex in neg_prolog_modules:  
                train_neg_vid_data.append(neg_prolog_modules[ex])
            if ex in pos_prolog_modules and len(pos_prolog_modules[ex]) != 0:
                # Some videos don't have positive examples
                for example_ins in pos_prolog_modules[ex]:
                    temp_train_pos_vid_data.append([example_ins[1]['size'], example_ins])
      
        # Sort the blankets based on size. The smallest should be used for bottom clause        
        temp_train_pos_ex_data.sort()        
        for (size, ex_data) in temp_train_pos_ex_data:
            train_pos_ex_data.append(ex_data)
         
        train_pos_ex = FolKB(train_pos_ex_dict.values())
        # Since the pos ex has only one arg in it, the .op will return the whole hierarchy as op.
        #train_pos_ex.clauses[
        example_dir = join(OUT_ROOT_DIR, 'examples')        
        for ex in pos_prolog_modules:
            for i in xrange(len(pos_prolog_modules[ex])):
                pos_prolog_module  = pos_prolog_modules[ex][i][0]
                pos_prolog_example = pos_prolog_modules[ex][i][1]
                assert_example_to_prolog(pos_prolog_example, prolog, pos_prolog_module)
    
        for ex in neg_prolog_modules:
            for i in xrange(len(neg_prolog_modules[ex])):
                neg_prolog_module  = neg_prolog_modules[ex][i][0]
                neg_prolog_example = neg_prolog_modules[ex][i][1]
                assert_example_to_prolog(neg_prolog_example, prolog, neg_prolog_module)

        apm = psutil.avail_phymem()/(1024*1024)
        log.info(YBT + 'AVAILABLE MEMORY after asserting blankets in Prolog: ' + BBB + repr(apm) + RESET)
        
        solution_hyp  = {}
        inTerms       = {}
        sol           = {}
        event_ind     = 0
        pos_eval_time = 0
        neg_eval_time = 0
        
        solution_hyp[event] = {}
        inTerms[event]      = {}
        temp_sol            = {}
    
        [solution_hyp, inTerms, temp_sol, eval_time] = get_solution_hyp(class_label, modeh, modeb, test_data_list,\
                                                                   train_pos_ex_dict, train_pos_ex_data, \
                                                                   train_neg_ex_data, prolog, solution_hyp, \
                                                                   inTerms, temp_sol, constants)
        pos_eval_time = eval_time[0]
        neg_eval_time = eval_time[1]
    
        # Test the HYP        
        sol[event] = {}
        sol[event][k_fold_count] = {}
        sol[event][k_fold_count]['tp'] = []
        sol[event][k_fold_count]['fp'] = []
        sol[event][k_fold_count]['tn'] = []
        sol[event][k_fold_count]['fn'] = []
        sol[event][k_fold_count]['test_results'] = {}
        sol[event][k_fold_count]['hyp'] = solution_hyp[event][0]
        sol[event][k_fold_count]['inTerms'] = inTerms[event][0]
        
        pickle.dump(sol, open(sol_file, 'w'), 1) 
        test_time_start = time.time()
        
        total_test_vids = 0 
        log.info(len(test_prolog_modules.keys()))
        log.info(len(test_data_key))
        for test_prolog_module in test_prolog_modules:
            total_test_vids += 1
            test_vid =  test_prolog_module.split('_test')[0]
            bg_KB = FolKB()
            bg_KB.clauses = test_prolog_modules[test_prolog_module][1]
            intvs = []
                
            for intv in bg_KB.clauses['int']:
                intvs.append(intv.args[0].op)
                intvs.append(intv.args[1].op)
            if len(intvs) == 0:
                continue
            start_frame = min(intvs)
            end_frame   = max(intvs)
          
            intv = Expr('int', [start_frame, end_frame])
            test_pos_ex = [Expr(event, intv)]
            pos_vid_data = []
            
            test_prolog_blanket = test_prolog_modules[test_prolog_module][1]
            sol[event][test_vid] = {}
            assert_blanket_to_prolog_str_int(test_prolog_blanket, prolog, test_prolog_module)
               
            # The test vid data. This is used for negative score in testing
            test_blanket_data = [[(test_prolog_module, test_prolog_blanket),],]
            
            # Some videos does not have event instances, in that case we don't have
            # postive test example
            #pos_ex = test_pos_ex
            ilp = ILP(constants[:-1], color_map_file, event, modeh, modeb, None, [], test_blanket_data, prolog)
            #ilp = ILP(constants[:-1], color_map_file, event, modeh, modeb, pos_ex, [], test_blanket_data, prolog)
            #ilp = ILP(constants[:-1], color_map_file, event, modeh, modeb, pos_ex, test_pos_vid_data, test_neg_vid_data, prolog)
      
            # ilp.pos_ex_intv is used to see whether intervals are in positive area
            #for ex in pos_ex.clauses[modeh[0].predicate]:
                #ilp.pos_ex_intv.append((ex.args[-1].args[0].op,ex.args[-1].args[1].op))
                
            #for ex in test_pos_ex[test_vid]:
            for ex in test_pos_ex:
                #ilp.pos_ex_intv.append((ex.args[-1].args[0].op,ex.args[-1].args[1].op))
                # Since there is only one arg in the example, i.e. interval, no need to look that deep.
                ilp.pos_ex_intv.append((ex.args[0].op, ex.args[1].op))
    
            dup_sol_hyp = []
            #if not EVALUATION:                    
                #if event + '_' in test_vid:
                    #log.info('Testing hyp for video ' + GBT + repr(test_vid) + RESET)
                #else:
                    #log.info('Testing hyp for video ' + RBT + repr(test_vid) + RESET)
                
            hit = False    
            for hyp in solution_hyp[event][0]: #[test_vid]:
                # Loop as there might be multiple hyps (disjunction)
                dup_hyp = hyp.copy()
                ilp.calc_score(dup_hyp,test=True)                    
                dup_sol_hyp.append(dup_hyp)
                # See if the hyp satisfies test video
                if dup_hyp.get_score()[1] > 0:
                    hit = True
            
            if event + '_' in test_vid and hit:        
                sol[event][k_fold_count]['tp'].append(1)
            elif event + '_' in test_vid and not hit:        
                sol[event][k_fold_count]['tp'].append(0)
                sol[event][k_fold_count]['fn'].append(1)
            elif event + '_' not in test_vid and hit:        
                sol[event][k_fold_count]['fp'].append(1)
            elif event + '_' not in test_vid and not hit:        
                sol[event][k_fold_count]['fp'].append(0)
                sol[event][k_fold_count]['tn'].append(1)
                
            sol[event][k_fold_count][test_vid] = {}    
            sol[event][k_fold_count]['test_results'][test_vid] = hit
            #if not EVALUATION:
                #if hit:
                    #log.info('Test result for ' + GBT + repr(test_vid) + RESET)
                #else:
                    #log.info('Test result for ' + RBT + repr(test_vid) + RESET)
            
            #if len(solution_hyp[event][test_vid]) is not 0:
            if len(solution_hyp[event][0]) is not 0:
                sol[event][k_fold_count][test_vid]['test_score'] = [c.score for c in dup_sol_hyp]
            sol[event][k_fold_count][test_vid]['start_end'] = test_prolog_blanket['start_end']
                
        log.info('Total videos test: ' + GBB + repr(total_test_vids) + RESET)
        test_time_end = time.time()
        log.info(GBB + 'TP: ' + RESET + repr(sol[event][k_fold_count]['tp']))
        log.info(RBB + 'FP: ' + RESET + repr(sol[event][k_fold_count]['fp']))        
        log.info(RBB + 'FN: ' + RESET + repr(sol[event][k_fold_count]['fn']))  
        log.info(GBB + 'TN: ' + RESET + repr(sol[event][k_fold_count]['tn']))
        pickle.dump(sol, open(sol_file, 'w'), 1)   
        log.info('Dumped solution file: ' + sol_file)
        log.info(BBB + 'Total Evaluation time for pos ex:' + RESET + repr(pos_eval_time))
        log.info(BBB + 'Total Evaluation time for neg ex:' + RESET + repr(neg_eval_time))
        log.info(BBB + 'Total evaluation time for ' + repr(total_test_vids) + ' vids:' + RESET + repr(test_time_end - test_time_start))
        log.info('')
        log.info('')
        return sol
    except Exception:
        import traceback
        err_msg = traceback.format_exc(sys.exc_info())        
        log.error(RBT + err_msg + RESET)
        log.error(RBB + 'ERROR' + RESET)
        MAIL = 'python ' + BASE_LIB + 'utils/mail.py'
        try:    
            mail_cmd = MAIL + ' --body=ERROR_"' + tag + '\n' + err_msg + '" --subject=Error_in_learn_vigil_event_par_worker_' + event + '@' + host + ' -t ' + mail_id 
            # Use this incase of emergency
            # mail_cmd = MAIL + ' --body=ERROR_"' + '\n' + err_msg + '" --subject=Error_in_learn -t scksrd@leeds.ac.uk' 
        except Exception:
            mail_cmd = MAIL + ' --body=ERROR_"' + '\n' + err_msg + '" --subject=Error_in_learn_vigil_event_par_worker_' + '@' + host + ' -t ' + mail_id 
            pass

        if MAIL_FLAG:
            os.system(mail_cmd)               

if __name__ == "__main__":
    import sys
    learn_event_par_worker(sys.argv)
    
