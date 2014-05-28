import logging
#log = logging.getLogger("lam.cofriend.utils.read_from_pgsql")
log = logging.getLogger("")    

def get_track_data_from_pgsql_bak(pic_data_dir):
    import ConfigParser
    import logging
    import os
    import pg as pgsql
    import sys
    import cPickle as pickle
    
    py_version = str(sys.version[:3])
    if os.environ['COF_LEARN_ROOT']:
        ROOT_DIR = os.environ['COF_LEARN_ROOT']        
    else:
        ROOT_DIR = '/home/csunix/visdata/cofriend/data/'     

    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(ROOT_DIR + '/config.cfg')  

    log = logging.getLogger("cofriend.utils.read_from_pgsql")
    
    dbase_name = cfg_parser.get('PGSQL', 'database')
    host_name  = cfg_parser.get('PGSQL', 'host')
    port_num   = eval(cfg_parser.get('PGSQL', 'port'))
    password   = cfg_parser.get('PGSQL', 'passwd')

    #temp = pickle.load(open(pic_data_dir))
    #return temp[vid]
    
    try:    
        connection = pgsql.connect(dbname=dbase_name, host=host_name, port=port_num, passwd=password)
        log.info('Connection to database established')
    except Exception:
        #log.critical('Could not connect to psql. Is the server running? Also check input parameter in config file.')
        log.info('Could not connect to psql. Is the server running? Also check db input parameters in config file in main dir.')
    
    #db.query(c_S_MobFrame)
    #print 'created mob frame table'
    #db.query(c_S_Mobile)
    #print 'created mobile table'
    #db.query(c_Parent_Mobile)
    #print 'created parent mobile table'
    #db.query(c_Info_2D)
    #print 'created Info2D table'
    #db.query(c_fki)
    #print 'created fki index table'
    #db.query(c_MobProperties)
    #print 'created MobProperties table'
    
    # Structure of record read from xml
    # record = [mID, xM3D, yM3D, zM3D, w3D, h3D, l3D, obj_type, ornt, speed]        
            
    camID = 5 
    pickled_db_data  = {}
    #q_get_frames = 'SELECT "frameKey", "frameID" FROM "S_MobFrame" WHERE "camID" = %s'
    q_get_frames = 'SELECT "frameKey", "frameID", "time" FROM "S_MobFrame"'
    #log.info('Read data from S_MobFrame table')
    #frames_result = connection.query(q_get_frames % repr(camID)).getresult()    
    frames_result = connection.query(q_get_frames).getresult()    
    
    start_time_vid_map = {'2008-11-03 16':    'COF-1',
                         '2008-11-03 17':     'COF-2',
                         '2008-11-04 07':     'COF-3',
                         '2008-11-04 16':     'COF-4',
                         '2008-11-04 17':     'COF-5',
                         '2008-11-04 18':     'COF-6',
                         '2008-11-06 15':     'COF-7',
                         '2008-11-11 15':     'COF-8',
                         '2008-11-10 16':     'COF-9',
                         '2008-11-07 12':     'COF-10',
	                 '2008-11-21 16':     'COF-11-calib',
	                 '2008-11-19 16':     'COF-12-calib',
	                 '2008-12-26 08':     'COF-13',
                         '2008-12-26 11':     'COF-14',
                         '2009-01-21 11':     'COF-15',
                         '2009-02-02 16':     'COF-16',
                         '2009-02-01 14':     'COF-17',
                         '2009-02-03 09':     'COF-18',
                         '2009-02-04 08':     'COF-19-calib',
                         '2009-02-18 13':     'COF-20',
                         '2009-03-06 13':     'COF-21',
                         '2009-03-09 16':     'COF-22',
                         '2009-03-12 16':     'COF-23-calib',
                         '2009-03-11 08':     'COF-25',
                         '2009-03-19 16':     'COF-26',
                         '2009-03-19 16':     'COF-27',
                         '2009-03-29 15':     'COF-28',
                         '2009-04-04 17':     'COF-29',
                         '2009-04-10 18':     'COF-30',
                         '2009-03-27 15':     'COF-31',
                         '2009-04-15 11':     'COF-32',
                         '2009-04-15 17':     'COF-33',
                         '2009-04-13 10':     'COF-34',
                         '2009-04-08 11':     'COF-35',
                         '2009-04-19 12':     'COF-36',
                         '2009-05-01 11':     'COF-41',
                         '2009-05-22 11':     'COF-47',
                         '2009-05-17 11':     'COF-48',
                         '2009-05-26 14':     'COF-49',
                         '2009-05-20 09':     'COF-50',
                         '2009-05-26 14':     'COF-51',
                         '2009-05-25 15':     'COF-52',
                         '2009-12-09 08':     'COF-58',
                         '2009-12-09 16':     'COF-59',
                         '2009-12-16 11':     'COF-61',
                         '2009-12-13 15':     'COF-62',
                         '2009-12-22 09':     'COF-63',
                         '2009-12-22 15':     'COF-64',
                         '2009-12-23 09':     'COF-65',
                         '2009-12-23 14':     'COF-66',
                         '2009-12-24 09':     'COF-67',
                         '2009-12-24 10':     'COF-68'
                         }
    
    q_get_mobiles = 'SELECT * FROM "S_Mobile" WHERE "frameKey" = %s'
    prev_frame = 1000
    start = False
    log.info('Reading data from db ...')
    for fKey, fID, time in frames_result:
        if fID < prev_frame:
            if start:
                log.info('dumped ' + repr(vid) + ' data')
                pickle_file = os.path.join(pic_data_dir, 'pickled_db_data_' + repr(vid) + '.p')
                pickle.dump(pickled_db_data, open(pickle_file, 'w'), 1)
            start = True    
            new_start_time_stamp = time.split(':')[0]
            vid = eval(start_time_vid_map[new_start_time_stamp].split('-')[1])
            #pickled_db_data      = {}
            pickled_db_data[vid] = {}
        mob_result = connection.query(q_get_mobiles % repr(fKey)).getresult()
        pickled_db_data[vid][fID] = []
        for record in mob_result:
            mID         = record[0]
            obj_type    = record[1]
            obj_subtype = record[2]
            conf        = record[3]
            xM3D        = record[4]
            yM3D        = record[5]
            zM3D        = record[6]
            w3D         = record[7]
            h3D         = record[8]
            l3D         = record[9]
            #ornt        = record[19]
            #mob_key     = record[21]
            #xSpeed      = record[22]
            #ySpeed      = record[23]
            
            fields = (mID, xM3D, yM3D, zM3D, w3D, h3D, l3D, obj_subtype) #, obj_type, ornt, xSpeed, ySpeed)
            pickled_db_data[vid][fID].append(fields)
        print 'Reading data for frameKey: ' + repr(fKey)
        log.debug('Reading data for frameKey: ' + repr(fKey))
        prev_frame = fID

    #print 'dumped ' + vid + ' data'
    pickle_file = os.path.join(pic_data_dir, 'pickled_db_track_data.p')
    pickle.dump(pickled_db_data, open(pickle_file, 'w'), 1)
    
    log.info('Read complete data from S_Mobile')
    connection.close()
    log.info('Database connection closed')
    return pickled_db_data

def get_track_data_from_pgsql(videos, pickle_file, host_name=None):
    import ConfigParser
    from datetime import datetime
    import logging
    import os
    import pg as pgsql
    import sys
    import cPickle as pickle
    
    py_version = str(sys.version[:3])
    if os.environ['COF_LEARN_ROOT']:
        ROOT_DIR = os.environ['COF_LEARN_ROOT']        
    else:
        ROOT_DIR = '/home/csunix/visdata/cofriend/data/'     

    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(ROOT_DIR + '/config.cfg')  

    log = logging.getLogger("cofriend.utils.read_from_pgsql")
    
    dbase_name = cfg_parser.get('PGSQL', 'database')
    if host_name == None:
        host_name  = cfg_parser.get('PGSQL', 'host')
    port_num   = eval(cfg_parser.get('PGSQL', 'port'))
    password   = cfg_parser.get('PGSQL', 'passwd')

    #temp = pickle.load(open(pic_data_dir))
    #return temp[vid]
    
    try:    
        connection = pgsql.connect(dbname=dbase_name, host=host_name, port=port_num, passwd=password)
        log.info('Connection to database established')
    except Exception:
        print 'Could not connect to psql. Is the server running? Also check db input parameters in config file in main dir.'
        #log.critical('Could not connect to psql. Is the server running? Also check input parameter in config file.')
        log.info('Could not connect to psql. Is the server running? Also check db input parameters in config file in main dir.')
    
    q_turnover_data = 'SELECT * FROM "S_Turnover"'
    turnover_data = connection.query(q_turnover_data).getresult()
    turnover_mobframe_data = {}
    
    camID = 5 
    pickled_db_data  = {}
    
    # template query to get mobile data
    q_get_mobiles = 'SELECT * FROM "S_Mobile" WHERE "frameKey" = %s'
    
    for i in turnover_data:
        # i = [turnoverKey, turnoverID, startTime, endTime]
        # turnover id is of from 'cof008'. Only get id number    
        turnover_id = int(i[1][3:])
        if turnover_id not in videos:
            continue
        vid = turnover_id
        pickled_db_data[vid] = {}
     
        print 'Processing turnover ' + repr(turnover_id) + ' for 3D data'
    
        # Ignore milliseconds
        startTime = datetime.strptime(i[2].split('.')[0],"%Y-%m-%d %H:%M:%S")
        endTime   = datetime.strptime(i[3].split('.')[0],"%Y-%m-%d %H:%M:%S")
        # Get data that has startTime and endTime within the limits
        get_data_query = 'SELECT "frameKey", "frameID", "time" FROM "S_MobFrame" WHERE ' \
                         '"time" > \'%(stt)s\' AND "time" < \'%(ndt)s\'' \
                         % {'stt':startTime.isoformat(),'ndt':endTime.isoformat()}
        frames_result = connection.query(get_data_query).getresult()
        
        for fKey, fID, time in frames_result:
            mob_result = connection.query(q_get_mobiles % repr(fKey)).getresult()
            pickled_db_data[vid][fID] = []
            # Structure of record read from xml
            # record = [mID, xM3D, yM3D, zM3D, w3D, h3D, l3D, obj_type, ornt, speed]        

            for record in mob_result:
                mID         = record[0]
                obj_type    = record[1]
                obj_subtype = record[2]
                conf        = record[3]
                xM3D        = record[4]
                yM3D        = record[5]
                zM3D        = record[6]
                w3D         = record[7]
                h3D         = record[8]
                l3D         = record[9]
                ornt        = record[19]
                #mob_key     = record[21]
                xSpeed      = record[22]
                ySpeed      = record[23]

                fields = (mID, xM3D, yM3D, zM3D, w3D, h3D, l3D, obj_subtype, obj_type, ornt, xSpeed, ySpeed)
                pickled_db_data[vid][fID].append(fields)

        print 'Done with ' + repr(vid) + ' data'
    pickle.dump(pickled_db_data, open(pickle_file, 'w'), 1)
    
    log.info('Read complete data from S_Mobile')
    connection.close()
    log.info('Database connection closed')
    return pickled_db_data
    
