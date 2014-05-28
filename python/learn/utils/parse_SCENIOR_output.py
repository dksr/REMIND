""" Parse SCENIOR learned models recognition output
"""

def parse_SCENOIR_output(out_dir):
    import os

    recognitions = {}
    for idir in os.listdir(out_dir):
        print idir
        vid = idir.split('.')[0]
        print vid
        vid = int(vid[3:])
        print vid
        event = idir.split(' - ')[1]
        event = event.replace('-', '_')
        if vid not in recognitions:
            recognitions[vid] = {}
        for ifile in os.listdir(os.path.join(out_dir, idir)):
            intv = get_interval(os.path.join(out_dir, idir, ifile))
            if event in recognitions[vid]:
                recognitions[vid][event].append(intv)
            else:
                recognitions[vid][event] = [intv]
    return recognitions   
                
def get_interval(ifile):
    from datetime import datetime
    
    months_map = {
                  'Jan' :1,
                  'Feb' :2,
                  'Mar' :3,
                  'Apr' :4,
                  'May' :5,
                  'Jun' :6,
                  'Jul' :7,
                  'Aug' :8,
                  'Sep' :9,
                  'Oct' :10,
                  'Nov' :11,
                  'Dec' :12,                  
                 }
    
    ifile_p = open(ifile)
    start_time  = datetime.strptime("2012-12-12 12:12:12", "%Y-%m-%d %H:%M:%S")
    finish_time = datetime.strptime("2000-12-12 12:12:12", "%Y-%m-%d %H:%M:%S")
    for line in ifile_p:
        try:
            time_str = line.split(' : ')[1]
            time_fields = time_str.split()
            # Months is given as name rather than number
            month = months_map[time_fields[1]]
            day   = time_fields[2]
            time  = time_fields[3]
            year  = time_fields[-1]
        except Exception:
            continue
        date_time_str = year + '-' + repr(month) + '-' + day + ' ' + time
        # Find the min and max timestamps in the file and use them as start and finish times
        if line.startswith('   start'):
            start_time = min(start_time, datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S"))
        if line.startswith('   finish'):
            finish_time = max(finish_time, datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S"))

    ifile_p.close()
    return (start_time, finish_time)

if __name__ == '__main__':
    import cPickle as pickle
    
    gt_dir = '/home/csunix/visdata/cofriend/working_code/data/db/GT/'
    recognitions = parse_SCENOIR_output('/usr/not-backed-up/cofriend/data/results_lam_scenoir')
    gt_pickle_file = gt_dir + 'scenoir_learned_models_recognitions.p'
    pickle.dump(recognitions, open(gt_pickle_file, 'w'), 1)
    print 'done'
    