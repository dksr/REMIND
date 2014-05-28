"""Provide some widely useful utilities. Safe for "from utils import *".

"""

from __future__ import generators
from _heapq import heappush, heappop
import operator, math, random, copy, sys, os.path, re

try:
    import _bisect as bisect
except ImportError:
    import bisect

#______________________________________________________________________________
# Simple Data Structures: infinity, Dict, Struct

infinity = 1.0e400

def Dict(**entries):  
    """Create a dict out of the argument=value arguments. 
    >>> Dict(a=1, b=2, c=3)
    {'a': 1, 'c': 3, 'b': 2}
    """
    return entries

class DefaultDict(dict):
    """Dictionary with a default value for unknown keys."""
    def __init__(self, default):
        self.default = default

    def __getitem__(self, key):
        if key in self: return self.get(key)
        return self.setdefault(key, copy.deepcopy(self.default))

    def __copy__(self):
        copy = DefaultDict(self.default)
        copy.update(self)
        return copy

class Struct:
    """Create an instance with argument=value slots.
    This is for making a lightweight object whose class doesn't matter."""
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __cmp__(self, other):
        if isinstance(other, Struct):
            return cmp(self.__dict__, other.__dict__)
        else:
            return cmp(self.__dict__, other)

    def __repr__(self):
        args = ['%s=%s' % (k, repr(v)) for (k, v) in vars(self).items()]
        return 'Struct(%s)' % ', '.join(args)

def update(x, **entries):
    """Update a dict; or an object with slots; according to entries.
    >>> update({'a': 1}, a=10, b=20)
    {'a': 10, 'b': 20}
    >>> update(Struct(a=1), a=10, b=20)
    Struct(a=10, b=20)
    """
    if isinstance(x, dict):
        x.update(entries)   
    else:
        x.__dict__.update(entries) 
    return x 

def get_key(idict, ivalue):
    """get key for the given value from a dictionary"""
    for key, value in idict.items():
        if ivalue == value:
            return key

#______________________________________________________________________________
# Functions on Sequences (mostly inspired by Common Lisp)
# NOTE: Sequence functions (count_if, find_if, every, some) take function
# argument first (like reduce, filter, and map).

def dict_reverse(subst_dict):
    """Reverses dictionary keys into values and values into keys.
    Assumes the values are unique.
    """
    reverse_dict = {}
    for key in subst_dict.keys():
        if not isinstance(key, tuple):
            reverse_dict[subst_dict[key]] = key
    return reverse_dict        

def compare_dict_with_list_values(dict_a, dict_b):
    """This is compare function to compare dictionaries where the values
    are lists. Normal dict comparison fails as it does not sort the lists
    before comparison. For other cases using '==' is sufficient."""
    keys_a = sorted(dict_a.keys())
    keys_b = sorted(dict_b.keys())
    if keys_a != keys_b:
        return False
    for key in keys_a:
        if dict_a[key].sort() != dict_b[key].sort():
            return False
    return True	

def flatten(lst):
    """ nested = [('a', 'b', ['c', 'd'], ['a', 'b']), ['e', 'f']]
    flattened = list( flatten(nested) )
    ['a', 'b', 'c', 'd', 'a', 'b', 'e', 'f']
    with flatten() you can do everything you can do with generators,
    like such boring things
    for elem in flatten(nested):
        print elem     
    """
    for elem in lst:
        if type(elem) in (tuple, list):
            for i in flatten(elem):
                yield i
        else:
            yield elem

def make_list(ele):
    """ Returns a list of single element that has ele as the only element"""
    if not isinstance(ele, tuple) and not isinstance(ele, set) and not isinstance(ele, list):
        return [ele]
    else:
        return list(ele)
            
def removeall(item, seq):
    """Return a copy of seq (or string) with all occurences of item removed.
    >>> removeall(3, [1, 2, 3, 3, 2, 1, 3])
    [1, 2, 2, 1]
    >>> removeall(4, [1, 2, 3])
    [1, 2, 3]
    """
    if isinstance(seq, str):
        return seq.replace(item, '')
    else:
        return [x for x in seq if x != item]

def unique(seq):
    """Remove duplicate elements from seq. Assumes hashable elements.
    >>> unique([1, 2, 3, 2, 1])
    [1, 2, 3]
    """
    return list(set(seq))