def get_2D_data_from_pgsql(videos, camID):
    import copy
    import ConfigParser
    from datetime import datetime
    import logging
    import os
    import pg as pgsql
    import sys
    
    py_version = str(sys.version[:3])
    if os.environ['COF_LEARN_ROOT']:
        ROOT_DIR = os.environ['COF_LEARN_ROOT']        
    else:
        ROOT_DIR = '/home/csunix/scksrd/work/cof_learn'     

    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(ROOT_DIR + '/config.cfg')  

    log = logging.getLogger("cofriend.utils.read_from_pgsql")
    
    dbase_name = cfg_parser.get('PGSQL', 'database')
    host_name  = cfg_parser.get('PGSQL', 'host')
    port_num   = eval(cfg_parser.get('PGSQL', 'port'))
    password   = cfg_parser.get('PGSQL', 'passwd')

    try:    
        connection = pgsql.connect(dbname=dbase_name, host=host_name, port=port_num, passwd=password)
        #log.info('Connection established to database')
        print 'Connection established'
    except Exception:
        #log.critical('Could not connect to psql. Is the server running? Also check input parameters in config file.')
        print 'Could not connect to psql. Is the server running? Also check input parameters in config file.'
        
    pickled_2D_data  = {}
    q_turnover_data = 'SELECT * FROM "S_Turnover"'
    turnover_data = connection.query(q_turnover_data).getresult()
    turnover_mobframe_data = {}
    for i in turnover_data:
        # i = [turnoverKey, turnoverID, startTime, endTime]
        # turnover id is of from 'cof008'. Only get id number        
        turnover_id = int(i[1][3:])
        if turnover_id not in videos:
            continue
        print 'Processing turnover ' + repr(turnover_id) + ' for 2D data'
    
        # Ignore milliseconds
        startTime = datetime.strptime(i[2].split('.')[0],"%Y-%m-%d %H:%M:%S")
        endTime   = datetime.strptime(i[3].split('.')[0],"%Y-%m-%d %H:%M:%S")
        # Get data that has startTime and endTime within the limits
        get_data_query = 'SELECT "frameKey", "frameID", "time" FROM "S_MobFrame" WHERE ' \
                         '"time" > \'%(stt)s\' AND "time" < \'%(ndt)s\'' \
                         % {'stt':startTime.isoformat(),'ndt':endTime.isoformat()}
        turnover_mobframe_data[turnover_id] = connection.query(get_data_query).getresult()

        data_2D = {}
        for ind in xrange(len(turnover_mobframe_data[turnover_id])):
            frame_key  = turnover_mobframe_data[turnover_id][ind][0]
            q_mob_data = 'SELECT "mobileID", "type", "subtype", "x", "y", "z", "w3d", "h3d", "l3d", ' \
                         '"orientation", "mobileKey", "time", "frameKey" FROM "S_Mobile" ' \
                         'WHERE "frameKey" = %d' % frame_key
            mob_data = map(list, connection.query(q_mob_data).getresult())
            for i in xrange(len(mob_data)):
                # Get the 2D data
                mobileKey = mob_data[i][10]
                #q_2D_data = 'SELECT "frameID", "xCenter", "yCenter", "width", "length", "camID", "mobileKey" '\
                            #'FROM "S_Info2D" WHERE "mobileKey" = %d AND "camID" = %s' % (mobileKey, camID)
                q_2D_data = 'SELECT "frameID", "xCenter", "yCenter", "width", "length", "camID", "mobileKey" '\
                            'FROM "S_Info2D" WHERE "mobileKey" = %d' % (mobileKey)
                result = connection.query(q_2D_data).getresult()
                for j in result:
                    if j[5] == camID:
                        print j[0]
                        # append frameID and remaining data from S_Mobile
                        # [mID, type, stype, xC, yC, w, l]
                        try:
                            data_2D[j[0]].append(mob_data[i][:3] + list(j[1:5]))
                        except KeyError:
                            data_2D[j[0]] = [mob_data[i][:3] + list(j[1:5])]
                        break
                    
                        #data_2D.append([j[0]] + mob_data[i][:3] + list(j[1:5]))
                        #break
        
        pickled_2D_data[turnover_id] = copy.deepcopy(data_2D)
    connection.close()
    return pickled_2D_data

def get_3D_data_from_pgsql(videos, camID):
    import ConfigParser
    import copy
    from datetime import datetime
    import logging
    import os
    import pg as pgsql
    import sys
    
    py_version = str(sys.version[:3])
    if os.environ['COF_LEARN_ROOT']:
        ROOT_DIR = os.environ['COF_LEARN_ROOT']        
    else:
        ROOT_DIR = '/home/csunix/scksrd/work/cof_learn'     

    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(ROOT_DIR + '/config.cfg')  

    log = logging.getLogger("cofriend.utils.read_from_pgsql")
    
    dbase_name = cfg_parser.get('PGSQL', 'database')
    host_name  = cfg_parser.get('PGSQL', 'host')
    port_num   = eval(cfg_parser.get('PGSQL', 'port'))
    password   = cfg_parser.get('PGSQL', 'passwd')

    try:    
        connection = pgsql.connect(dbname=dbase_name, host=host_name, port=port_num, passwd=password)
        #log.info('Connection established to database')
        print 'Connection established'
    except Exception:
        #log.critical('Could not connect to psql. Is the server running? Also check input parameters in config file.')
        print 'Could not connect to psql. Is the server running? Also check input parameters in config file.'
        
    pickled_3D_data  = {}
    q_turnover_data = 'SELECT * FROM "S_Turnover"'
    turnover_data = connection.query(q_turnover_data).getresult()
    turnover_mobframe_data = {}
    for i in turnover_data:
        turnover_id = int(i[1][3:])
        if turnover_id not in videos:
            continue
        print 'Processing turnover ' + repr(turnover_id) + ' for 3D data'
    
        # Ignore milliseconds
        startTime = datetime.strptime(i[2].split('.')[0],"%Y-%m-%d %H:%M:%S")
        endTime   = datetime.strptime(i[3].split('.')[0],"%Y-%m-%d %H:%M:%S")
        
        #if turnover_id in [29, 58, 59, 61, 63]:
            ## This is a temporary fix
            #sy = repr(startTime.year)
            #sm = repr(startTime.month)
            #sd = repr(startTime.day)
            #sh = repr(startTime.hour + 1)
            #smin = repr(startTime.minute)
            #ss = repr(startTime.second)
    
            #ey = repr(endTime.year)
            #em = repr(endTime.month)
            #ed = repr(endTime.day)
            #eh = repr(endTime.hour + 1)
            #emin = repr(endTime.minute)
            #es = repr(endTime.second)
    
            #startTime = datetime.strptime(sy + '-' + sm + '-' + sd + ' ' + sh + ':' + smin + ':' + ss, "%Y-%m-%d %H:%M:%S")
            #endTime   = datetime.strptime(ey + '-' + em + '-' + ed + ' ' + eh + ':' + emin + ':' + es, "%Y-%m-%d %H:%M:%S")
        
        # Get data that has startTime and endTime within the limits
        get_data_query = 'SELECT "frameKey", "frameID", "time" FROM "S_MobFrame" WHERE ' \
                         '"time" > \'%(stt)s\' AND "time" < \'%(ndt)s\'' \
                         % {'stt':startTime.isoformat(),'ndt':endTime.isoformat()}
        turnover_mobframe_data[turnover_id] = connection.query(get_data_query).getresult()

        pickled_3D_data[turnover_id] = {}
        for ind in xrange(len(turnover_mobframe_data[turnover_id])):
            frame_key  = turnover_mobframe_data[turnover_id][ind][0]
            q_mob_data = 'SELECT "mobileID", "x", "y", "z", "w3d", "h3d", "l3d", ' \
                         '"orientation", "type", "subtype", "mobileKey", "time", "frameKey" FROM "S_Mobile" ' \
                         'WHERE "frameKey" = %d' % frame_key
            mob_data = map(list, connection.query(q_mob_data).getresult())
            for i in xrange(len(mob_data)):
                # Get the 2D data to get frame number for jpeg images.
                mobileKey = mob_data[i][10]
                #q_2D_data = 'SELECT "frameID", "xCenter", "yCenter", "width", "length", "camID", "mobileKey" '\
                            #'FROM "S_Info2D" WHERE "mobileKey" = %d AND "camID" = %s' % (mobileKey, camID)
                q_2D_data = 'SELECT "frameID", "xCenter", "yCenter", "width", "length", "camID", "mobileKey" '\
                            'FROM "S_Info2D" WHERE "mobileKey" = %d' % (mobileKey)
                result = connection.query(q_2D_data).getresult()
                for j in result:
                    if j[5] == camID:
                        # append frameID and remaining data from S_Mobile
                        try:
                            pickled_3D_data[turnover_id][j[0]].append(mob_data[i])
                        except KeyError:
                            pickled_3D_data[turnover_id][j[0]] = [mob_data[i]]
                        break
    
    connection.close()
    return pickled_3D_data

