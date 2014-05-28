
event_type = {'PrimitiveState': 1,
              'PrimitiveEvent': 1,
              'CompositeState': 1,
              'CompositeEvent': 1
             }

constraints = {' before ' : 1,
               ' meet '   : 1,
               ' <= '     : 1,
               ' = '      : 1,
               ' >= '     : 1,
               ' overlap ': 1,
               ' in '     : 1,
               ' > '      : 1
              }

constraints_name_map = {'before' : 'before',
                        'meet'   : 'meet',
                        ' <= '     : 1,
                        ' = '      : 1,
                        ' >= '     : 1,
                        'overlap': 1,
                        ' in '     : 1,
                        ' > '       : 1
                       }

rel_name_map = {'before' : 'before',
                'meet'   : 'meet',
                '<='     : 'leq',
                '='      : 'eq',
                '>='     : 'geq',
                'overlap': 'overlap',
                'in'     : 'in',
                '>'       : 'greater',
                '<'       : 'less',                
                }

discard = ['Alarm']

class EventDef():
   
    def __init__(self, model_str):
        from pyparsing import nestedExpr, stringEnd
        
        self.event_name = ''
        self.PO   = {}
        self.components  = {}
        self.components_str = ''
        self.constraints = []
        self.constraints_str = ''    
        self.event_type  = ''
        self.model_str   = model_str
        self.head = ''
        self.body = ''
        
        name_ind = 0
        po_ind   = 2
        components_ind  = 3
        constraints_ind = 5
        
        # Find event type
        temp_ind = self.model_str.find('(')
        self.event_type = self.model_str[:temp_ind]
        # Remove it from the model string to make it parsable by nested parser
        self.model_str  = self.model_str.replace(self.event_type, '')
        nestedItems = nestedExpr("(", ")")
        res = (nestedItems+stringEnd).parseString(self.model_str).asList()
        
        # Get event name. Remove the ',' at the end
        self.event_name = res[0][name_ind][:-1]
        self.head       = res[0][name_ind][:-1]
        
        # [['v1', ':', 'Vehicle'], ',', ['v2', ':', 'Vehicle'], ',', ['z1', ':', 'Zone']]        
        for po in res[0][po_ind]:
            if type(po) is list:
                self.PO.update({po[0]:po[2]})
        #print self.PO        
        #print res
        # [['c1', ':', 'CompositeEvent', 'FWD_LD_Positioning', ['v1,', 'z1']], 
        #  ['c2', ':', 'CompositeEvent', 'FWD_TS_Positioning', ['v2,', 'z2']]
        # ]
        #print res[0][components_ind]        
        for comp in res[0][components_ind + 1]:
            c_id   = comp[0]
            c_type = comp[2]
            c_name = comp[3]
            c_veh  = comp[4]
            #c_vehicles = []
            #for veh in c_veh:
                #if veh.endswith(','):
                    #c_vehicles.append(veh[:-1])
                #else:
                    #c_vehicles.append(veh)                        
            #self.components[c_id] = [c_name, c_vehicles]
            self.components[c_id] = [c_name, c_veh]
            self.components_str += c_name + '('
            # Remove and ',' in vehicle names, lower the case of vehicle types (constants) 
            # and upper the case of vehicles (variables)
            for veh in c_veh:
                self.components_str += self.PO[veh.strip(',')].lower() + '(' + veh.strip(',').upper() + '),'
            self.components_str += c_id
            self.components_str += '), '    
                
        if res[0][constraints_ind] == 'Constraints':
            # [['c1->Interval', 'before', 'c2->Interval']]
            if len(res[0][constraints_ind + 1]) != 0:
                for constraint in res[0][constraints_ind + 1]:
                    # ['duration', ['c1'], '>=', '3']
                    if type(constraint[1]) is not list and constraint[1] in rel_name_map:
                        rel  = rel_name_map[constraint[1]]
                        arg1 = constraint[0]
                        arg2 = constraint[2]
                    elif constraint[2] in rel_name_map:
                        rel  = rel_name_map[constraint[2]]
                        arg1 = constraint[0] + '(' + constraint[1][0] + ')' 
                        arg2 = constraint[3]
                        
                    if '->' in arg1:
                        arg1 = arg1.replace('->', ':')
                        # If constraint is on type of obj, then change the constraint to 
                        # valid prolog expression. i.e. 'z1->Name' to type(Z1)
                        if arg1.split(':')[1] == 'Name' or arg1.split(':')[1] == 'SubType':
                            if arg1.split(':')[0] in self.PO:
                                arg1 = 'type(' + arg1.split(':')[0].upper() + ')'
                            else: 
                                arg1 = 'type(' + arg1.split(':')[0] + ')'
                    if '->' in arg2:
                        arg2 = arg2.replace('->', ':')
                        if arg2.split(':')[1] == 'Name' or arg2.split(':')[1] == 'SubType':
                            if arg2.split(':')[0] in self.PO:
                                arg2 = 'type(' + arg2.split(':')[0].upper() + ')'
                            else: 
                                arg2 = 'type(' + arg2.split(':')[0] + ')'
                    self.constraints_str += rel + '(' + arg1 + ',' + arg2 + '), '
                    self.constraints.append((rel, arg1, arg2))
                # Remove the final ','    
                self.constraints_str = self.constraints_str.strip(', ')
                self.constraints_str += '.'
                
        if self.constraints_str == '':
            self.components_str = self.components_str.strip(', ')
            self.constraints_str = '.'
            
        self.body = self.components_str + self.constraints_str        
     
    def __str__(self):
        return self.head + ' :- ' + self.body
    
    