def product(numbers):
    """Return the product of the numbers.
    >>> product([1,2,3,4])
    24
    """
    return reduce(operator.mul, numbers, 1)

def combinations_from_multiple_lists(a):
    """ Use car_product instead. Need to test which one is faster"""
    r=[[]]
    for x in a:
        if len(x) is not 0:
            t = []
            for y in x:
                for i in r:
                    t.append(i+[y])
            r = t
    return r

def car_product(*args, **kwds):
    """Cartesian Product of lists. Implementation of iterators.product"""
    # car_product(['ABCD', 'xy']) --> Ax Ay Bx By Cx Cy Dx Dy
    # car_product([range(2), repeat=3]) --> 000 001 010 011 100 101 110 111
    pools = map(tuple, args[0]) * kwds.get('repeat', 1)
    result = [[]]
    for pool in pools:
        result = [x+[y] for x in result for y in pool]
    for prod in result:
        yield tuple(prod)

def count_if(predicate, seq):
    """Count the number of elements of seq for which the predicate is true.
    >>> count_if(callable, [42, None, max, min])
    2
    """
    f = lambda count, x: count + (not not predicate(x))
    return reduce(f, seq, 0)

def find_if(predicate, seq):
    """If there is an element of seq that satisfies predicate; return it.
    >>> find_if(callable, [3, min, max])
    <built-in function min>
    >>> find_if(callable, [1, 2, 3])
    """
    for x in seq:
        if predicate(x): return x
    return None

def every(predicate, seq):
    """True if every element of seq satisfies predicate.
    >>> every(callable, [min, max])
    1
    >>> every(callable, [min, 3])
    0
    """
    for x in seq:
        if not predicate(x): return False
    return True

def some(predicate, seq):
    """If some element x of seq satisfies predicate(x), return predicate(x).
    >>> some(callable, [min, 3])
    1
    >>> some(callable, [2, 3])
    0
    """
    for x in seq:
        px = predicate(x)
        if  px: return px
    return False   

def isin(elt, seq):
    """Like (elt in seq), but compares with is, not ==.
    >>> e = []; isin(e, [1, e, 3])
    True
    >>> isin(e, [1, [], 3])
    False
    """
    for x in seq:
        if elt is x: return True
    return False

def most_common(lst):
    """Return the most common element in the list"""
    return max(set(lst), key=lst.count)

#______________________________________________________________________________
# Functions on sequences of numbers
# NOTE: these take the sequence argument first, like min and max,
# and like standard math notation: \sigma (i = 1..n) fn(i)
# A lot of programing is finding the best value that satisfies some condition;
# so there are three versions of argmin/argmax, depending on what you want to
# do with ties: return the first one, return them all, or pick at random.

def mean(values):
    """Computes the arithmetic mean of a list of numbers.

    >>> print mean([20, 30, 70])
    40.0
    """
    return sum(values, 0.0) / len(values)
            
def argmin(seq, fn):
    """Return an element with lowest fn(seq[i]) score; tie goes to first one.
    >>> argmin(['one', 'to', 'three'], len)
    'to'
    """
    best = seq[0]; best_score = fn(best)
    for x in seq:
        x_score = fn(x)
        if x_score < best_score:
            best, best_score = x, x_score
    return best

def argmin_list(seq, fn):
    """Return a list of elements of seq[i] with the lowest fn(seq[i]) scores.
    >>> argmin_list(['one', 'to', 'three', 'or'], len)
    ['to', 'or']
    """
    best_score, best = fn(seq[0]), []
    for x in seq:
        x_score = fn(x)
        if x_score < best_score:
            best, best_score = [x], x_score
        elif x_score == best_score:
            best.append(x)
    return best

def argmin_random_tie(seq, fn):
    """Return an element with lowest fn(seq[i]) score; break ties at random.
    Thus, for all s,f: argmin_random_tie(s, f) in argmin_list(s, f)"""
    best_score = fn(seq[0]); n = 0
    for x in seq:
        x_score = fn(x)
        if x_score < best_score:
            best, best_score = x, x_score; n = 1
        elif x_score == best_score:
            n += 1
            if random.randrange(n) == 0:
                best = x
    return best

def argmax(seq, fn):
    """Return an element with highest fn(seq[i]) score; tie goes to first one.
    >>> argmax(['one', 'to', 'three'], len)
    'three'
    """
    return argmin(seq, lambda x: -fn(x))