def get_SED_recognitions_from_pgsql(videos):
    import ConfigParser
    from datetime import datetime
    import os
    import pg as pgsql
    import sys
    
    from base.base_constants import GBT, RBB, YBT, RESET
    
    py_version = str(sys.version[:3])
    if os.environ['COF_LEARN_ROOT']:
        ROOT_DIR = os.environ['COF_LEARN_ROOT']        
    else:
        ROOT_DIR = '/home/csunix/visdata/cofriend/data/'     

    cfg_parser = ConfigParser.ConfigParser()
    print ROOT_DIR
    cfg_parser.read(ROOT_DIR + '/config.cfg')  

    dbase_name = cfg_parser.get('PGSQL', 'database')
    host_name  = cfg_parser.get('PGSQL', 'host')
    port_num   = eval(cfg_parser.get('PGSQL', 'port'))
    password   = cfg_parser.get('PGSQL', 'passwd')
    camID      = cfg_parser.get('PARAMETERS', 'camID')
    
    try:    
        connection = pgsql.connect(dbname=dbase_name, host=host_name, port=port_num, passwd=password)   
        log.info(GBT + 'Database connection established' + RESET)
    except Exception:
        import traceback
        err_msg = traceback.format_exc(sys.exc_info())      
        log.error(RBB + err_msg + RESET)
        sys.exit(0)
        
    primitive_events = {"Person_Outside_Zone":  1,
                        "Person_Enters_Zone":  1,
                        "Person_Inside_Zone" :  1,
                        "Vehicle_Inside_Zone":  1, 
                        "Vehicle_Outside_Zone": 1,
                        "Vehicle_Positioned"  : 1,
                        "Vehicle_Stopped"     : 1,
                        "Vehicle_Enters_Zone" : 1,
                        "Vehicle_Leaves_Zone" : 1,
                        "Vehicle_Stopped_Inside_Zone" :1,
                        "Vehicle_Positioning" : 1,
                        }
    
    sed_recognitions_data  = {}
    q_turnover_data = 'SELECT * FROM "S_Turnover"'
    turnover_data = connection.query(q_turnover_data).getresult()
    turnover_sed_recognized_data = {}
    for i in turnover_data:
        turnover_id = i[1]
        int_key = int(turnover_id[-3:])
        if int_key not in videos:
            print repr(int_key) + ' not in vids'
            # Skip processing video if it is not in the considered videos
            continue
        
        log.info('Processing ' + YBT + turnover_id + RESET)    
        # Ignore milliseconds
        startTime = datetime.strptime(i[2].split('.')[0],"%Y-%m-%d %H:%M:%S")
        endTime   = datetime.strptime(i[3].split('.')[0],"%Y-%m-%d %H:%M:%S")
    
        get_data_query = 'SELECT "activityKey", "activityID", "startTime", "endTime", "startFrameID", ' \
                         '"endFrameID", "frameKey", "name", "activityAText" FROM "S_Activity" WHERE ' \
                         '"startTime" > \'%(stt)s\' AND "endTime" < \'%(ndt)s\'' \
                         % {'stt':startTime.isoformat(),'ndt':endTime.isoformat()}
        # Result is list of tuples. Convert it to list of lists because we have to add few more fields
        turnover_ped_data = map(list, connection.query(get_data_query).getresult())
        print repr(len(turnover_ped_data)) + '  ' + repr(int_key)
        
        turnover_sed_recognized_data[int_key] = []
        for ind in xrange(len(turnover_ped_data)):
            record = turnover_ped_data[ind]
            activity_name = record[7]
            if activity_name not in primitive_events:
                turnover_sed_recognized_data[int_key].append(record)
    return turnover_sed_recognized_data           

def get_SED_recognitions_timestamps_from_pgsql(videos):
    import ConfigParser
    from datetime import datetime
    import os
    import pg as pgsql
    import sys
    
    from base.base_constants import GBT, RBB, YBT, RESET
    
    py_version = str(sys.version[:3])
    if os.environ['COF_LEARN_ROOT']:
        ROOT_DIR = os.environ['COF_LEARN_ROOT']        
    else:
        ROOT_DIR = '/home/csunix/visdata/cofriend/data/'     

    cfg_parser = ConfigParser.ConfigParser()
    print ROOT_DIR
    cfg_parser.read(ROOT_DIR + '/config.cfg')  

    dbase_name = cfg_parser.get('PGSQL', 'database')
    host_name  = cfg_parser.get('PGSQL', 'host')
    port_num   = eval(cfg_parser.get('PGSQL', 'port'))
    password   = cfg_parser.get('PGSQL', 'passwd')
    camID      = cfg_parser.get('PARAMETERS', 'camID')
    
    try:    
        connection = pgsql.connect(dbname=dbase_name, host=host_name, port=port_num, passwd=password)   
        log.info(GBT + 'Database connection established' + RESET)
    except Exception:
        import traceback
        err_msg = traceback.format_exc(sys.exc_info())      
        log.error(RBB + err_msg + RESET)
        sys.exit(0)
    
    event_names = {'AFT_Bulk_LoadingUnloading_Operation': 1, 
                   'AFT_CN_LoadingUnloading_Operation': 1, 
                   'FWD_CN_LoadingUnloading_Operation': 1, 
                   'FWD_Bulk_LoadingUnloading_Operation': 1, 
                   'Left_Refuelling': 1, 
                   'GPU_Positioning': 1, 
                   'GPU_Removing': 1, 
                   'PB_Positioning': 1, 
                   'Catering': 1, 
                   'Aircraft_Arrival': 1, 
                   'Aircraft_Positioned': 1, 
                   'Aircraft_Departure': 1, 
                   'PBB_Positioning': 1,
                   'PBB_Removing': 1, 
                  }
        
    primitive_events = {"Person_Outside_Zone":  1,
                        "Person_Enters_Zone":  1,
                        "Person_Inside_Zone" :  1,
                        "Vehicle_Inside_Zone":  1, 
                        "Vehicle_Outside_Zone": 1,
                        "Vehicle_Positioned"  : 1,
                        "Vehicle_Stopped"     : 1,
                        "Vehicle_Enters_Zone" : 1,
                        "Vehicle_Leaves_Zone" : 1,
                        "Vehicle_Stopped_Inside_Zone" :1,
                        "Vehicle_Positioning" : 1,
                        "Arrival_Preparation" : 1,
                        'AFT_LD_Positioning' : 1,
                        'FWD_TS_Positioning' : 1,
                        'TK_Positioning'     : 1,
                        
                        }
    
    sed_recognitions_data  = {}
    q_turnover_data = 'SELECT * FROM "S_Turnover"'
    turnover_data = connection.query(q_turnover_data).getresult()
    turnover_sed_recognized_data = {}
    for i in turnover_data:
        turnover_id = i[1]
        int_key = int(turnover_id[-3:])
        if int_key not in videos:
            print repr(int_key) + ' not in vids'
            # Skip processing video if it is not in the considered videos
            continue
        
        log.info('Processing ' + YBT + turnover_id + RESET)    
        # Ignore milliseconds
        startTime = datetime.strptime(i[2].split('.')[0],"%Y-%m-%d %H:%M:%S")
        endTime   = datetime.strptime(i[3].split('.')[0],"%Y-%m-%d %H:%M:%S")
    
        get_data_query = 'SELECT "activityKey", "activityID", "startTime", "endTime", "startFrameID", ' \
                         '"endFrameID", "frameKey", "name", "activityAText" FROM "S_Activity" WHERE ' \
                         '"startTime" > \'%(stt)s\' AND "endTime" < \'%(ndt)s\'' \
                         % {'stt':startTime.isoformat(),'ndt':endTime.isoformat()}
        # Result is list of tuples. Convert it to list of lists because we have to add few more fields
        turnover_ped_data = map(list, connection.query(get_data_query).getresult())
        print repr(len(turnover_ped_data)) + '  ' + repr(int_key)
        
        turnover_sed_recognized_data[int_key] = {}
        for ind in xrange(len(turnover_ped_data)):
            record = turnover_ped_data[ind]
            activity_name = record[7]
            if activity_name in event_names:
                start_time = datetime.strptime(record[2].split('.')[0],"%Y-%m-%d %H:%M:%S")
                end_time   = datetime.strptime(record[3].split('.')[0],"%Y-%m-%d %H:%M:%S")                
                if activity_name in turnover_sed_recognized_data[int_key]:
                    turnover_sed_recognized_data[int_key][activity_name].append([start_time, endTime])
                else:
                    turnover_sed_recognized_data[int_key][activity_name] = [[start_time, endTime]]
    return turnover_sed_recognized_data       

