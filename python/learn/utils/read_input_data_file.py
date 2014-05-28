def get_rel_data(argv):    
    import ConfigParser
    import cPickle as pickle    
    import os
    import platform
    import re
    import sys
    import time
    from optparse import OptionParser   
    from os.path import join
    
    host = os.uname()[1].split('.')[0]
    if host == 'cslin174':
        ROOT_DIR = '/home/csunix/visdata/cofriend/sandeep/Dropbox/code/my_code/'        
    else:    
        try:
            ROOT_DIR = os.environ['LEARN_ROOT']
        except KeyError:
            ROOT_DIR = '/nobackup/scksrd/cofriend/code/vigil/'    
            
    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(ROOT_DIR + '/config.cfg')       
    MAIL_FLAG = eval(cfg_parser.get('PARAMETERS', 'mail_flag'))
    ONLY_ERROR_MAIL = eval(cfg_parser.get('PARAMETERS', 'only_error_mail'))
    release   = eval(cfg_parser.get('PARAMETERS', 'release'))        
    DEBUG = eval(cfg_parser.get('PARAMETERS', 'debug'))

    if 'WINGDB_ACTIVE' in os.environ: 
        DEBUG = True
        
    if release:
        py_version   = str(sys.version[:3])
    else:
        py_version   = cfg_parser.get('PARAMETERS', 'py_version')

    sys.path.append(join(ROOT_DIR,     'lib/python' + py_version +'/site-packages'))
 
    from base.base_constants  import RBB, GBB, YBB, BBB, RBT, CBT, YBT, MBT, GBT, \
         GT, YT, MT, RT, CT, RESET                          
    from base.ilp.logic import Expr, expr

    from base.utils.Logging                import initialize_logging            
    from learn.ilp.hyp                     import Clause, Modes
    
    if argv is None:
        argv = sys.argv[1:]

    # Setup command line options
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-i", "--infile",    dest="in_file",  default="", help="input file name")            
    parser.add_option("-d", "--dpath",     dest="out_dir",  default="", help="output directory (default '')")    
    parser.add_option("-t", "--tag",       dest="tag",      default="", help="name tag (default '')")    
    parser.add_option("-l", "--logdir",    dest="logdir",   default="/tmp", help="log DIRECTORY (default /tmp/)")
    parser.add_option("-f", "--logfile",   dest="logfile",  default="project.log", help="log FILE (default project.log)")
    parser.add_option("-v", "--loglevel",  dest="loglevel", default="debug", help="logging level (debug, info, error)")    
    parser.add_option("-m", "--module",    dest="module",   default="", help="logger name (empty for main script or root logger)")    
    parser.add_option("-q", "--quiet",     dest="quiet",    default=False, action="store_true", help="do not log to console")
    parser.add_option("-u", "--filequiet", dest="fquiet",   default=False, action="store_true", help="do not log to file")
    parser.add_option("-c", "--clean",     dest="clean",    default=False, action="store_true", help="remove old log file")
    
    # Process command line and config file options
    (options, args) = parser.parse_args(argv)
            
    # Setup logger format and output locations        
    
    log = initialize_logging(options.__dict__)
    start_time = time.asctime()
    log.info('')
    log.info("START TIME: " + BBB + start_time + RESET)
    log.info("HOST      : " + host)

    tag = options.tag
    OUT_ROOT_DIR  = options.out_dir
    
    #rel_data     = cfg_parser.get('PARAMETERS', 'rel_data')   
    #var_depth    = eval(cfg_parser.get('PARAMETERS', 'var_depth'))        
    #max_terms    = eval(cfg_parser.get('PARAMETERS', 'max_terms'))
    #sp_max_terms = eval(cfg_parser.get('PARAMETERS', 'sp_max_terms'))
    #max_bc_length    = eval(cfg_parser.get('PARAMETERS', 'max_bc_length'))
    #min_pos_examples = eval(cfg_parser.get('PARAMETERS', 'min_pos_examples'))
    #num_refine_ops   = eval(cfg_parser.get('PARAMETERS', 'num_refine_ops'))
    #temp_rel_mandatory  = eval(cfg_parser.get('PARAMETERS', 'temporal_rel_mandatory'))
    #CLASSIFICATION      = eval(cfg_parser.get('PARAMETERS', 'classification'))
    #STRATIFIED_CV       = eval(cfg_parser.get('PARAMETERS', 'stratified_cv'))
    #K                   = eval(cfg_parser.get('PARAMETERS', 'k_fold_value'))    
    #PARALLEL_EXEC       = eval(cfg_parser.get('PARAMETERS', 'parallel_exec'))
    #EVALUATION          = eval(cfg_parser.get('PARAMETERS', 'evaluation'))
    ## Should we combine the spatial and temporal terms while constructing the hyp?
    #min_score_to_expand_hyp  = eval(cfg_parser.get('PARAMETERS', 'min_score_to_expand_hyp'))
    
    #log.info("Rel_data          : " + rel_data)
    #log.info("VAR_DEPTH         : " + repr(var_depth))
    #log.info("MAX_TERMS         : " + repr(max_terms))
    #log.info("RELEASE_VERSION?  : " + repr(release))
    #log.info("MAX_SPATIAL_TERMS : " + repr(sp_max_terms))
    #log.info("MIN_POS_EXAMPLES  : " + repr(min_pos_examples))
    #log.info("NUM_REFINE_OPS    : " + repr(num_refine_ops))
    #log.info("MAX_BOTTOM_CLAUSE_LENGTH: " + repr(max_bc_length))
    #log.info("MIN_SCORE_TO_EXPAND_HYP : " + repr(min_score_to_expand_hyp))
    #log.info("COMBINE_SPATIO_TEMPORAL : " + repr(combine_spatial_temporal))
    #log.info("TEMPORAL_REL_MANDATORY  : " + repr(temp_rel_mandatory))
    #log.info("CLASSIFICATION  : "         + repr(CLASSIFICATION))
    #log.info("STRATIFIED_CV  : "          + repr(STRATIFIED_CV))
    #log.info("PARALLEL_EXEC  : "          + repr(PARALLEL_EXEC ))
    #log.info("K  : "                      + repr(K))
    #log.info("")
    
    log.info("")
    log.info(YBT + "Data PATHS:" + RESET)
    log.info("ROOT_DIR             : " + ROOT_DIR)
    log.info("OUT_ROOT_DIR         : " + OUT_ROOT_DIR)
    log.info("")
            
    input_file = open(options.in_file) 
    mode_pattern = re.compile(':- mode(\w)\((\d*), (.*)\((.*)\)\).')
    neg_ex_fact_pattern = re.compile(':-(\w*)\((.*)\).')
    fact_pattern = re.compile('(\w*)\((.*)\).')
    modeb = []
    class_predicate = None
    pos_example_flag = True
    example_data_start = False
    rel_data = {}
    rel_data['modes'] = []
    rel_data['pos'] = {}
    rel_data['neg'] = {}
    for line in input_file:
        line = line.strip()
        if line == '' or line.startswith('%'):
            continue
        log.info(line)
        if line.find(':- mode') != -1:
            (hORb, recall, predicate, mode_args) = mode_pattern.findall(line)[0]
            mode_args = mode_args.split(', ')
            expr_str = predicate + '(' + ','.join(mode_args) + ')'
            # We don't use the symbol # in python as it is used for comments
            expr_str = expr_str.replace('#', '$')
            if hORb == 'h':
                class_predicate = predicate
                modeh = [Modes(1, expr(expr_str))]
            elif hORb == 'b':
                modeb.append(Modes(1, expr(expr_str), False))
        elif class_predicate and line.find(':-') == -1 and line.find(class_predicate) != -1:    
            (predicate, pos_example_args) = fact_pattern.findall(line)[0]
            example_data_start = True
            pos_example_flag   = True
            rel_data['pos'][pos_example_args] = {}
        elif class_predicate and line.find(':-') != -1 and line.find(class_predicate) != -1:
            (predicate, neg_example_args) = fact_pattern.findall(line)[0]
            example_data_start = True
            pos_example_flag   = False
            rel_data['neg'][neg_example_args] = {}
        elif example_data_start:
            (predicate, fact_args) = fact_pattern.findall(line)[0]
            fact_args = fact_args.split(', ')
            expr_str = predicate + '(' + ','.join(fact_args) + ')'
            if pos_example_flag:
                if predicate not in rel_data['pos'][pos_example_args]:
                    rel_data['pos'][pos_example_args][predicate] = []
                rel_data['pos'][pos_example_args][predicate].append(expr(expr_str))
            else:
                if predicate not in rel_data['neg'][neg_example_args]:
                    rel_data['neg'][neg_example_args][predicate] = []
                rel_data['neg'][neg_example_args][predicate].append(expr(expr_str))
    
    input_file.close()
    rel_data['modes'] = [modeh, modeb]
    master_data_file = join(OUT_ROOT_DIR, class_predicate + '_data_' + tag + '.p')
    pickle.dump(rel_data, open(master_data_file, 'w'), 1)
    log.info('Relational data dumped in: ' + master_data_file)
    return rel_data

if __name__ == "__main__":
    argv = ['-i', '/tmp/aleph_cw/easytmp.b']
    get_rel_data(argv)