def argmax_list(seq, fn):
    """Return a list of elements of seq[i] with the highest fn(seq[i]) scores.
    >>> argmax_list(['one', 'three', 'seven'], len)
    ['three', 'seven']
    """
    return argmin_list(seq, lambda x: -fn(x))

def argmax_random_tie(seq, fn):
    "Return an element with highest fn(seq[i]) score; break ties at random."
    return argmin_random_tie(seq, lambda x: -fn(x))
#______________________________________________________________________________
# Statistical and mathematical functions

def histogram(values, mode=0, bin_function=None):
    """Return a list of (value, count) pairs, summarizing the input values.
    Sorted by increasing value, or if mode=1, by decreasing count.
    If bin_function is given, map it over values first."""
    if bin_function: values = map(bin_function, values)
    bins = {}
    for val in values:
        bins[val] = bins.get(val, 0) + 1
    if mode:
        return sorted(bins.items(), key=lambda x: (x[1],x[0]), reverse=True)
    else:
        return sorted(bins.items())

def log2(x):
    """Base 2 logarithm.
    >>> log2(1024)
    10.0
    """
    return math.log10(x) / math.log10(2)

def mode(values):
    """Return the most common value in the list of values.
    >>> mode([1, 2, 3, 2])
    2
    """
    return histogram(values, mode=1)[0][0]

def median(values):
    """Return the middle value, when the values are sorted.
    If there are an odd number of elements, try to average the middle two.
    If they can't be averaged (e.g. they are strings), choose one at random.
    >>> median([10, 100, 11])
    11
    >>> median([1, 2, 3, 4])
    2.5
    """
    n = len(values)
    values = sorted(values)
    if n % 2 == 1:
        return values[n/2]
    else:
        middle2 = values[(n/2)-1:(n/2)+1]
        try:
            return mean(middle2)
        except TypeError:
            return random.choice(middle2)

def mean(values):
    """Return the arithmetic average of the values."""
    return sum(values) / float(len(values))

def stddev(values, meanval=None):
    """The standard deviation of a set of values.
    Pass in the mean if you already know it."""
    if meanval == None: meanval = mean(values)
    return math.sqrt(sum([(x - meanval)**2 for x in values]) / (len(values)-1))

def dotproduct(X, Y):
    """Return the sum of the element-wise product of vectors x and y.
    >>> dotproduct([1, 2, 3], [1000, 100, 10])
    1230
    """
    return sum([x * y for x, y in zip(X, Y)])

def vector_add(a, b):
    """Component-wise addition of two vectors.
    >>> vector_add((0, 1), (8, 9))
    (8, 10)
    """
    return tuple(map(operator.add, a, b))

def probability(p):
    "Return true with probability p."
    return p > random.uniform(0.0, 1.0)

def num_or_str(x):
    """The argument is a string; convert to a number if possible, or strip it.
    >>> num_or_str('42')
    42
    >>> num_or_str(' 42x ')
    '42x'
    """
    if isnumber(x): return x
    try:
        return int(x) 
    except ValueError:
        try:
            return float(x) 
        except ValueError:
            return str(x).strip() 

def normalize(numbers, total=1.0):
    """Multiply each number by a constant such that the sum is 1.0 (or total).
    >>> normalize([1,2,1])
    [0.25, 0.5, 0.25]
    """
    k = total / sum(numbers)
    return [k * n for n in numbers]

## OK, the following are not as widely useful utilities as some of the other
## functions here, but they do show up wherever we have 2D grids: Wumpus and
## Vacuum worlds, TicTacToe and Checkers, and markov decision Processes.

orientations = [(1,0), (0, 1), (-1, 0), (0, -1)]

def turn_right(orientation):
    return orientations[orientations.index(orientation)-1]

def turn_left(orientation):
    return orientations[(orientations.index(orientation)+1) % len(orientations)]

def distance((ax, ay), (bx, by)):
    "The distance between two (x, y) points."
    return math.hypot((ax - bx), (ay - by))

def distance2((ax, ay), (bx, by)):
    "The square of the distance between two (x, y) points."
    return (ax - bx)**2 + (ay - by)**2

