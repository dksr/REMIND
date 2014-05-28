#############################################################################
#   read_utils.py
#
#   Created: 12/08/08
#   Author : Krishna Sandeep Reddy Dubba    
#   Email  : scksrd@leeds.ac.uk
#   Purpose: 
#
#   This program is part of the CO-FRIEND project, partially funded by the
#   European Commission under the 7th Framework Program.
#
#   See http://www.co-friend.net
#
#   (C) University of Leeds - Co-friend Consortium
#############################################################################

"""Reads or unpickles KB from files"""
import os
import cPickle as pickle
from base.hyp import *


def get_KB(file_name, pic=False):
    # file_name supplied is config file name. Just change the extentions
    base_file = file_name
    if not pic:
        # add extensions
        bg_clause = None
        print base_file + '.f'
        pos_ex = read_KB_file(base_file + '.f', pic)
        neg_ex = read_KB_file(base_file + '.n', pic)
        bg_ex  = read_KB_file(base_file + '.b', pic)
        return bg_clause, bg_ex, pos_ex, neg_ex 
   
    pic_kb = read_KB_file(base_file + '.p', pic)
    return pic_kb['bc'], pic_kb['bg'], pic_kb['pos'], pic_kb['neg']  

def read_KB_file(file_name, pic=False):
    # If pickle option is false, read the text files and prepare FOL KB
    if not os.path.exists(file_name):
        print('Warning: ' + file_name +' is missing')
        return None
    if not pic:
        kb = FolKB()
        file = open(file_name)
        lines = []
        count = 1
        for line in file:
            ind = line.find(").")
            if ind > 0 :
                l = line[0:ind+1]
                kb.tell(expr(l))                
        return kb        
        
    # Else unpickle the file and return
    return pickle.load(open(file_name))     

def pickle_KB(file_name, bc, bg_kb, pos_kb, neg_kb=None):
    """Pickles the KB in binary format"""
    kb = {}
    kb['bg'] = bg_kb
    kb['pos'] = pos_kb
    kb['neg'] = neg_kb
    kb['bc'] = bc 
    pickle.dump(kb, open(file_name,'w'), 1)



if __name__ == "__main__":
    kb = read_KB_file('/home/sandy/python/ilp/data/s63.txt')
    print 'over'
    