def get_ped_data_from_pgsql(videos):
    import ConfigParser
    from datetime import datetime
    import os
    import pg as pgsql
    import sys
    
    from base.base_constants import GBT, RBB, YBT, RESET
    
    py_version = str(sys.version[:3])
    if os.environ['COF_LEARN_ROOT']:
        ROOT_DIR = os.environ['COF_LEARN_ROOT']        
    else:
        ROOT_DIR = '/home/csunix/visdata/cofriend/data/'     

    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(ROOT_DIR + '/config.cfg')  

    dbase_name = cfg_parser.get('PGSQL', 'database')
    host_name  = cfg_parser.get('PGSQL', 'host')
    port_num   = eval(cfg_parser.get('PGSQL', 'port'))
    password   = cfg_parser.get('PGSQL', 'passwd')
    camID      = cfg_parser.get('PARAMETERS', 'camID')
    
    try:    
        connection = pgsql.connect(dbname=dbase_name, host=host_name, port=port_num, passwd=password)   
        log.info(GBT + 'Database connection established' + RESET)
    except Exception:
        import traceback
        err_msg = traceback.format_exc(sys.exc_info())      
        log.error(RBB + err_msg + RESET)
        sys.exit(0)
        
    ped_activity_data  = {}
    q_turnover_data = 'SELECT * FROM "S_Turnover"'
    turnover_data = connection.query(q_turnover_data).getresult()
    turnover_ped_data = {}
    for i in turnover_data:
        turnover_id = i[1]
        int_key = int(turnover_id[-3:])
        if int_key not in videos:
            print repr(int_key) + ' not in vids'
            # Skip processing video if it is not in the considered videos
            continue
        
        log.info('Processing ' + YBT + turnover_id + RESET)    
        # Ignore milliseconds
        startTime = datetime.strptime(i[2].split('.')[0],"%Y-%m-%d %H:%M:%S")
        endTime   = datetime.strptime(i[3].split('.')[0],"%Y-%m-%d %H:%M:%S")
        
        #if int_key in [29, 58, 59, 61, 63]:
            ## This is a temporary fix
            #sy = repr(startTime.year)
            #sm = repr(startTime.month)
            #sd = repr(startTime.day)
            #sh = repr(startTime.hour + 1)
            #smin = repr(startTime.minute)
            #ss = repr(startTime.second)
    
            #ey = repr(endTime.year)
            #em = repr(endTime.month)
            #ed = repr(endTime.day)
            #eh = repr(endTime.hour + 1)
            #emin = repr(endTime.minute)
            #es = repr(endTime.second)
    
            #startTime = datetime.strptime(sy + '-' + sm + '-' + sd + ' ' + sh + ':' + smin + ':' + ss, "%Y-%m-%d %H:%M:%S")
            #endTime   = datetime.strptime(ey + '-' + em + '-' + ed + ' ' + eh + ':' + emin + ':' + es, "%Y-%m-%d %H:%M:%S")
        
        # Get data that has startTime and endTime within the limits
        get_data_query = 'SELECT "activityKey", "activityID", "startTime", "endTime", "startFrameID", ' \
                         '"endFrameID", "frameKey", "name", "activityAText" FROM "S_Activity" WHERE ' \
                         '"startTime" > \'%(stt)s\' AND "endTime" < \'%(ndt)s\'' \
                         % {'stt':startTime.isoformat(),'ndt':endTime.isoformat()}
        # Result is list of tuples. Convert it to list of lists because we have to add few more fields
        turnover_ped_data[turnover_id] = map(list, connection.query(get_data_query).getresult())
        print repr(len(turnover_ped_data[turnover_id])) + '  ' + repr(int_key)
        for ind in xrange(len(turnover_ped_data[turnover_id])):
            record = turnover_ped_data[turnover_id][ind]
            activity_key = record[0]
            frame_key    = record[6]
            print repr(turnover_id) + ' : ' + repr(frame_key)
            q_obj_data = 'SELECT "name", "objectID", "activityKey" FROM "S_ActivityParameter" ' \
                         'WHERE "activityKey" = %d' % activity_key
            obj_data = map(list, connection.query(q_obj_data).getresult())
            objs = []
            for i in xrange(len(obj_data)):
                obj = obj_data[i]
                # Test if obj is vehicle. Other type is a zone
                if obj[0].startswith('V') or obj[0].startswith('v'):
                    # Get the vehicle type
                    mobID = obj[1]
                    #q_obj_type = 'SELECT "type", "subtype" FROM "S_Mobile" WHERE ' \
                                 #'"mobileID" = %d AND "frameKey" = %d' \
                                 #% (mobID, frame_key)
                    q_obj_type = 'SELECT "type", "subtype" FROM "S_Mobile" WHERE ' \
                                 '"mobileID" = %(mobid)d AND "startTime" > \'%(stt)s\' AND "startTime" < \'%(ndt)s\'' \
                                 % {'mobid':mobID, 'stt':startTime.isoformat(),'ndt':endTime.isoformat()}
                    # Only one record is returned. So take the first one as the result is a list.
                    if len(connection.query(q_obj_type).getresult()) > 0:
                        (typ,subtyp) = connection.query(q_obj_type).getresult()[0]
                    else:
                        log.warning('Not found the record with objID and frame_key')
                        break
                     # Types are first separated by '-' and then type and score separated by ':'
                    main_typ = typ.split('-')
                    if main_typ[0].split(':')[0] == 'AIRCRAFT':
                        obj_type = main_typ[0].split(':')[0]
                    elif main_typ[0].split(':')[0] == 'VEHICLE':
                        if subtyp.split(':')[0] == 'UNKNOWN':
                            if len(subtyp.split('|')) > 1:
                                obj_type = subtyp.split('|')[1].split(':')[0]
                            else: 
                                # make it UNKNOWN
                                obj_type = subtyp.split('-')[0].split(':')[0]
                        else:
                            obj_type = subtyp.split('-')[0].split(':')[0]
                    elif main_typ[0].split(':')[0] == 'OTHER':
                        if subtyp.split(':')[0] == 'UNKNOWN':
                            if len(subtyp.split('|')) > 1:
                                obj_type = subtyp.split('|')[1].split(':')[0]
                        else:    
                            obj_type = subtyp.split('|')[0].split(':')[0]
                    elif main_typ[0].split(':')[0] == 'PERSON':        
                        if subtyp.split(':')[0] == 'PERSON':
                            obj_type = 'PERSON'
                        else:
                            obj_type = subtyp.split('|')[0].split(':')[0]
                    else:
                        print 'Error: Unknown type encountered'
                            
                    #obj[0] = obj_type + '(' + obj[0] + ')'
                    # In new Inria data obj name is always v1, so use mobID to get correct name
                    obj[0] = obj_type + '(' + obj[0][0] + '_' + repr(mobID) + ')'
                    # get start and end frame ids
                    #q_mobKey = 'SELECT "mobileKey" FROM "S_Mobile" WHERE ' \
                               #'"mobileID" = %d AND "frameKey" = %d' \
                               #% (mobID, frame_key)                    
                    #mobKey = connection.query(q_mobKey).getresult()
                    #if len(mobKey) != 0:
                        #mobKey = mobKey[0]
                    #q_frameID = 'SELECT "frameID", "camID" FROM "S_Info2D" WHERE ' \
                               #'"mobileKey" = %d' % (mobKey)
                    #fIDs = connection.query(q_frameID).getresult()
                    #for f in fIDs:
                        #if f[1] == camID:
                            #startFrameID = f[0]
                            #endFrameID   = startFrameID + (record[5] - record[4])
                objs.append(obj[0].lower())
                
            startFrameID = record[4]
            endFrameID   = record[5]    
            record.append(startFrameID)
            record.append(endFrameID)
            record.append(objs)          
        
    ped_activity_data['activity'] = turnover_ped_data
    connection.close()
    return ped_activity_data

def pgsql_ped_to_relational(pgsql_data):    
    import cPickle as pickle
    import os
    import re
    import sys
    
    from base.ilp.logic import Expr, expr
    from base.base_constants import GBT, RBB, YBT, RESET
    
    all_types = {'unknown': ['obj','unknown'],
                 'person': ['obj','person'],                      
                 'aircraft': ['obj','veh','heavy_veh','aircraft'],
                 #'aircraft': ['obj', 'aircraft'],
                 'vehicle': ['obj','veh'],
                 'service_vehicle': ['obj','veh','light_veh','service_vehicle'],
                 'push_back': ['obj','veh','light_veh','push_back'],
                 'passenger_boarding_bridge': ['obj','veh','heavy_veh','passenger_boarding_bridge'],
                 'container': ['obj','veh','heavy_veh','container'],
                 'catering': ['obj','veh','heavy_veh','catering'],
                 'transporter': ['obj','veh','light_veh','transporter'],                      
                 'ground_power_unit': ['obj','veh','light_veh','ground_power_unit'], 
                 'conveyor_belt': ['obj','veh','heavy_veh','conveyor_belt'],
                 'loader': ['obj','veh','heavy_veh','loader'],
                 'bulk_loader': ['obj','veh','heavy_veh','bulk_loader'],
                 'passenger_stair': ['obj','veh','heavy_veh','passenger_stair'],
                 'tanker': ['obj','veh','heavy_veh','tanker'],
                 'mobile_stair': ['obj','veh','heavy_veh','mobile_stair']
                }
    
    pgsql_data = pgsql_data['activity']
    relational_data = {}
    # record = [actv_key, actv_ID, startTime, endTime, startFrame, endFrame, frameKey, actv_name, actv_class, real_s, real_e, [objs]]
    # record = [   0    ,    1   ,    2     ,    3   ,     4     ,    5    ,    6    ,     7    ,      8    ,    9  ,   10  ,   11]
    for key in pgsql_data:
        if len(pgsql_data[key]) == 0:
            continue
        print 'Processing ' + key
        log.info('Getting relational data from ' + YBT + key + RESET)
        # Get last 3 chars of the key and convert them into a number. Ex: 'cof065' to 65.
        int_key = int(key[-3:])
        relational_data[int_key] = {}
        # First ints, objs, zones are stored in dicts to avoid duplicates
        objs    = {}
        intvs   = {}        
        zones   = {}
        clauses = {}        
        clauses['int']  = []
        clauses['obj']  = []
        clauses['zone'] = []
        start = 10000
        end   = 0
        for record in pgsql_data[key]:
            s    = record[9]
            e    = record[10]
            start = min(start, s)
            end   = max(end, e)
            rel  = record[7]
            rel  = rel[0].lower() + rel[1:]
            args = record[11]

            # add some stuff to clauses dict
            if len(args) < 1:
                continue
            if args[0] not in objs:
                objs[args[0]] = 1
            if len(args) > 1:
                # The second obj is always a zone
                if args[1] not in zones:
                    zones[args[1]] = 1
           
            # Prepare arguments for relational expression
            try:
                (typ, obj) = re.match('(.*)\((.*)\)', args[0]).groups()
            except AttributeError:
                continue
            
            """Ignore relations with persons in them"""
            #if typ == 'person':
                #continue
            
            real_type = all_types[typ]
            obj_expr = Expr(real_type, obj)            
            rel_expr_args = [obj_expr]
            if len(args) > 1:
                rel_expr_args.append(args[1])

            intv = Expr('int', [record[9], record[10]])
            if intv not in intvs:
                intvs[intv] = 1
            rel_expr_args.append(intv)
            
            rel_expr = Expr(rel, rel_expr_args)
            
            try:
                clauses[rel].append(rel_expr)
            except KeyError:
                clauses[rel] = [rel_expr]
                
        clauses['int']  = intvs.keys()
        for key in objs.keys():
            # seperate type and object. Example input is loader(v_25)
            try:
                (typ, obj) = re.match('(.*)\((.*)\)', key).groups()
            except AttributeError:
                continue
            real_type = all_types[typ]
            obj_expr = Expr(real_type, obj)
            clauses['obj'].append(obj_expr)
        for key in zones.keys():
            zone_expr = Expr('zone', key)
            clauses['zone'].append(zone_expr)
        relational_data[int_key] = (clauses, (start, end))
    return relational_data
    #pickle.dump(relational_data, open(pickle_rel_data_file, 'w'), 1)

def correct_types_in_relational_data(relational_data):
    from base.utils.base_utils import most_common
    from base.ilp.logic import Expr
    
    obj_type_lists = {}
    spr = ['vehicle_Positioning', 'vehicle_Stopped', \
           'vehicle_Stopped_Inside_Zone', 'vehicle_Positioned',\
           'vehicle_Inside_Zone', 'vehicle_Outside_Zone','vehicle_Enters_Zone', \
           'vehicle_Removing', 'vehicle_Leaves_Zone']

    for vid in relational_data:
        obj_type_lists[vid] = {}
        for rel in relational_data[vid][0]:
            if rel in spr:
                for fact in relational_data[vid][0][rel]:
                    for arg in fact.args:
                        if len(arg.args) is not 0 and arg.op != 'int':
                            # If arg is not zone or interval
                            obj = arg.args[0]
                            if obj not in obj_type_lists[vid]:
                                obj_type_lists[vid][obj] = []
                            # Collect the types of this obj in a list
                            obj_type_lists[vid][obj].append(arg.op)
     
    # Now get the most common type of an object 
    obj_types = {}
    for vid in obj_type_lists:            
        obj_types[vid] = {}
        for obj in obj_type_lists[vid]:
            obj_types[vid][obj] = most_common(obj_type_lists[vid][obj])
            
    corrected_relational_data = {}        
    for vid in relational_data:
        corrected_relational_data[vid] = []
        corrected_relational_data[vid].append({})
        corrected_relational_data[vid].append(relational_data[vid][1])
        for rel in relational_data[vid][0]:
            if rel in spr:
                corrected_relational_data[vid][0][rel] = []
                for fact in relational_data[vid][0][rel]:
                    new_args = fact.args[:]
                    for i in xrange(len(fact.args)):
                        if len(fact.args[i].args) is not 0 and fact.args[i].op != 'int':
                            # If arg is not zone or interval, get new expr for obj with corrected type
                            new_args[i] = Expr(obj_types[vid][fact.args[i].args[0]], fact.args[i].args[0])
                    # Get new fact with corrected type 
                     
                    """Ignore relations with persons in them"""
                    if 'person' in new_args[0].op:             
                        continue
                    
                    new_fact = Expr(fact.op, new_args)
                    #if repr(fact) != repr(new_fact):
                        #print fact, new_fact
                    # Append the new fact
                    corrected_relational_data[vid][0][rel].append(new_fact)
            else:
                # Just copy data of other relations
                corrected_relational_data[vid][0][rel] = relational_data[vid][0][rel][:]
                                    
    return corrected_relational_data