def clip(vector, lowest, highest):
    """Return vector, except if any element is less than the corresponding
    value of lowest or more than the corresponding value of highest, clip to
    those values.
    >>> clip((-1, 10), (0, 0), (9, 9))
    (0, 9)
    """
    return type(vector)(map(min, map(max, vector, lowest), highest))
#______________________________________________________________________________
# Misc Functions

def printf(format, *args): 
    """Format args with the first argument as format string, and write.
    Return the last arg, or format itself if there are no args."""
    sys.stdout.write(str(format) % args)
    return if_(args, args[-1], format)

def caller(n=1):
    """Return the name of the calling function n levels up in the frame stack.
    >>> caller(0)
    'caller'
    >>> def f(): 
    ...     return caller()
    >>> f()
    'f'
    """
    import inspect
    return  inspect.getouterframes(inspect.currentframe())[n][3]

def memoize(fn, slot=None):
    """Memoize fn: make it remember the computed value for any argument list.
    If slot is specified, store result in that slot of first argument.
    If slot is false, store results in a dictionary."""
    if slot:
        def memoized_fn(obj, *args):
            if hasattr(obj, slot):
                return getattr(obj, slot)
            else:
                val = fn(obj, *args)
                setattr(obj, slot, val)
                return val
    else:
        def memoized_fn(*args):
            if not memoized_fn.cache.has_key(args):
                memoized_fn.cache[args] = fn(*args)
            return memoized_fn.cache[args]
        memoized_fn.cache = {}
    return memoized_fn

def if_(test, result, alternative):
    """Like C++ and Java's (test ? result : alternative), except
    both result and alternative are always evaluated. However, if
    either evaluates to a function, it is applied to the empty arglist,
    so you can delay execution by putting it in a lambda.
    >>> if_(2 + 2 == 4, 'ok', lambda: expensive_computation())
    'ok'
    """
    if test:
        if callable(result): return result()
        return result
    else:
        if callable(alternative): return alternative()
        return alternative

def name(object):
    "Try to find some reasonable name for the object."
    return (getattr(object, 'name', 0) or getattr(object, '__name__', 0)
            or getattr(getattr(object, '__class__', 0), '__name__', 0)
            or str(object))

def isnumber(x):
    "Is x a number? We say it is if it has a __int__ method."
    return hasattr(x, '__int__')

def issequence(x):
    "Is x a sequence? We say it is if it has a __getitem__ method."
    return hasattr(x, '__getitem__')

def print_table(table, header=None, sep=' ', numfmt='%g'):
    """Print a list of lists as a table, so that columns line up nicely.
    header, if specified, will be printed as the first row.
    numfmt is the format for all numbers; you might want e.g. '%6.2f'.
    (If you want different formats in differnt columns, don't use print_table.)
    sep is the separator between columns."""
    justs = [if_(isnumber(x), 'rjust', 'ljust') for x in table[0]]
    if header:
        table = [header] + table
    table = [[if_(isnumber(x), lambda: numfmt % x, x)  for x in row]
             for row in table]    
    maxlen = lambda seq: max(map(len, seq))
    sizes = map(maxlen, zip(*[map(str, row) for row in table]))
    for row in table:
        for (j, size, x) in zip(justs, sizes, row):
            print getattr(str(x), j)(size), sep,
        print

def AIMAFile(components, mode='r'):
    "Open a file based at the AIMA root directory."
    import utils
    dir = os.path.dirname(utils.__file__)
    return open(apply(os.path.join, [dir] + components), mode)

def DataFile(name, mode='r'):
    "Return a file in the AIMA /data directory."
    return AIMAFile(['..', 'data', name], mode)


#______________________________________________________________________________
# Queues: Stack, FIFOQueue, PriorityQueue

class Queue:
    """Queue is an abstract class/interface. There are three types:
        Stack(): A Last In First Out Queue.
        FIFOQueue(): A First In First Out Queue.
        PriorityQueue(lt): Queue where items are sorted by lt, (default <).
    Each type supports the following methods and functions:
        q.append(item)  -- add an item to the queue
        q.extend(items) -- equivalent to: for item in items: q.append(item)
        q.pop()         -- return the top item from the queue
        len(q)          -- number of items in q (also q.__len())
    Note that isinstance(Stack(), Queue) is false, because we implement stacks
    as lists.  If Python ever gets interfaces, Queue will be an interface."""

    def __init__(self): 
        abstract

    def extend(self, items):
        for item in items: self.append(item)
        #[self.append(item) for item in items]
        
