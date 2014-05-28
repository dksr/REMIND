import os
import sys
from optparse import OptionParser

def ffmpeg_vid2img(argv=None):
    
    if argv == None:
        argv = sys.argv
    if len(argv) == 1:
        sys.argv.append('-help')
        
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-i", "--invid",  dest="in_vid",  default="",  help="input video")
    parser.add_option("-o", "--outdir", dest="out_dir", default="",  help="output directory")
    parser.add_option("-f", "--format", dest="im_format",  default="jpg",  help="output image format (jpg)")
    parser.add_option("-p", "--file_pattern", dest="file_pattern",  default="%05d",  help="file format (%05d)")
    parser.add_option("-s", "--size", dest="size",  default="320:180",  help="image size (640:360)")
    
    # Process command line and config file options
    (options, args) = parser.parse_args(argv)
    
    in_vid    = options.in_vid
    out_dir   = options.out_dir
    im_format = options.im_format
    size      = options.size
    file_pattern = options.file_pattern
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
        
        
    ffmpeg_cmd = 'ffmpeg -i ' + in_vid + ' -s ' + size + ' ' + os.path.join(out_dir, file_pattern + '.' + im_format)
    os.system(ffmpeg_cmd)
    return in_vid
    
def ffmpeg_img2vid(argv=None):
    import tempfile
    
    if argv == None:
        argv = sys.argv
    if len(argv) == 1:
        sys.argv.append('-help')
        
    parser = OptionParser("usage: %prog [options]")
    parser.add_option("-i", "--img_dir",  dest="img_dir",  default="",  help="input video")
    parser.add_option("-o", "--outdir", dest="out_dir", default="",  help="output directory")
    parser.add_option("-f", "--format", dest="im_format",  default="jpg",  help="output image format (jpg)")
    parser.add_option("-p", "--file_pattern", dest="file_pattern",  default="%05d",  help="file format (%05d)")
    parser.add_option("-s", "--start_frame",  dest="start_frame",  default="",  help="Start frame")
    parser.add_option("-e", "--end_frame",  dest="end_frame",  default="",  help="end frame")
    
    # Process command line and config file options
    (options, args) = parser.parse_args(argv)
    
    start_frame = int(options.start_frame)
    end_frame = int(options.end_frame)    
    img_dir    = options.img_dir
    out_dir   = options.out_dir
    im_format = options.im_format
    file_pattern = options.file_pattern
    
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    tmp_output_dir = tempfile.mkdtemp()
    count = 0
    file_names = os.listdir(img_dir)
    file_names.sort()
    for i in file_names:
        frame = int(i.split('.')[0])
        if frame < start_frame or frame > end_frame:
            continue
        cp_cmd = 'cp ' + os.path.join(img_dir, i) + ' ' + os.path.join(tmp_output_dir, '%05d.jpg' %count)
        os.system(cp_cmd)
        count += 1
    
    ffmpeg_cmd = 'ffmpeg -i ' + os.path.join(tmp_output_dir, '%05d.jpg') + ' ' + \
               os.path.join(out_dir, os.path.basename(img_dir) + repr(start_frame) + '_' + repr(end_frame) + '.avi' )
    os.system(ffmpeg_cmd)
    os.rmdir(tmp_output_dir)
    print 'DONE'
    

if __name__ == "__main__":
    import sys
    from multiprocessing import Pool
    
    #ffmpeg_vid2img(sys.argv)
    #ffmpeg_img2vid(sys.argv)
    pool = Pool(processes=10)
    
    args = []
    f = open('/vol/laag/mindseye/videos/Y2/fullpath_vids_similar_to_eval.txt')
    base_out_dir = '/vol/laag/mindseye/videos/Y2/jpegs/vids_similar_to_test_1280_720'
    for line in f:
        if line == '\n':
            continue
        line = line.strip()
        vid_name = line.split('/')[-1]
        if not os.path.isdir(os.path.join(base_out_dir, vid_name)):
            os.makedirs(os.path.join(base_out_dir, vid_name))                    
        args.append(['-i', line, '-s', '1280:720', '-o', os.path.join(base_out_dir, vid_name)])
    result = pool.map(ffmpeg_vid2img, args)
    print '###########################################'
    print 'DONE'    
             
    