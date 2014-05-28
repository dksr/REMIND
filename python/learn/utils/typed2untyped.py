import cPickle as pickle
import copy
import sys 
sys.path.append('/home/csunix/visdata/cofriend/sandeep/Dropbox/code/my_code/trunk/python/')

def type2untypevid(rel_data_file):

    rel_data = pickle.load(open(rel_data_file))
    
    untype_rel_data = {}
    
    for vid in rel_data:
        print vid
        untype_rel_data[vid] = []
        untype_rel_data[vid].append({})
        untype_rel_data[vid].append(rel_data[vid][1])
        for rel in rel_data[vid][0]:
            untype_rel_data[vid][0][rel] = []
            for fact in rel_data[vid][0][rel]:
                new_fact = copy.deepcopy(fact)
                for arg in new_fact.args:
                    if len(arg.args) == 0:
                        continue
                    elif arg.op == 'int':
                        continue
                    else:
                        arg.op = 'obj'
                untype_rel_data[vid][0][rel].append(new_fact)
                
    pickle.dump(untype_rel_data,open('/home/csunix/visdata/cofriend/release/thesis_data/relational_ped_data_untype_correct_aircraft_hv_20110301_n35_i150.p','w'))          
    print 'done'            


def type2untypeblankets(blankets_data_file):

    rel_data = pickle.load(open(blankets_data_file))
    
    untype_rel_data = {}
    
    for data_type in rel_data:        
        print data_type
        if data_type == 'modes' or data_type == 'test_pos_ex' or data_type == 'pos_ex':
            untype_rel_data[data_type] = copy.deepcopy(rel_data[data_type])
            continue
        else:
            untype_rel_data[data_type] = {}
            for vid in rel_data[data_type]:
                untype_rel_data[data_type][vid] = []
                if data_type == 'test':
                    untype_rel_data[data_type][vid].append(rel_data[data_type][vid][0])
                    untype_rel_data[data_type][vid].append({})
                    
                    for rel in rel_data[data_type][vid][1]:
                        untype_rel_data[data_type][vid][1][rel] = []
                        for fact in rel_data[data_type][vid][1][rel]:
                            new_fact = copy.deepcopy(fact)
                            if rel != 'start_end':
                                if len(new_fact.args) == 1:
                                    new_fact.op = 'obj'
                                elif len(new_fact.args) > 2:  
                                    for arg in new_fact.args:
                                        if len(arg.args) == 0:
                                            continue
                                        elif arg.op == 'int':
                                            continue
                                        else:
                                            arg.op = 'obj'
                            untype_rel_data[data_type][vid][1][rel].append(new_fact)
                            
                elif data_type == 'pos' or data_type == 'neg':
                    for i, ex in enumerate(rel_data[data_type][vid]):
                        new_ex = []
                        new_ex.append(ex[0])
                        new_ex.append({})
                        for rel in ex[1]:
                            print rel
                            print i
                            if rel == 'start_end' or rel == 'dint' or rel == 'zone':
                                new_ex[1][rel] = ex[1][rel]  
                                continue
                            new_ex[1][rel] = []
                            for fact in ex[1][rel]:
                                new_fact = copy.deepcopy(fact)
                                if len(new_fact.args) == 1:
                                    new_fact.op = 'obj'
                                elif len(new_fact.args) > 2:    
                                    for arg in new_fact.args:
                                        if len(arg.args) == 0:
                                            continue
                                        elif arg.op == 'int':
                                            continue
                                        else:
                                            arg.op = 'obj'
                                new_ex[1][rel].append(new_fact)
                        untype_rel_data[data_type][vid].append(new_ex)
                         
    pickle.dump(untype_rel_data,open('/home/csunix/visdata/cofriend/release/thesis_data/par29_type_sfe_db_gt_noVOZ_aircraft_hv_lujoined_2/blankets/Aircraft_Arrival_n35_i150_1_all_untype_blankets.p','w'))          
    print 'done'            

if __name__ == '__main__':
    data_file = '/home/csunix/visdata/cofriend/release/thesis_data/par29_type_sfe_db_gt_noVOZ_aircraft_hv_lujoined_2/blankets/Aircraft_Arrival_n35_i150_1_all_blankets.p'
    type2untypeblankets(data_file)