def Stack():
    """Return an empty list, suitable as a Last-In-First-Out Queue."""
    return []

class FIFOQueue(Queue):
    """A First-In-First-Out Queue."""
    def __init__(self):
        self.A = []; self.start = 0
    def append(self, item):
        self.A.append(item)
    def __len__(self):
        return len(self.A) - self.start
    def extend(self, items):
        self.A.extend(items)     
    def pop(self):        
        e = self.A[self.start]
        self.start += 1
        if self.start > 5 and self.start > len(self.A)/2:
            self.A = self.A[self.start:]
            self.start = 0
        return e

class PriorityQueue(Queue):
    """A queue in which the minimum (or maximum) element (as determined by f and
    order) is returned first. If order is min, the item with minimum f(x) is
    returned first; if order is max, then it is the item with maximum f(x)."""
    def __init__(self, order=min, f=lambda x: x):
        update(self, A=[], order=order, f=f)
    def append(self, item):
        bisect.insort(self.A, (self.f(item), item))
    def __len__(self):
        return len(self.A)
    def pop(self):
        if self.order == min:
            return self.A.pop(0)[1]
        else:
            return self.A.pop()[1]
 
class PQueue_heapq(Queue):
    """A queue in which the minimum element (as determined by f) is returned first.
    Uses the heapq module of python."""
    def __init__(self, order=min, f=lambda x: x):
        update(self, A=[], order=order, f=f)
    def append(self, item):
        if self.order == max:
            # If order is max, negate the score
            heappush(self.A, (-self.f(item), item))
        else:    
            heappush(self.A, (self.f(item), item))
    def __len__(self):
        return len(self.A)
    def pop(self):
        # Always return the least scored element
        return heappop(self.A)[1]
    
## Fig: The idea is we can define things like Fig[3,10] later.
## Alas, it is Fig[3,10] not Fig[3.10], because that would be the same as Fig[3.1]
Fig = {} 

#______________________________________________________________________________
# Support for doctest

def ignore(x): None

def random_tests(text):
    """Some functions are stochastic. We want to be able to write a test
    with random output.  We do that by ignoring the output."""
    def fixup(test): 
        if " = " in test:
            return ">>> " + test
        else:
            return ">>> ignore(" + test + ")"
    tests =  re.findall(">>> (.*)", text)
    return '\n'.join(map(fixup, tests))

#______________________________________________________________________________

def pp(plist):
    """Print list in a nice way
    """
    for item in plist:
        print item

def ppd(pdict):
    """Print dictionary in a nice way
    """
    for key in pdict.keys():
        print key, ': ', pdict[key] 

#______________________________________________________________________________