def correct_rels_in_ped_relational_data(relational_data):
    import copy
    from base.utils.base_utils import most_common
    from base.ilp.logic import Expr
    
    # Ignoring 'vehicle_Stopped'. So removing it from data
    valid_spr = ['vehicle_Positioning',\
                 'vehicle_Stopped_Inside_Zone',\
                 'vehicle_Positioned',\
                 'vehicle_Inside_Zone', \
                 'vehicle_Outside_Zone',\
                 'vehicle_Enters_Zone', \
                 'vehicle_Leaves_Zone']
    
    copy_rels = ['int', 'obj', 'zone']
    
    obj_pair = {}
    new_relational_data = {}
    for vid in relational_data:
        new_relational_data[vid] = []
        new_relational_data[vid].append({})
        new_relational_data[vid].append(relational_data[vid][1])
        obj_pair[vid] = {}
        for rel in relational_data[vid][0]:
            if rel in valid_spr:
                for fact in relational_data[vid][0][rel]:
                    (obj, zone) = (fact.args[0].args[0].op, fact.args[1].op)
                    if (obj, zone) not in obj_pair[vid]:
                        obj_pair[vid][(obj, zone)] = {}
                        obj_pair[vid][(obj, zone)]['intvs'] = []
                        obj_pair[vid][(obj, zone)]['type'] = fact.args[0].op
                    # Store all intervals related to obj, zone pair seperately
                    obj_pair[vid][(obj, zone)]['intvs'].append(fact.args[-1])
                    try:                        
                        obj_pair[vid][(obj, zone)][fact.op].append(fact.args[-1])
                    except KeyError:
                        obj_pair[vid][(obj, zone)][fact.op] = [fact.args[-1]]
            elif rel in copy_rels:
                new_relational_data[vid][0][rel] = relational_data[vid][0][rel][:]
                
        # Now get rid of some relations.
        obj_pair_dup = copy.deepcopy(obj_pair[vid])
        print len(obj_pair_dup)
        for (obj, zone) in obj_pair_dup:
            if vid == 3 and obj == 'v_68':
                print 'hi'
            # If 'v_O_Z' is the only relation between an obj and zone get rid of it (the others are 'intvs' and 'type')
            if len(obj_pair[vid][(obj, zone)]) == 3 and 'vehicle_Outside_Zone' in obj_pair[vid][(obj, zone)]:
                obj_pair[vid].pop((obj, zone))
                continue
            
            
            #First adjust 'vehicle_Inside_Zone' and 'vehicle_Positioned'
            v_I_Z_invs = []
            v_P_invs   = []
            v_O_Z_invs = []
            if 'vehicle_Inside_Zone' in obj_pair_dup[(obj, zone)]:
                for intv in obj_pair_dup[(obj, zone)]['vehicle_Inside_Zone']:
                    v_I_Z_invs.append(intv.args[0].op)
                    v_I_Z_invs.append(intv.args[1].op)
                (v_I_Z_start, v_I_Z_end) = (min(v_I_Z_invs), max(v_I_Z_invs))
                obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] = [Expr('int', [v_I_Z_start, v_I_Z_end])]
                new_relational_data[vid][0]['int'].append(Expr('int', [v_I_Z_start, v_I_Z_end]))
                
            if 'vehicle_Positioned' in obj_pair_dup[(obj, zone)]:
                for intv in obj_pair_dup[(obj, zone)]['vehicle_Positioned']:
                    v_P_invs.append(intv.args[0].op)
                    v_P_invs.append(intv.args[1].op)
                (v_P_start, v_P_end) = (min(v_P_invs), max(v_P_invs))
                obj_pair[vid][(obj, zone)]['vehicle_Positioned']  = [Expr('int', [v_P_start, v_P_end])]
                new_relational_data[vid][0]['int'].append(Expr('int', [v_P_start, v_P_end]))
              
            if 'vehicle_Outside_Zone' in obj_pair_dup[(obj, zone)]:
                for intv in obj_pair_dup[(obj, zone)]['vehicle_Outside_Zone']:
                    v_O_Z_invs.append(intv.args[0].op)
                    v_O_Z_invs.append(intv.args[1].op)
                (v_O_Z_start, v_O_Z_end) = (min(v_O_Z_invs), max(v_O_Z_invs))
                
            if len(v_I_Z_invs) != 0 and len(v_O_Z_invs) != 0:
                # Only one VOZ event after VIZ. Change 'vehicle_Outside_Zone'
                if v_O_Z_start > v_I_Z_end:
                    v_O_Z_start = v_I_Z_end + 1
                    obj_pair[vid][(obj, zone)]['vehicle_Outside_Zone'] = [Expr('int', [v_O_Z_start, v_O_Z_end])]
                    new_relational_data[vid][0]['int'].append(Expr('int', [v_O_Z_start, v_O_Z_end]))
                # Only one VOZ event before VIZ.  Change 'vehicle_Inside_Zone'
                elif v_O_Z_end < v_I_Z_start:
                    v_I_Z_start = v_O_Z_end + 1
                    obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] = [Expr('int', [v_I_Z_start, v_I_Z_end])]
                    new_relational_data[vid][0]['int'].append(Expr('int', [v_I_Z_start, v_I_Z_end]))
                # Two VOZ events, before and after VIZ. Change 'vehicle_Outside_Zone'    
                elif v_O_Z_end > v_I_Z_end and v_O_Z_start < v_I_Z_start:
                    v_O_Z_temp_end = v_I_Z_start - 1
                    obj_pair[vid][(obj, zone)]['vehicle_Outside_Zone'] = [Expr('int', [v_O_Z_start, v_O_Z_temp_end])]
                    new_relational_data[vid][0]['int'].append(Expr('int', [v_O_Z_start, v_O_Z_temp_end]))
                    v_O_Z_start = v_I_Z_end + 1
                    obj_pair[vid][(obj, zone)]['vehicle_Outside_Zone'].append(Expr('int', [v_O_Z_start, v_O_Z_end]))
                    new_relational_data[vid][0]['int'].append(Expr('int', [v_O_Z_start, v_O_Z_end]))
                
                #obj_pair[vid][(obj, zone)]['vehicle_Positioned']  = [Expr('int', [v_O_Z_start, v_O_Z_end])]    
                
            #if len(v_I_Z_invs) != 0 and len(v_P_invs) != 0:
                #print obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] 
                #print obj_pair[vid][(obj, zone)]['vehicle_Positioned']
                #if v_I_Z_end < v_P_start:
                    ## if the inside_zone and positioned are gaped, then make them meet by extending v_P start backwards
                    #v_P_start = v_I_Z_start + 1
                    #obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] = [Expr('int', [v_I_Z_start, v_I_Z_end])]                    
                    #obj_pair[vid][(obj, zone)]['vehicle_Positioned']  = [Expr('int', [v_P_start, v_P_end])]                
                #elif v_I_Z_end > v_P_start:
                    ## if the inside_zone and positioned are overlaped, then make them meet by extending v_I_Z end backwards
                    #v_I_Z_end = v_P_start - 1
                    #obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] = [Expr('int', [v_I_Z_start, v_I_Z_end])]
                    #obj_pair[vid][(obj, zone)]['vehicle_Positioned']  = [Expr('int', [v_P_start, v_P_end])]  
                #print obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] 
                #print obj_pair[vid][(obj, zone)]['vehicle_Positioned']
    
            # First adjust 'vehicle_Inside_Zone' and 'vehicle_Positioned'
            #v_L_Z_invs = []
            #v_P_invs   = []
            #if 'vehicle_Leaves_Zone' in obj_pair_dup[(obj, zone)]:
                #for intv in obj_pair_dup[(obj, zone)]['vehicle_Leaves_Zone']:
                    #v_I_Z_invs.append(intv.args[0].op)
                    #v_I_Z_invs.append(intv.args[1].op)
                    #(v_I_Z_start, v_I_Z_end) = (min(v_I_Z_invs), max(v_I_Z_invs))
                ##obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] = [Expr('int', [v_I_Z_start, v_I_Z_end])]
                
            #if 'vehicle_Positioned' in obj_pair_dup[(obj, zone)]:
                #for intv in obj_pair_dup[(obj, zone)]['vehicle_Positioned']:
                    #v_P_invs.append(intv.args[0].op)
                    #v_P_invs.append(intv.args[1].op)
                    #(v_P_start, v_P_end) = (min(v_P_invs), max(v_P_invs))
                ##obj_pair[vid][(obj, zone)]['vehicle_Positioned']  = [Expr('int', [v_P_start, v_P_end])]
            
            #if len(v_I_Z_invs) != 0 and len(v_P_invs) != 0:
                #print obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] 
                #print obj_pair[vid][(obj, zone)]['vehicle_Positioned']
                #if v_I_Z_end < v_P_start:
                    ## if the inside_zone and positioned are gaped, then make them meet by extending v_P start backwards
                    #v_P_start = v_I_Z_start + 1
                    #obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] = [Expr('int', [v_I_Z_start, v_I_Z_end])]                    
                    #obj_pair[vid][(obj, zone)]['vehicle_Positioned']  = [Expr('int', [v_P_start, v_P_end])]                
                #elif v_I_Z_end > v_P_start:
                    ## if the inside_zone and positioned are overlaped, then make them meet by extending v_I_Z end backwards
                    #v_I_Z_end = v_P_start - 1
                    #obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] = [Expr('int', [v_I_Z_start, v_I_Z_end])]
                    #obj_pair[vid][(obj, zone)]['vehicle_Positioned']  = [Expr('int', [v_P_start, v_P_end])]  
                #print obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] 
                #print obj_pair[vid][(obj, zone)]['vehicle_Positioned']
                
            ## Now adjust 'vehicle_Inside_Zone' and 'vehicle_Positioned' 'vehicle_Outside_Zone'
            #v_I_Z_invs = []
            #v_O_Z_invs = []
            #v_P_invs   = []            
            #if 'vehicle_Inside_Zone' in obj_pair_dup[(obj, zone)]:
                #for intv in obj_pair_dup[(obj, zone)]['vehicle_Inside_Zone']:
                    #v_I_Z_invs.append(intv.args[0].op)
                    #v_I_Z_invs.append(intv.args[1].op)
                    #(v_I_Z_start, v_I_Z_end) = (min(v_I_Z_invs), max(v_I_Z_invs))
                ##obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone'] = [Expr('int', [v_I_Z_start, v_I_Z_end])]
                
            #if 'vehicle_Positioned' in obj_pair_dup[(obj, zone)]:
                #for intv in obj_pair_dup[(obj, zone)]['vehicle_Positioned']:
                    #v_P_invs.append(intv.args[0].op)
                    #v_P_invs.append(intv.args[1].op)
                    #(v_P_start, v_P_end) = (min(v_P_invs), max(v_P_invs))
                ##obj_pair[vid][(obj, zone)]['vehicle_Positioned']  = [Expr('int', [v_P_start, v_P_end])]
            #if 'vehicle_Outside_Zone' in obj_pair_dup[(obj, zone)]:
                #for intv in obj_pair_dup[(obj, zone)]['vehicle_Outside_Zone']:
                    #v_O_Z_invs.append(intv.args[0].op)
                    #v_O_Z_invs.append(intv.args[1].op)
                    #(v_O_Z_start, v_O_Z_end) = (min(v_O_Z_invs), max(v_O_Z_invs))
                ##obj_pair[vid][(obj, zone)]['vehicle_Outside_Zone'] = [Expr('int', [v_O_Z_start, v_O_Z_end])]
            #if len(v_I_Z_invs) != 0 and len(v_O_Z_invs) != 0 and len(v_P_invs) != 0:
                #if v_O_Z_end < v_I_Z_start:
                    #v_I_Z_start = v_O_Z_end + 1
                    #obj_pair[vid][(obj, zone)]['vehicle_Inside_Zone']  = [Expr('int', [v_I_Z_start, v_I_Z_end])]
                    #obj_pair[vid][(obj, zone)]['vehicle_Outside_Zone'] = [Expr('int', [v_O_Z_start, v_O_Z_end])]
                #elif v_O_Z_end > v_P_end and if v_O_Z_start < v_I_Z_start:
                    #obj_pair[vid][(obj, zone)]['vehicle_Outside_Zone'] = [Expr('int', [v_O_Z_start, v_I_Z_start - 1])]
                    #v_O_Z_start = v_P_end + 1
                    #obj_pair[vid][(obj, zone)]['vehicle_Outside_Zone'].append(Expr('int', [v_O_Z_start, v_O_Z_end]))
                
        #print len(obj_pair[vid]) 
                         
        for (obj, zone) in obj_pair[vid]:
            obj_expr  = Expr(obj_pair[vid][(obj, zone)]['type'], obj)
            zone_expr = Expr(zone)
            for key_rel in obj_pair[vid][(obj, zone)]:
                if key_rel not in ['intvs', 'type']:
                    if key_rel not in new_relational_data[vid][0]:
                        new_relational_data[vid][0][key_rel] = []
                    for intv in obj_pair[vid][(obj, zone)][key_rel]:
                        rel_expr = Expr(key_rel, [obj_expr, zone_expr, intv])
                        print rel_expr
                        new_relational_data[vid][0][key_rel].append(Expr(key_rel, [obj_expr, zone_expr, intv]))
            
    return new_relational_data                
                    
