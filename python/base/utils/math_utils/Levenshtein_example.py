from Levenshtein import median

print 'correct string: Levenshtein' 
print 
print 'Garbled:'
f = ['Levnhtein', 'Leveshein', 'Leenshten',
     'Leveshtei', 'Lenshtein', 'Lvenstein',
     'Levenhtin', 'evenshtei']
print f
print 
print 'median string: ', median(f)