__doc__ += """
>>> d = DefaultDict(0) 
>>> d['x'] += 1
>>> d['x']
1

>>> d = DefaultDict([])
>>> d['x'] += [1]
>>> d['y'] += [2]
>>> d['x']
[1]

>>> s = Struct(a=1, b=2)
>>> s.a
1
>>> s.a = 3
>>> s
Struct(a=3, b=2)

>>> def is_even(x): 
...     return x % 2 == 0
>>> sorted([1, 2, -3]) 
[-3, 1, 2]
>>> sorted(range(10), key=is_even)
[1, 3, 5, 7, 9, 0, 2, 4, 6, 8]
>>> sorted(range(10), lambda x,y: y-x) 
[9, 8, 7, 6, 5, 4, 3, 2, 1, 0]

>>> removeall(4, []) 
[]
>>> removeall('s', 'This is a test. Was a test.') 
'Thi i a tet. Wa a tet.'
>>> removeall('s', 'Something') 
'Something'
>>> removeall('s', '') 
''

>>> list(reversed([])) 
[]

>>> count_if(is_even, [1, 2, 3, 4]) 
2
>>> count_if(is_even, []) 
0

>>> argmax([1], lambda x: x*x) 
1
>>> argmin([1], lambda x: x*x) 
1


# Test of memoize with slots in structures
>>> countries = [Struct(name='united states'), Struct(name='canada')]

# Pretend that 'gnp' was some big hairy operation:
>>> def gnp(country): 
...     print 'calculating gnp ...'
...     return len(country.name) * 1e10

>>> gnp = memoize(gnp, '_gnp')
>>> map(gnp, countries)
calculating gnp ...
calculating gnp ...
[130000000000.0, 60000000000.0]
>>> countries
[Struct(_gnp=130000000000.0, name='united states'), Struct(_gnp=60000000000.0, name='canada')]

# This time we avoid re-doing the calculation
>>> map(gnp, countries) 
[130000000000.0, 60000000000.0]

# Test Queues:
>>> nums = [1, 8, 2, 7, 5, 6, -99, 99, 4, 3, 0]
>>> def qtest(q): 
...     return [q.extend(nums), [q.pop() for i in range(len(q))]][1]

>>> qtest(Stack()) 
[0, 3, 4, 99, -99, 6, 5, 7, 2, 8, 1]

>>> qtest(FIFOQueue()) 
[1, 8, 2, 7, 5, 6, -99, 99, 4, 3, 0]

>>> qtest(PriorityQueue(min)) 
[-99, 0, 1, 2, 3, 4, 5, 6, 7, 8, 99]

>>> qtest(PriorityQueue(max)) 
[99, 8, 7, 6, 5, 4, 3, 2, 1, 0, -99]

>>> qtest(PriorityQueue(min, abs)) 
[0, 1, 2, 3, 4, 5, 6, 7, 8, -99, 99]

>>> qtest(PriorityQueue(max, abs)) 
[99, -99, 8, 7, 6, 5, 4, 3, 2, 1, 0]

>>> vals = [100, 110, 160, 200, 160, 110, 200, 200, 220]
>>> histogram(vals) 
[(100, 1), (110, 2), (160, 2), (200, 3), (220, 1)]
>>> histogram(vals, 1) 
[(200, 3), (160, 2), (110, 2), (220, 1), (100, 1)]
>>> histogram(vals, 1, lambda v: round(v, -2)) 
[(200.0, 6), (100.0, 3)]

>>> log2(1.0) 
0.0

>>> def fib(n): 
...     return (n<=1 and 1) or (fib(n-1) + fib(n-2))

>>> fib(9)
55

# Now we make it faster:
>>> fib = memoize(fib)
>>> fib(9) 
55

>>> q = Stack()
>>> q.append(1)
>>> q.append(2)
>>> q.pop(), q.pop()
(2, 1)

>>> q = FIFOQueue()
>>> q.append(1)
>>> q.append(2)
>>> q.pop(), q.pop()
(1, 2)


>>> abc = set('abc')
>>> bcd = set('bcd')
>>> 'a' in abc
True
>>> 'a' in bcd
False
>>> list(abc.intersection(bcd))
['c', 'b']
>>> list(abc.union(bcd))
['a', 'c', 'b', 'd']

## From "What's new in Python 2.4", but I added calls to sl

>>> def sl(x):
...     return sorted(list(x))


>>> a = set('abracadabra')                  # form a set from a string
>>> 'z' in a                                # fast membership testing
False
>>> sl(a)                                   # unique letters in a
['a', 'b', 'c', 'd', 'r']

>>> b = set('alacazam')                     # form a second set
>>> sl(a - b)                               # letters in a but not in b
['b', 'd', 'r']
>>> sl(a | b)                               # letters in either a or b
['a', 'b', 'c', 'd', 'l', 'm', 'r', 'z']
>>> sl(a & b)                               # letters in both a and b
['a', 'c']
>>> sl(a ^ b)                               # letters in a or b but not both
['b', 'd', 'l', 'm', 'r', 'z']


>>> a.add('z')                              # add a new element
>>> a.update('wxy')                         # add multiple new elements
>>> sl(a)  
['a', 'b', 'c', 'd', 'r', 'w', 'x', 'y', 'z']
>>> a.remove('x')                           # take one element out
>>> sl(a)
['a', 'b', 'c', 'd', 'r', 'w', 'y', 'z']

"""

if __name__ == '__main__':
    a = [1]
    b = [2]
    def f(x):
        return x
    data = [(-1, 'J'), (-4, 'N'), (-3, 'H'), (-2, 'O')]
    p = PQueue_heapq(min, f)
    for i in data:
        p.append(i)
    while p:
        print p.pop()[1]
    
    #s = car_product(a, b)
    print 'hi'