def get_opra_rel(data_file, output_file, opra_param):
    import cPickle as pickle
    from math import sin, cos, radians
    import os
    import re
    import socket
    import sys
    import time

    from base.ilp.logic import Expr
    
    CRLF = "\r\n"
    
    all_types = {'unknown': ['obj','unknown'],
                 'person': ['obj','person'],  
                 'vehicle': ['obj','veh'],
                 'aircraft': ['obj','veh','heavy_veh','aircraft'],                
                 'service_vehicle': ['obj','veh','light_veh','service_vehicle'],
                 'push_back': ['obj','veh','light_veh','push_back'],
                 'passenger_boarding_bridge': ['obj','veh','heavy_veh','passenger_boarding_bridge'],
                 'container': ['obj','veh','heavy_veh','container'],
                 'catering': ['obj','veh','heavy_veh','catering'],                 
                 'transporter': ['obj','veh','light_veh','transporter'],                      
                 'ground_power_unit': ['obj','veh','light_veh','ground_power_unit'], 
                 'conveyor_belt': ['obj','veh','heavy_veh','conveyor_belt'],
                 'loader': ['obj','veh','heavy_veh','loader'],
                 'bulk_loader': ['obj','veh','heavy_veh','bulk_loader'],
                 'passenger_stair': ['obj','veh','heavy_veh','passenger_stair'],
                 'tanker': ['obj','veh','heavy_veh','tanker'],
                 'mobile_stair': ['obj','veh','heavy_veh','mobile_stair']
                }
    
    # Define line endings
    def readline():
        # Read a line from the server . Strip trailing CR and / or LF
        input = sockfile.readline()
        if not input:
            raise EOFError
        if input[-2:] == CRLF: # strip line endings
            input = input[:-2]
        elif input[-1:] in CRLF:
            input = input[:-1]
        if len(input) == 0:
            return readline()
        if input[0] == ";":
            # ignore comments
            return readline()
        else:
            return input
    def sendline(line):
        # Send a line to the server. 
        sock.send(line + CRLF) # unbuffered write

    # create a socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
    # connect to sparq
    sock.connect(('localhost' , 4443))
    sockfile = sock.makefile('rw')
    p_str  = '\((.*)\s\)'
    # To match the sub result
    ip_str = '\(*([\w\s]*)\)*$'
    result_pattern     = re.compile(p_str)
    sub_result_pattern = re.compile(ip_str)
    
    data_3d = pickle.load(open(data_file))  
    sol = {}
    for vid in data_3d.keys():      
        frames = data_3d[vid].keys()
        if len(frames) == 0:
            continue
        frames.sort()        
        # To match the overall result
        start = min(frames)
        end   = max(frames)
        rel_data = {}
        frame_rels = {}
        obj_rels = {}
        no_obj_frames = {}
        for frame in frames:
            #print frame
            frame_rels[frame] = {}
            frame_data = data_3d[vid][frame]
            objs = {}
            obj_typ_map = {}
            for i in xrange(len(frame_data)):
                # "mobileID", "x", "y", "z", "w3d", "h3d", "l3d",
                # "orientation", "type", "subtype", "mobileKey", "time", "frameKey"
                mob_id = frame_data[i][0]
                x      = frame_data[i][1]
                y      = frame_data[i][2]
                ot     = frame_data[i][7]
                typ    = frame_data[i][8]
                subtyp = frame_data[i][9]
                
                # Types are first separated by '-' and then type and score separated by ':'
                main_typ = typ.split('-')
                if main_typ[0].split(':')[0] == 'AIRCRAFT':
                    obj_type = main_typ[0].split(':')[0]
                elif main_typ[0].split(':')[0] == 'VEHICLE':
                    if subtyp.split(':')[0] == 'UNKNOWN':
                        if len(subtyp.split('|')) > 1:
                            obj_type = subtyp.split('|')[1].split(':')[0]
                        else: 
                            # make it UNKNOWN
                            obj_type = subtyp.split('-')[0].split(':')[0]
                    else:
                        obj_type = subtyp.split('-')[0].split(':')[0]
                elif main_typ[0].split(':')[0] == 'OTHER':
                    if subtyp.split(':')[0] == 'UNKNOWN':
                        if len(subtyp.split('|')) > 1:
                            obj_type = subtyp.split('|')[1].split(':')[0]
                    else:    
                        obj_type = subtyp.split('|')[0].split(':')[0]
                            
                #print frame_data[i]                                   
                mob_id_str = 'v_' + repr(mob_id)
                obj_typ_map[mob_id_str] = obj_type.lower()            

                objs[mob_id] = (mob_id_str, repr(x), repr(y), repr(sin(radians(ot))), repr(cos(radians(ot))))
            q_str = 'qualify opra-' + opra_param + ' all ('
            for i in objs:
                q_str += '(' + ' '.join(objs[i]) + ') '
            q_str = q_str.strip()
            q_str += ')'
            #print q_str
            sendline(q_str)
            scene = readline()[6:].strip()
            #print scene
            # rel_str looks like '(O1 2_5 O2) (O1 2_6 O3) (O2 5_2 O3)'
            try:
                result_str = result_pattern.match(scene).groups()[0]
                rels = result_str.split(') (')
                # rels looks like ['(O1 2_5 O2', 'O1 2_6 O3', 'O2 5_2 O3)']
                for i in rels:
                    # rel_str looks like 'O1 2_5 O2'
                    rel_str = sub_result_pattern.match(i).groups()[0]                    
                    obj1, rel, obj2 = rel_str.split()                    
                    # SparQ returns capital letters for objs
                    obj1 = obj1.lower()
                    obj2 = obj2.lower()                    
                    typ1 = obj_typ_map[obj1]
                    typ2 = obj_typ_map[obj2]
                    #print typ1, typ2
                    obj1 = Expr(all_types[typ1], obj1)
                    obj2 = Expr(all_types[typ2], obj2)

                    # Just '1_2' as relation name does not work with 'Expr'
                    rel = 'r_' + rel
                    if (obj2, obj1) not in frame_rels[frame]:
                        frame_rels[frame][(obj1, obj2)] = rel
                    else:
                        frame_rels[frame][(obj2, obj1)] = rel
                    try:
                        if (obj2, obj1) not in obj_rels:
                            obj_rels[(obj1, obj2)].append((frame, rel))
                        else:                         
                            obj_rels[(obj2, obj1)].append((frame, rel))                        
                    except KeyError:
                        obj_rels[(obj1, obj2)] = [(frame, rel)]
            except AttributeError:
                print 'No objs or only one object in this frame - ' + repr(vid) + ' :' + repr(frame)
                no_obj_frames.update({frame:1}) 
                pass
        rel_data['obj_rels']   = obj_rels
        rel_data['frame_rels'] = frame_rels
        rel_data['no_obj_frames'] = no_obj_frames
        sol[vid] = (rel_data, (start, end))
    sendline("quit")
    time.sleep(1)
    # and close the socket    
    sock.close()   
    pickle.dump(sol, open(output_file, 'w'))
    print 'Done'

def get_opraX4_rel(opra_data_file, output_data_file):
    import cPickle as pickle
    opra_data = pickle.load(open(opra_data_file))
    opraX4_map = {0 : 'f',
                  1 : 'f',
                  2 : 'f',
                  14: 'f',
                  15: 'f',
                  
                  11: 'r',
                  12: 'r',
                  13: 'r',
                  
                  6 : 'b',
                  7 : 'b',
                  8 : 'b',
                  9 : 'b',
                  10: 'b',
                  
                  3 : 'l',
                  4 : 'l',
                  5 : 'l',
                  
                  's': 's'
                  }
    sol = {}
    for vid in opra_data.keys():
        opraX4_data = {}
        if 'obj_rels' not in opra_data[vid][0]:
            continue
        (start, end) = opra_data[vid][1]
        obj_rels = opra_data[vid][0]['obj_rels']
        for (obj1, obj2) in obj_rels.keys():
            
            # Skip if one of the object is person
            if 'person' in obj1.op or 'person' in obj2.op:
                print repr(obj1) + '  ' + repr(obj2)
                continue
            
            opraX4_data[(obj1, obj2)] = []
            for (frame, rel) in obj_rels[(obj1, obj2)]:
                (op1, op2)  = (rel.split('_')[1], rel.split('_')[2])
                if op1 != 's':
                    opraX4_rel1 = opraX4_map[eval(op1)]
                else:
                    opraX4_rel1 = op1
                if op2 != 's':
                    opraX4_rel2 = opraX4_map[eval(op2)]
                else:
                    opraX4_rel2 = op2
                opraX4_rel = 'r_' + opraX4_rel1 + '_' + opraX4_rel2
                opraX4_data[(obj1, obj2)].append((frame, opraX4_rel))
                
        sol[vid] = ({'obj_rels':opraX4_data}, (start, end))
    pickle.dump(sol, open(output_data_file, 'w'))
    print 'ok'    
    
