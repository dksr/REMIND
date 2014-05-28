import cPickle as pickle
import sys
import time

sys.path.append('/home/csunix/visdata/cofriend/sandeep/Dropbox/code/my_code/trunk/python/')
sys.path.append('/home/csunix/visdata/cofriend/release/arc1_code/lam/lib/python2.6/site-packages')

from pyswip import Prolog
from base.ilp.logic import expr
from base.ilp.hyp_vigil import Clause
from base.ilp.get_blanket import assert_blanket_to_prolog_str_int

def query_hyp_in_event_db(hyp, event_db_file):
    prolog = Prolog()
    
    str2num_file = '/home/csunix/visdata/cofriend/sandeep/Dropbox/code/my_code/trunk/python/cofriend/str2num.pl'
    prolog.consult(str2num_file)
    
    print 'Reading event database ...'
    all_prolog_modules  = pickle.load(open(event_db_file))
    (modeh, modeb)      = all_prolog_modules['modes']
    pos_ex              = all_prolog_modules['pos_ex']
    test_pos_ex         = all_prolog_modules['test_pos_ex']
    pos_prolog_modules  = all_prolog_modules['pos']
    neg_prolog_modules  = all_prolog_modules['neg']
    test_prolog_modules = all_prolog_modules['test']        
    
    pos_event_dbs = []
    neg_event_dbs = []
    print 'Asserting pos prolog modules ...'
    for vid in pos_prolog_modules:
        for i in xrange(len(pos_prolog_modules[vid])):
            pos_prolog_module  = pos_prolog_modules[vid][i][0]
            pos_prolog_blanket = pos_prolog_modules[vid][i][1]
            pos_event_dbs.append(pos_prolog_module)
            assert_blanket_to_prolog_str_int(pos_prolog_blanket, prolog, pos_prolog_module)
            
    print 'Asserting neg prolog modules ...'            
    for vid in neg_prolog_modules:
        for i in xrange(len(neg_prolog_modules[vid])):
            neg_prolog_module  = neg_prolog_modules[vid][i][0]
            neg_prolog_blanket = neg_prolog_modules[vid][i][1]
            neg_event_dbs.append(neg_prolog_module)
            assert_blanket_to_prolog_str_int(neg_prolog_blanket, prolog, neg_prolog_module)
                
    print 'num of pos: ' + repr(len(pos_event_dbs))
    print 'num of neg: ' + repr(len(neg_event_dbs))
    print 'Querying in pos prolog modules ...'        
    t0 = time.clock()
    print time.asctime()
    for i in xrange(100000):
        pos_cover = hyp.pyswip_covers(prolog, pos_event_dbs, True, False, neg=0)
    print time.asctime()
    pos_eval_time = (time.clock() - t0)
    
    print 'Querying in neg prolog modules ...'        
    t0 = time.clock()
    print time.asctime()
    for i in xrange(100000):
        neg_cover = hyp.pyswip_covers(prolog, neg_event_dbs, True, False, neg=1)
    print time.asctime()
    neg_eval_time = (time.clock() - t0)
    print pos_eval_time
    print neg_eval_time

def query_hyp_in_video_db(hyps, video_db):
    prolog = Prolog()
    
    str2num_file = '/home/csunix/visdata/cofriend/sandeep/Dropbox/code/my_code/trunk/python/cofriend/str2num.pl'
    prolog.consult(str2num_file)
    
    print 'Asserting the database ...'
    assert_blanket_to_prolog_str_int(video_db, prolog, 'vid_db')
    result = {}        
    for event in hyps:
        result[event] = []
        print 'Querying in the video for event: ' + event
        for hyp in hyps[event]:
            pos_cover = hyp.pyswip_covers(prolog, [('vid_db',video_db)], True, False, neg=0)
            result[event].append(pos_cover)
    return result
    
def cof_test():
    #data_file = '/home/csunix/visdata/cofriend/release/thesis_data/par29_type_sfe_db_gt_noVOZ_aircraft_hv_lujoined_2/blankets/Aircraft_Arrival_n35_i150_1_all_blankets.p'
    #hyp = 'Aircraft_Arrival :- vehicle_Positioned(obj(veh(heavy_veh(aircraft(S)))),arrival_zone,int(T,U)), vehicle_Leaves_Zone(obj(veh(heavy_veh(aircraft(S)))),arrival_zone,int(V_1,V_1)), before(int(V_1,V_1),int(T,U))'
    data_file = '/home/csunix/visdata/cofriend/release/thesis_data/par29_type_sfe_db_gt_noVOZ_aircraft_hv_lujoined_2/blankets/Aircraft_Arrival_n35_i150_1_all_untype_blankets.p'
    hyp = 'Aircraft_Arrival :- vehicle_Positioned(obj(S),arrival_zone,int(T,U)), vehicle_Leaves_Zone(obj(S),arrival_zone,int(V_1,V_1)), before(int(V_1,V_1),int(T,U))'
    head = hyp.split(' :- ')[0]
    body = hyp.split(' :- ')[1]
    body = body.split(', ')
    head = expr(head)
    body = map(expr, body)
    hyp = Clause(head, body, 0)
    print hyp
    query_hyp_in_event_db(hyp, data_file)

    
if __name__ == '__main__':
    import os
    
    data_file = '/usr/not-backed-up/data_sets/Minds_Eye/mindseye_vigil/Y2/tracklets/year-two-evaluation/vigil_Y2_eval_blankets.p'
    sol_dir = '/usr/not-backed-up/data_sets/Minds_Eye/mindseye_vigil/Y2/results/oct_Y2'
    video_db = pickle.load(open(data_file))
    sol  = {}
    hyps = {}
    for i in os.listdir(sol_dir):
        if 'remote' not in i:
            continue
        for j in os.listdir(os.path.join(sol_dir, i)):
            temp_sol = pickle.load(open(os.path.join(sol_dir, i, j)))
            event = temp_sol.keys()[0]
            hyps[event] = temp_sol[event][1]['hyp']
    for vid in video_db:
        sol[vid] = query_hyp_in_video_db(hyps, video_db[vid])

print '==========================='
print 'DONE'
    