if __name__ == "__main__":
    
    data = """
    (FWD_CN_LoadingUnloading_Operation_Starts,
        PhysicalObjects( (v1 : Vehicle), (v2 : Vehicle), (z1 : Zone), (z2 : Zone) )
        Components( (c1 : CompositeEvent FWD_LD_Positioning(v1, z1))
                                (c2 : CompositeEvent FWD_TS_Positioning(v2, z2)) )
        Constraints( (c1->Interval before c2->Interval) )
        Alarm ((Level : VERYURGENT))
    )
    """
    
    data2 = """
    (Departure_Starts,
         PhysicalObjects( (v1 : Vehicle), (z1 : Zone) )
         Components( (c1 : CompositeEvent PB_Positioning(v1, z1)) )
         Alarm ((Level : NOTURGENT))
    )
    """
    
    data3 = """
    (Right_AFT_Catering,
        PhysicalObjects( (v1 : Vehicle), (z1 : Zone) )
        Components( (c1 : CompositeState Right_AFT_CT_Positioned(v1, z1)) )
        Constraints()
        Alarm ((Level : VERYURGENT))
    )
    """
    
    data4 = """
    (PBB_Positioning,
        PhysicalObjects( (v1 : Vehicle), (z1 : Zone) )
        Components( (c1 : PrimitiveState Vehicle_Inside_Zone(v1, z1)) )
        Constraints( (z1->Name = Jet_Bridge_Evolution) 
        (v1->SubType = PASSENGER_BOARDING_BRIDGE) 
        (duration(c1) >= 3)
    )
    Alarm ((Level : VERYURGENT))
    )
    """
    
    model_dir = '/home/csunix/visdata/cofriend/data/SED-config-INRIA-v161210/scenarios/'
    out_model_dir = '/home/csunix/visdata/cofriend/data/SED-config-INRIA-v161210/scenarios/pl_out/'
    file_list = [('sr.scenario.cofriend.Arrival.model', 'sr.scenario.cofriend.Arrival.model.pl'),
                 ('sr.scenario.cofriend.Catering.model', 'sr.scenario.cofriend.Catering.model.pl'),
                 ('sr.scenario.cofriend.Departure.model', 'sr.scenario.cofriend.Departure.model.pl'),
                 ('sr.scenario.cofriend.LoadingUnloading.model', 'sr.scenario.cofriend.LoadingUnloading.model.pl'),
                 ('sr.scenario.cofriend.Positioned.model', 'sr.scenario.cofriend.Positioned.model.pl'),
                 ('sr.scenario.cofriend.Positioning.model', 'sr.scenario.cofriend.Positioning.model.pl'),
                 ('sr.scenario.cofriend.Refuelling.model', 'sr.scenario.cofriend.Refuelling.model.pl'),
                 ('sr.scenario.cofriend.Removing.model', 'sr.scenario.cofriend.Removing.model.pl')
                ]
    mstr = ''
    for (ifile, ofile) in file_list:
        print model_dir + ifile
        i_mfile = open(model_dir + ifile)        
        o_mfile = open(out_model_dir + ofile, 'w')        
        for line in i_mfile:
            if 'CompositeEvent(' in line:
                mstr = line.replace('CompositeEvent','')
            elif 'CompositeState(' in line:
                mstr = line.replace('CompositeState','')
            elif line == ')\n':
                mstr += line
                # There might be missing closing brackets
                if mstr.count('(') != mstr.count(')'):
                    continue
                print mstr
                model = EventDef(mstr)
                o_mfile.write(model.__str__() + '\n' + '\n')
                print model
            elif line == '}\n':  
                mstr = ''
                break
            else:
                mstr += line 