def get_opra_intv(rel_data_file, output_data_file):
    import cPickle as pickle
    rel_data = pickle.load(open(rel_data_file))
    sol = {}
    # Database has data for every 10 frames
    sample_length = 9
    
    for vid in rel_data.keys():
        if 'obj_rels' not in rel_data[vid][0]:
            continue
        (start, end) = rel_data[vid][1]
    
        obj_rels = rel_data[vid][0]['obj_rels']
        new_obj_rels_intv = {}
        for (obj1, obj2) in obj_rels.keys():
            new_obj_rels_intv[(obj1, obj2)] = []
            start_frame = None
            end_frame   = None
            current_rel = None
            
            for (frame, rel) in obj_rels[(obj1, obj2)]:
                if start_frame == None and current_rel == None:
                    start_frame = frame
                    current_rel = rel
                if current_rel != rel:
                    end_frame = frame - 1
                    new_obj_rels_intv[(obj1, obj2)].append(((start_frame, end_frame), current_rel))
                    start_frame = frame
                    current_rel = rel
                # End frame is set to current frame + sample_length always    
                end_frame = frame + sample_length
            else:
                new_obj_rels_intv[(obj1, obj2)].append(((start_frame, end_frame), current_rel))
        sol[vid] =  (new_obj_rels_intv, (start, end))
    pickle.dump(sol, open(output_data_file, 'w'))
    print 'ok'

def get_opra_intv_expr(rel_data_file, output_data_file):
    import cPickle as pickle
    import copy
    from base.ilp.logic import Expr
    
    rel_data = pickle.load(open(rel_data_file))
    sol = {}
    blanket = {}
    obj_rels = {}
    for vid in rel_data.keys():
        print vid
        if len(rel_data[vid][0].keys()) == 0:
            continue
        (start, end) = rel_data[vid][1]
        blanket['int'] = {}
        blanket['obj'] = {}
        for (obj1, obj2) in rel_data[vid][0].keys():
            for (intv, rel) in rel_data[vid][0][(obj1, obj2)]:
                intv_expr = Expr('int', [intv[0], intv[1]])
                rel_expr  = Expr(rel, [obj1, obj2, intv_expr])
                if rel in blanket:
                    blanket[rel].append(rel_expr)
                else:    
                    blanket[rel] = [rel_expr]
                if intv_expr not in blanket['int']:
                    blanket['int'].update({intv_expr:1})
                if obj1 not in blanket['obj']:
                    blanket['obj'].update({obj1:1})
                if obj2 not in blanket['obj']:
                    blanket['obj'].update({obj2:1})
                try:
                    obj_rels[(obj1, obj2)].append(rel_expr)
                except KeyError:
                    obj_rels[(obj1, obj2)] = [rel_expr]
        new_blanket = copy.deepcopy(blanket)
        sol[vid] = (new_blanket, (start, end))
        #sol[vid]['obj_rels'] = obj_rels
    pickle.dump(sol, open(output_data_file, 'w'))
    print 'ok'

def get_proximity_rel((x1, y1), (x2, y2), threshold):
    import math
    
    dist = math.sqrt(( x1-x2 )**2 + ( y1-y2 )**2)
    if dist > threshold:
        return 'far'
    else:
        return 'near'
    
def hist_of_proximity(data_3D_file):
    import cPickle as pickle
    import itertools
    import math
    import matplotlib.mlab as mlab
    import matplotlib.pyplot as plt
    import numpy as np

    data_3D = pickle.load(open(data_3D_file))
    sol = {}
    #X = {}
    X = []
    for vid in data_3D.keys():      
        print 'processing vid: ' + repr(vid)
        frames = data_3D[vid].keys()
        if len(frames) == 0:
            continue
        frames.sort()        
        # To match the overall result
        start = min(frames)
        end   = max(frames)
        for frame in frames:
            #print frame
            frame_data = data_3D[vid][frame]
            points = []
            dist = 0
            for i in xrange(len(frame_data)):
                # "mobileID", "x", "y", "z", "w3d", "h3d", "l3d",
                # "orientation", "type", "subtype", "mobileKey", "time", "frameKey"
                (x, y) = (frame_data[i][1], frame_data[i][2])
                points.append((x,y))
            for ((x1, y1), (x2, y2)) in itertools.combinations(points, 2):
                dist = math.sqrt( ( x1-x2 )**2 + ( y1-y2 )**2 )
                X.append(dist)
                #if dist in X:
                    #X.update({dist:X[dist] + 1})
                #else:    
                    #X[dist] = 1
                    
    # the histogram of the data
    #n, bins, patches = plt.hist(X, 5, normed=1, facecolor='green', alpha=0.75)
    print len(X)
    plt.hist(X[:300000], 100 ,facecolor='green', alpha=0.75)
    #mu, sigma = 100, 15

    # add a 'best fit' line
    #Y = mlab.normpdf( bins, mu, sigma)
    #l = plt.plot(X.keys(), X.values(),'b^')
    #l = plt.plot(X.values(), X.keys(),'b^')
    #plt.plot(s+nse, t, 'b^')

    plt.xlabel('dist')
    plt.ylabel('Number')
    plt.title('Proximity Histogram')
    #plt.axis([0, max(X.values()), 0, max(X.keys())])
    plt.grid(True)
    
    plt.show()
    
def get_ped_data_from_pgsql_bak(video):
    import ConfigParser
    from datetime import datetime
    import logging
    import os
    import pg as pgsql
    import sys
    
    py_version = str(sys.version[:3])
    if os.environ['COF_LEARN_ROOT']:
        ROOT_DIR = os.environ['COF_LEARN_ROOT']        
    else:
        ROOT_DIR = '/home/csunix/visdata/cofriend/data/'     

    cfg_parser = ConfigParser.ConfigParser()
    cfg_parser.read(ROOT_DIR + '/config.cfg')  

    log = logging.getLogger("cofriend.utils.read_from_pgsql")
    
    dbase_name = cfg_parser.get('PGSQL', 'database')
    host_name  = cfg_parser.get('PGSQL', 'host')
    port_num   = eval(cfg_parser.get('PGSQL', 'port'))
    password   = cfg_parser.get('PGSQL', 'passwd')

    try:    
        connection = pgsql.connect(dbname=dbase_name, host=host_name, port=port_num, passwd=password)
        #log.info('Connection established to database')
        print 'Connection established'
    except Exception:
        #log.critical('Could not connect to psql. Is the server running? Also check input parameters in config file.')
        print 'Could not connect to psql. Is the server running? Also check input parameters in config file.'
        
    pickled_ped_activity_data  = {}
    q_turnover_data = 'SELECT * FROM "S_Turnover"'
    turnover_data = connection.query(q_turnover_data).getresult()
    turnover_ped_data = {}
    for i in turnover_data:
        turnover_id = i[1]
        print 'Processing ' + turnover_id
    
        # Ignore milliseconds
        startTime = datetime.strptime(i[2].split('.')[0],"%Y-%m-%d %H:%M:%S")
        endTime   = datetime.strptime(i[3].split('.')[0],"%Y-%m-%d %H:%M:%S")
        # Get data that has startTime and endTime within the limits
        get_data_query = 'SELECT "activityKey", "activityID", "startTime", "endTime", "startFrameID", ' \
                         '"endFrameID", "frameKey", "name", "activityAText" FROM "S_Activity" WHERE ' \
                         '"startTime" > \'%(stt)s\' AND "endTime" < \'%(ndt)s\'' \
                         % {'stt':startTime.isoformat(),'ndt':endTime.isoformat()}
        # Result is list of tuples. Convert it to list of lists because we have to add few more fields
        turnover_ped_data[turnover_id] = map(list, connection.query(get_data_query).getresult())

        for ind in xrange(len(turnover_ped_data[turnover_id])):
            record = turnover_ped_data[turnover_id][ind]
            activity_key = record[0]
            frame_key    = record[6]
            q_obj_data = 'SELECT "name", "objectID", "activityKey" FROM "S_ActivityParameter" ' \
                         'WHERE "activityKey" = %d' % activity_key
            obj_data = map(list, connection.query(q_obj_data).getresult())
            objs = []
            for i in xrange(len(obj_data)):
                obj = obj_data[i]
                # Test if obj is vehicle. Other type is a zone
                if obj[0].startswith('V'):                    
                    # Get the vehicle type
                    mobID = obj[1]
                    q_obj_type = 'SELECT "type", "subtype" FROM "S_Mobile" WHERE ' \
                                 '"mobileID" = %d AND "frameKey" = %d' \
                                 % (mobID, frame_key)
                    # Only one record is returned. So take the first one as the result is a list.
                    if len(connection.query(q_obj_type).getresult()) > 0:
                        (typ,subtyp) = connection.query(q_obj_type).getresult()[0]
                    else:
                        print 'Not found the record with objID and frame_key'
                    main_typ = typ.split(':')
                    if main_typ[0] == 'AIRCRAFT':
                        obj_type = main_typ[0]
                    elif main_typ[0] == 'VEHICLE':
                        obj_type = subtyp.split(':')[0]
                    elif main_typ[0] == 'OTHER' and subtyp.split(':')[0] == 'UNKNOWN':                        
                        if len(main_typ) > 1:
                            # Try to get next main type if there is one otherwise make it UNKNOWN
                            obj_type = main_typ[1]
                        else:    
                            obj_type = subtyp.split(':')[0]
                    obj[0] = obj_type + '(' + obj[0] + ')'
                objs.append(obj[0].lower())
            record.append(objs)
        
    pickled_ped_activity_data['activity'] = turnover_ped_data
    connection.close()
    return pickled_ped_activity_data

