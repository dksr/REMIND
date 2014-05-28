import re
from pyswip import *
import sys
sys.path.append('/home/csunix/dksreddy/work/base/src/python')
from deepstr import deep_str

progol_file = '/home/csunix/dksreddy/work/base/src/python/ilp/data/s63_4.b'
pf = open(progol_file)

p = Prolog()

assertz  = Functor("assertz")
sur      = Functor("sur", 3)
con      = Functor("con", 3)
dis      = Functor("dis", 3)
intvf     = Functor("intv", 2)
objf      = Functor("obj", 1)
zonef     = Functor("zone", 1)
before   = Functor("before", 2)
overlaps = Functor("overlaps", 2)
meets    = Functor("meets", 2)
finishes = Functor("finishes", 2)
during   = Functor("during", 2)

# patterns for file parsing
obj_p = re.compile('obj\((\w*)\).')
zon_p = re.compile('zone\((\w*)\).')
int_p = re.compile('int\((\d*),(\d*)\).')
bef_p = re.compile('before\(int\((\d*),(\d*)\),int\((\d*),(\d*)\)\).')
ovl_p = re.compile('overlaps\(int\((\d*),(\d*)\),int\((\d*),(\d*)\)\).')
dur_p = re.compile('during\(int\((\d*),(\d*)\),int\((\d*),(\d*)\)\).')
fin_p = re.compile('finishes\(int\((\d*),(\d*)\),int\((\d*),(\d*)\)\).')
con_p = re.compile('con\((\w*), (\w*), int\((\d*),(\d*)\)\).')
sur_p = re.compile('sur\((\w*), (\w*), int\((\d*),(\d*)\)\).')
dis_p = re.compile('dis\((\w*), (\w*), int\((\d*),(\d*)\)\).')

debug_p = re.compile('before\(int\(1392,1392\),int\(1440,1488\)\).')

for line in pf:
    # if interval line matches
    #m = int_p.match(line)
    #if m:
    #    call(assertz(intvf(m.group(1), m.group(2))))
    #    continue
        
    # if line starting with 'before' matches    
    print line
    m = debug_p.match(line)
    if m:
        #before(int(1392,1392),int(1440,1488)). 
        print 'gotit'
        m2 = bef_p.match(line)
        intv_1 = intvf(m2.group(1), m2.group(2))
        intv_2 = intvf(m2.group(3), m2.group(4))
#        X = Variable()
#        Y = Variable()
#        q = Query(before(X, Y))
#        while q.nextSolution():
#            i += 1
#            print '('+str(i)+")",
#            
#            if type(X.value) is Functor:
#                print X.value.name, deep_str(X.value.args) 
#            else:
#                print deep_str(X.value), i
#                #print X.value, i
#                
#            if type(Y.value) is Functor:
#                print Y.value.name, deep_str(Y.value.args) 
#            else:
#                print deep_str(Y.value)
#        q.closeQuery()
        call(assertz(before(intv_1, intv_2)))
        print 'over'
        continue
        
    m = bef_p.match(line)
    if m:
        # Get interval string 
        intv_1 = intvf(m.group(1), m.group(2))
        intv_2 = intvf(m.group(3), m.group(4))
        call(assertz(before(intv_1, intv_2)))
        print 'done'
        continue

    m = dur_p.match(line)
    if m:
        intv_1 = intvf(m.group(1), m.group(2))
        intv_2 = intvf(m.group(3), m.group(4))
        call(assertz(during(intv_1, intv_2)))
        print 'done'
        continue

    m = ovl_p.match(line)
    if m:
        intv_1 = intvf(m.group(1), m.group(2))
        intv_2 = intvf(m.group(3), m.group(4))
        call(assertz(overlaps(intv_1, intv_2)))
        print 'done'
        continue    

    m = fin_p.match(line)
    if m:
        intv_1 = intvf(m.group(1), m.group(2))
        intv_2 = intvf(m.group(3), m.group(4))
        call(assertz(before(intv_1, intv_2)))
        print 'done'
        continue    

#    m = sur_p.match(line)
#    if m:
#        zone = zonef(m.group(1))
#        obj  = objf(m.group(2))
#        intv = intvf(m.group(3), m.group(4))
#        call(assertz(sur(zone, obj, intv)))
#        continue
#    
#    m = con_p.match(line)
#    if m:
#        zone = zonef(m.group(1))
#        obj  = objf(m.group(2))
#        intv = intvf(m.group(3), m.group(4))
#        call(assertz(con(zone, obj, intv)))
#        continue
#
#    m = dis_p.match(line)
#    if m:
#        zone = zonef(m.group(1))
#        obj  = objf(m.group(2))
#        intv = intvf(m.group(3), m.group(4))
#        call(assertz(dis(zone, obj, intv)))
#        continue

    #m = obj_p.match(line)
    #if m:
    #   call(assertz(objf(m.group(1))))
    #    continue
    
    #m = zon_p.match(line)
    #if m:
    #    call(assertz(zonef(m.group(1))))
    #    continue
    
pf.close()
print 'hi'
print 'hi'