def pgsql_ped_to_relational_bak(pickled_pgsql_file, pickle_rel_data_file):    
    import cPickle as pickle
    import logging
    import os
    import re
    import sys
    from base.ilp.logic import Expr, expr
    
    all_types = {'unknown': ['obj','unknown'],
                 'person': ['obj','person'],                      
                 'aircraft': ['obj','aircraft'],
                 'transporter': ['obj','veh','light_veh','transporter'],                      
                 'ground_power_unit': ['obj','veh','light_veh','ground_power_unit'], 
                 'conveyor_belt': ['obj','veh','heavy_veh','conveyor_belt'],
                 'loader': ['obj','veh','heavy_veh','loader'],
                 'bulk_loader': ['obj','veh','heavy_veh','bulk_loader'],
                 'passenger_stair': ['obj','veh','heavy_veh','passenger_stair'],
                 'tanker': ['obj','veh','heavy_veh','tanker'],
                 'mobile_stair': ['obj','veh','heavy_veh','mobile_stair']
                }
    
    pgsql_data = pickle.load(open(pickled_pgsql_file))
    pgsql_data = pgsql_data['activity']
    relational_data = {}
    # record = [actv_key, actv_ID, startTime, endTime, startFrame, endFrame, frameKey, actv_name, actv_class, [objs]]
    # record = [   0    ,    1   ,    2     ,    3   ,     4     ,    5    ,    6    ,     7    ,      8    ,    9  ]
    for key in pgsql_data:
        if len(pgsql_data[key]) == 0:
            continue
    
        print 'Processing ' + key
        # Get last 3 chars of the key and convert them into a number. Ex: 'cof065' to 65.
        int_key = int(key[-3:])
        relational_data[int_key] = {}
        # First ints, objs, zones are stored in dicts to avoid duplicates
        objs    = {}
        intvs   = {}        
        zones   = {}
        clauses = {}        
        clauses['int']  = []
        clauses['obj']  = []
        clauses['zone'] = []
        start = 10000
        end   = 0
        for record in pgsql_data[key]:
            s    = record[4]
            e    = record[5]
            start = min(start, s)
            end   = max(end, e)
            rel  = record[7]
            rel  = rel[0].lower() + rel[1:]
            args = record[9]

            # add some stuff to clauses dict
            if args[0] not in objs:
                objs[args[0]] = 1
            if len(args) > 1:
                # The second obj is always a zone
                if args[1] not in zones:
                    zones[args[1]] = 1
                    
            # Prepare arguments for relational expression    
            (typ, obj) = re.match('(.*)\((.*)\)', args[0]).groups()
            real_type = all_types[typ]
            obj_expr = Expr(real_type, obj)            
            rel_expr_args = [obj_expr]
            if len(args) > 1:
                rel_expr_args.append(args[1])

            intv = Expr('int', [record[4], record[5]])
            if intv not in intvs:
                intvs[intv] = 1
            rel_expr_args.append(intv)
            
            rel_expr = Expr(rel, rel_expr_args)
            
            try:
                clauses[rel].append(rel_expr)
            except KeyError:
                clauses[rel] = [rel_expr]
                
        clauses['int']  = intvs.keys()
        for key in objs.keys():
            # seperate type and object. Example input is loader(v_25)
            (typ, obj) = re.match('(.*)\((.*)\)', key).groups()
            real_type = all_types[typ]
            obj_expr = Expr(real_type, obj)
            clauses['obj'].append(obj_expr)
        for key in zones.keys():
            zone_expr = Expr('zone', key)
            clauses['zone'].append(zone_expr)
        relational_data[int_key] = (clauses, (start, end))
    pickle.dump(relational_data, open(pickle_rel_data_file, 'w'), 1)
    print 'DONE'
                

if __name__ == "__main__":
    import cPickle as pickle
    import sys
    import os
    
    #vid = raw_input("vid: ")
    #vids = eval(vid)

    #host = raw_input("host: ")
    
    os.environ['COF_LEARN_ROOT'] = '/home/csunix/visdata/cofriend/release/temp/lam/'
    sys.path.append('/home/csunix/visdata/cofriend/release/temp/lam/lib/python2.6/site-packages')
    #for vid in vids:
        #get_track_data_from_pgsql([vid], '/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/track_data_3D_20110301_' + repr(vid) + '.p', host)
   
    #data = get_2D_data_from_pgsql([1,3,4,8,18,29,58,59,61,62,63,66], '5')
    #data = get_2D_data_from_pgsql([1,3,4,8,18,29], '5')
    #file_p = open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/pgsql_2D_cam5_data_20101229_1.p', 'w')
    #pickle.dump(data, file_p, 1)
    ##file_p.close()
    #data = pickle.load(open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/pgsql_2D_cam5_data_20101229_1.p'))
    #data = pickle.load(open('/usr/not-backed-up/cofriend/hambueg_release/pgsql_3D_cam5_COF-all_20110124.p'))
    ###data = get_2D_data_from_pgsql([1], '5')
    f = open('/usr/not-backed-up/cofriend/hambueg_release/cof_3D_cam5_all_20110301_all.txt', 'w')
    in_dir = '/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/'
    for i_file in os.listdir(in_dir):
        if 'track_data_3D_20110301_' not in i_file:
            continue
        print i_file
        data = pickle.load(open(os.path.join(in_dir, i_file)))
        vid = data.keys()[0]
        frames = data[vid].keys()
        frames.sort()
        for frame in frames:
            if len(data[vid][frame]) == 0:
                continue
            #(mID, xM3D, yM3D, zM3D, w3D, h3D, l3D, obj_subtype, obj_type, ornt, xSpeed, ySpeed)
            for record in data[vid][frame]:
                new_record = [vid, frame]
                new_record.extend(record)
                new_record = repr(new_record)
                new_record = new_record.replace('[', '')
                new_record = new_record.replace(']', '')
                new_record += '\n'
                f.writelines(new_record)
    f.close()
    print 'Writing done'
    #for vid in data:
        #frames = data[vid].keys()
        #frames.sort()
        #for frame in frames:
            #for obj in data[vid][frame]:
                #record = [vid, frame]
                #record.extend(obj)
                #f.write(repr(record))
                #f.write('\n')
                ##f.writelines(record)
    #f.close()            
            
    #pickle.dump(data, open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/pgsql_3D_data_20101229.p', 'w'), 1)
    #data = get_ped_data_from_pgsql([4,8,33,35,41,47,48,49,50,58,59,61,63,66,67])
    #data = get_ped_data_from_pgsql([1,2,3,4,5,6,7,8,9,16,18,20,25,29,30,58,59,61,62,63,64,65,66])
    #data = get_ped_data_from_pgsql([59])
    #data = get_ped_data_from_pgsql([1,3,4,8,18,29,58,59,61,62,63,64,65,66])
    ##data = get_ped_data_from_pgsql([1])
    #get_track_data_from_pgsql([1,2,3,4,5,6,7,8,9,16,18,20,25,29,30,58,59,61,62,63,64,65,66], '/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/track_data_3D_20110301.p')
    #pickle.dump(data, open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/pgsql_ped_data_correct_20110301.p', 'w'), 1)
    #data = pickle.load(open('/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/pgsql_ped_data_correct_20110301.p'))
    #relational_data = pgsql_ped_to_relational(data)
    #type_corrected_relational_data = correct_types_in_relational_data(relational_data)
    #cpf = '/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/relational_ped_data_type_correct_aircraft_hv_20110301_n35_i150.p'
    #pickle.dump(type_corrected_relational_data, open(cpf, 'w'), 1)
    
    ##pgsql_ped_to_relational('/usr/not-backed-up/cofriend/data/db_pickled_new/pgsql_ped_data_correct_12-seq_MultiCam-SED.p', \
    ##                        '/usr/not-backed-up/cofriend/data/db_pickled_new/relational_ped_data_correct_12-seq_MultiCam-SED.p')
    ##pf = '/usr/not-backed-up/cofriend/data/db_pickled_new/relational_ped_data_correct.p'                            
    ##relational_data = pickle.load(open(pf))
    #type_corrected_relational_data = correct_types_in_relational_data(relational_data)
    #corrected_relational_data = correct_rels_in_ped_relational_data(type_corrected_relational_data)
    #cpf = '/home/csunix/visdata/cofriend/release/temp/lam/data/db/pickled_new/relational_ped_data_type_correct_20110301_n35_i150.p'
    #pickle.dump(type_corrected_relational_data, open(cpf, 'w'), 1)
    #pgsql_ped_to_relational('/tmp/pgsql_ped_data.p', \
                            #'/usr/not-backed-up/cofriend/data/db_pickled_new/relational_ped_data_new.p')
    #data = get_2D_data_from_pgsql([4,8,33,35,41], '5')                        
    #pickle.dump(data, open('/home/csunix/visdata/cofriend/data/db_pickled_new/data_2D/cof_4_8_33_35_41_db_2D_cam5.p','w'), 1)
    #data = get_SED_recognitions_from_pgsql([64, 65, 66, 3, 4, 1, 8, 61, 18, 30, 25, 58, 59, 29, 62, 63])
    #data = get_SED_recognitions_timestamps_from_pgsql([1,2,3,4,5,6,7,8,9,16,18,20,25,29,30,58,59,61,62,63,64,65,66])
    #pf = '/home/csunix/visdata/cofriend/working_code/data/db/sed_recognition_timestamps_20110301.p'
    #pickle.dump(data, open(pf, 'w'), 1)
    
    data = get_3D_data_from_pgsql([33, 35, 41, 47, 48, 49], '4')
    #data_dump = '20110124'
    #track_data_file  = '/home/csunix/visdata/cofriend/release/temp/opra_lam/data/db/pickled_new/pgsql_3D_cam5_COF-all_' + data_dump + '.p'
    #opra_rel_file    = '/home/csunix/visdata/cofriend/release/temp/opra_lam/data/db/pickled_new/opra/opra_4_COF-all_' + data_dump + '.p'
    #opraX4_rel_file  = '/home/csunix/visdata/cofriend/release/temp/opra_lam/data/db/pickled_new/opra/opraX_4_COF-all_' + data_dump + '_no_persons.p'
    #opraX4_intv_file = '/home/csunix/visdata/cofriend/release/temp/opra_lam/data/db/pickled_new/opra/opraX_4_intv_COF-all_' + data_dump + '_no_persons.p'
    #opraX4_expr_file = '/home/csunix/visdata/cofriend/release/temp/opra_lam/data/db/pickled_new/opra/opraX_4_expr_COF-all_' + data_dump + '_no_persons.p'
    
    #data = get_3D_data_from_pgsql([1,2,3,4,5,6,7,8,9,16,18,20,29,58,59,61,62,63,64,65,66], '5')
    #pickle.dump(data, open(track_data_file, 'w'))
    #get_opra_rel(track_data_file, opra_rel_file,'4')
    #get_opraX4_rel(opra_rel_file, opraX4_rel_file)    
    #get_opra_intv(opraX4_rel_file, opraX4_intv_file)
    #get_opra_intv_expr(opraX4_intv_file, opraX4_expr_file)
    
    #data_3D_file = '/home/csunix/visdata/cofriend/release/temp/opra_lam/data/db/pickled_new/pgsql_3D_COF-all.p'
    #hist_of_proximity(data_3D_file)
    print 'DONE'
    
    print 'DONE'    
    
 