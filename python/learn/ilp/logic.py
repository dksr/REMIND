#############################################################################
#
#   Author   : Krishna Sandeep Reddy Dubba
#   Email    : scksrd@leeds.ac.uk
#   Institute: University of Leeds, UK
#
#############################################################################

"""Most of the code taken from AIMA book code
Representations and Inference for Logic

Covers both Propositional and First-Order Logic. First we have four
important data types:

    KB            Abstract class holds a knowledge base of logical expressions
    Expr          A logical expression
    substitution  Implemented as a dictionary of var:value pairs, {x:1, y:x}

Be careful: some functions take an Expr as argument, and some take a KB.

A few functions:

    unify            Do unification of two FOL sentences
"""

from __future__ import generators
import os
import re
import sys

# Append lib_dir to PYTHONPATH
MAIN_CODE_DIR = os.environ['MAIN_CODE_DIR']
py_ver = repr(sys.version_info.major) + '.' + repr(sys.version_info.minor)
lib_dir = os.path.join(MAIN_CODE_DIR, 'lib', 'python' + py_ver, 'site-packages')
sys.path.append(lib_dir)
    
from base.utils.base_utils import *


# TO DO LIST:
# BUG at Line 574 (not generic but works for current data).
#______________________________________________________________________________

class KB:
    """A Knowledge base to which you can tell and ask sentences.
    To create a KB, first subclass this class and implement
    tell, ask_generator, and retract.  Why ask_generator instead of ask?  
    The book is a bit vague on what ask means --
    For a Propositional Logic KB, ask(P & Q) returns True or False, but for an
    FOL KB, something like ask(Brother(x, y)) might return many substitutions
    such as {x: Cain, y: Abel}, {x: Abel, y: Cain}, {x: George, y: Jeb}, etc.  
    So ask_generator generates these one at a time, and ask either returns the
    first one or returns False."""

    def __init__(self, sentence=None):
        abstract

    def tell(self, sentence): 
        "Add the sentence to the KB"
        abstract

    def ask(self, query):
        """Ask returns a substitution that makes the query true, or
        it returns False. It is implemented in terms of ask_generator."""
        try: 
            return self.ask_generator(query).next()
        except StopIteration:
            return False

    def ask_generator(self, query): 
        "Yield all the substitutions that make query true."
        abstract

    def retract(self, sentence):
        "Remove the sentence from the KB"
        abstract

#______________________________________________________________________________
    
class Expr:
    """A symbolic mathematical expression.  We use this class for logical
    expressions, and for terms within logical expressions. In general, an
    Expr has an op (operator) and a list of args.  The op can be:
      Null-ary (no args) op:
        A number, representing the number itself.  (e.g. Expr(42) => 42)
        A symbol, representing a variable or constant (e.g. Expr('F') => F)
      Unary (1 arg) op:
        '~', '-', representing NOT, negation (e.g. Expr('~', Expr('P')) => ~P)
      Binary (2 arg) op:
        '>>', '<<', representing forward and backward implication
        '+', '-', '*', '/', '**', representing arithmetic operators
        '<', '>', '>=', '<=', representing comparison operators
        '<=>', '^', representing logical equality and XOR
      N-ary (0 or more args) op:
        '&', '|', representing conjunction and disjunction
        A symbol, representing a function term or FOL proposition

    Exprs can be constructed with operator overloading: if x and y are Exprs,
    then so are x + y and x & y, etc.  Also, if F and x are Exprs, then so is 
    F(x); it works by overloading the __call__ method of the Expr F.  Note 
    that in the Expr that is created by F(x), the op is the str 'F', not the 
    Expr F.   See http://www.python.org/doc/current/ref/specialnames.html 
    to learn more about operator overloading in Python.

    WARNING: x == y and x != y are NOT Exprs.  The reason is that we want
    to write code that tests 'if x == y:' and if x == y were the same
    as Expr('==', x, y), then the result would always be true; not what a
    programmer would expect.  But we still need to form Exprs representing
    equalities and disequalities.  We concentrate on logical equality (or
    equivalence) and logical disequality (or XOR).  You have 3 choices:
        (1) Expr('<=>', x, y) and Expr('^', x, y)
            Note that ^ is bitwose XOR in Python (and Java and C++)
        (2) expr('x <=> y') and expr('x =/= y').  
            See the doc string for the function expr.
        (3) (x % y) and (x ^ y).
            It is very ugly to have (x % y) mean (x <=> y), but we need
            SOME operator to make (2) work, and this seems the best choice.

    WARNING: if x is an Expr, then so is x + 1, because the int 1 gets
    coerced to an Expr by the constructor.  But 1 + x is an error, because
    1 doesn't know how to add an Expr.  (Adding an __radd__ method to Expr
    wouldn't help, because int.__add__ is still called first.) Therefore,
    you should use Expr(1) + x instead, or ONE + x, or expr('1 + x').
    """

    def __init__(self, op, *args):
        "Op is a string or number; args are Exprs (or are coerced to Exprs)."
        # To make this constructor accept lists and tuples of arguments
        if len(args) == 1:
            if isinstance(args[0], tuple):
                args = args[0]
            elif isinstance(args[0], list):
                args = args[0]
        if isinstance(op, str) or (isnumber(op) and not args):
            if len(args) == 1 and isinstance(args[0], Expr) and len(args[0].args) != 0:
                self.op = op + '::' + args[0].op
                args = args[0].args
            else:    
                self.op = num_or_str(op)
        elif isinstance(op, list):
            # Assumes each element in the op_list is string
            self.op = '::'.join(op)            
        else:            
            raise AssertionError('Wrong type while constructing expression')
        self.args = map(expr, args) ## Coerce args to Exprs
    
    def get_string(self):    
        return Expr.__repr__(self)

    def __call__(self, *args):
        """Self must be a symbol with no args, such as Expr('F').  Create a new
        Expr with 'F' as op and the args as arguments."""
        assert is_symbol(self.op) and not self.args
        return Expr(self.op, *args)

    def __repr__(self):
        "Show something like 'P' or 'P(x, y)', or '~P' or '(P | Q | R)'"
        if len(self.args) == 0: # Constant or proposition with arity 0
            return str(self.op)
        elif is_symbol(self.op): # Functional or Propositional operator
            op_list = self.op.split('::')
            if len(op_list) is 1:
                return '%s(%s)' % (self.op, ','.join(map(repr, self.args)))
            else:
                op_str = '('.join(op_list)
                expr_str = '%s(%s' % (op_str, ','.join(map(repr, self.args)))
                return expr_str + ')' * len(op_list)
        elif len(self.args) == 1: # Prefix operator
            return self.op + repr(self.args[0])
        else: # Infix operator
            return '(%s)' % (' '+self.op+' ').join(map(repr, self.args))

    def __eq__(self, other):
        """x and y are equal iff their ops and args are equal."""
        return (other is self) or (isinstance(other, Expr) 
            and self.op == other.op and self.args == other.args)

    def __hash__(self):
        "Need a hash method so Exprs can live in dicts."
        return hash(self.op) ^ hash(tuple(self.args))

    # See http://www.python.org/doc/current/lib/module-operator.html
    # Not implemented: not, abs, pos, concat, contains, *item, *slice
    def __lt__(self, other):     return Expr('<',  self, other)
    def __le__(self, other):     return Expr('<=', self, other)
    def __ge__(self, other):     return Expr('>=', self, other)
    def __gt__(self, other):     return Expr('>',  self, other)
    def __add__(self, other):    return Expr('+',  self, other)
    def __sub__(self, other):    return Expr('-',  self, other)
    def __and__(self, other):    return Expr('&',  self, other)
    def __div__(self, other):    return Expr('/',  self, other)
    def __truediv__(self, other):return Expr('/',  self, other)
    def __invert__(self):        return Expr('~',  self)
    def __lshift__(self, other): return Expr('<<', self, other)
    def __rshift__(self, other): return Expr('>>', self, other)
    def __mul__(self, other):    return Expr('*',  self, other)
    def __neg__(self):           return Expr('-',  self)
    def __or__(self, other):     return Expr('|',  self, other)
    def __pow__(self, other):    return Expr('**', self, other)
    def __xor__(self, other):    return Expr('^',  self, other)
    def __mod__(self, other):    return Expr('<=>',  self, other) ## (x % y)
    


def expr(s):
    """Create an Expr representing a logic expression by parsing the input
    string. Symbols and numbers are automatically converted to Exprs.
    In addition you can use alternative spellings of these operators:
      'x ==> y'   parses as   (x >> y)    # Implication
      'x <== y'   parses as   (x << y)    # Reverse implication
      'x <=> y'   parses as   (x % y)     # Logical equivalence
      'x =/= y'   parses as   (x ^ y)     # Logical disequality (xor)
    But BE CAREFUL; precedence of implication is wrong. expr('P & Q ==> R & S')
    is ((P & (Q >> R)) & S); so you must use expr('(P & Q) ==> (R & S)').
    >>> expr('P <=> Q(1)')
    (P <=> Q(1))
    >>> expr('P & Q | ~R(x, F(x))')
    ((P & Q) | ~R(x, F(x)))
    """
    if isinstance(s, Expr): return s
    if isnumber(s): return Expr(s)
    if isinstance(s, list):
        return map(expr, s)
    ## Replace the alternative spellings of operators with canonical spellings
    s = s.replace('==>', '>>').replace('<==', '<<')
    s = s.replace('<=>', '%').replace('=/=', '^')
    ## Replace a symbol or number, such as 'P' with 'Expr("P")'
    # Added $+- to the list. These are useful for handling mode declarations.
    s = re.sub(r'([a-zA-Z0-9_.$+-]+)', r'Expr("\1")', s)
    ## Now eval the string.  (A security hole; do not use with an adversary.)
    print s
    return eval(s, {'Expr':Expr})
    
    #if s.find(',') != -1 or s.find('(') != -1:
        #return eval(s, {'Expr':Expr})
    #else:
        ## Split the string using '(' and all the substrings except the last one are functors
        #functors = s.split('(')[:-1]
        #arg      = s.split('(')[-1].split(')')[0]
        #return Expr('::'.join(functors), arg)
        

def is_symbol(s):
    "A string s is a symbol if it starts with an alphabetic char."
    return isinstance(s, str) and len(s) != 0 and s[0].isalpha()

def is_var_symbol(s):
    "A logic variable symbol is an initial-lowercase string."
    #return is_symbol(s) and s[0].islower()
    return is_symbol(s) and s[0].isupper()

def is_prop_symbol(s):
    """A proposition logic symbol is an initial-uppercase string other than
    TRUE or FALSE."""
    #return is_symbol(s) and s[0].isupper() and s != 'TRUE' and s != 'FALSE'
    return is_symbol(s) and s[0].islower()

def is_positive(s):
    """s is an unnegated logical expression
    >>> is_positive(expr('F(A, B)'))
    True
    >>> is_positive(expr('~F(A, B)'))
    False
    """
    return s.op != '~'

def is_negative(s):
    """s is a negated logical expression
    >>> is_negative(expr('F(A, B)'))
    False
    >>> is_negative(expr('~F(A, B)'))
    True
    """
    return s.op == '~'

def is_literal(s):
    """s is a FOL literal
    >>> is_literal(expr('~F(A, B)'))
    True
    >>> is_literal(expr('F(A, B)'))
    True
    >>> is_literal(expr('F(A, B) & G(B, C)'))
    False
    """
    return is_symbol(s.op) or (s.op == '~' and is_literal(s.args[0]))

def literals(s):
    """returns the list of literals of logical expression s.
    >>> literals(expr('F(A, B)'))
    [F(A, B)]
    >>> literals(expr('~F(A, B)'))
    [~F(A, B)]
    >>> literals(expr('(F(A, B) & G(B, C)) ==> R(A, C)'))
    [F(A, B), G(B, C), R(A, C)]
    """
    op = s.op
    if op in set(['&', '|', '<<', '>>', '%', '^']):
        result = []
        for arg in s.args:
            result.extend(literals(arg))
        return result
    elif is_literal(s):
        return [s]
    else:
        return []

def variables(s):
    """returns the set of variables in logical expression s.
    >>> ppset(variables(F(x, A, y)))
    set([x, y])
    >>> ppset(variables(expr('F(x, x) & G(x, y) & H(y, z) & R(A, z, z)')))
    set([x, y, z])
    """
    # Will not work for secong order logic
    #if is_literal(s):
    #    return set([v for v in s.args if is_variable(v)])
    #else:
    if is_variable(s):
        return set([s])
    else:
        vars = set([])
        for arg in s.args:
            vars = vars.union(variables(arg))
        return vars

def is_definite_clause(s):
    """returns True for exprs s of the form A & B & ... & C ==> D,
    where all literals are positive.  In clause form, this is
    ~A | ~B | ... | ~C | D, where exactly one clause is positive.
    >>> is_definite_clause(expr('Farmer(Mac)'))
    True
    >>> is_definite_clause(expr('~Farmer(Mac)'))
    False
    >>> is_definite_clause(expr('(Farmer(f) & Rabbit(r)) ==> Hates(f, r)'))
    True
    >>> is_definite_clause(expr('(Farmer(f) & ~Rabbit(r)) ==> Hates(f, r)'))
    False
    """
    if s is None: 
        return False
    op = s.op
    return (is_symbol(op) or
            (op == '>>' and every(is_positive, literals(s))))


## Useful constant Exprs used in examples and code:
TRUE, FALSE, ZERO, ONE, TWO = map(Expr, ['TRUE', 'FALSE', 0, 1, 2]) 
#A, B, C, F, G, P, Q  = map(Expr, 'ABCFGPQ')
#built_in_vars = a, b, c, d, e, f, g, h, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z = map(Expr, 'abcdefghlmnopqrstuvwxyz')
built_in_vars = A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z = map(Expr, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
#______________________________________________________________________________

def conjuncts(s):
    """Return a list of the conjuncts in the sentence s.
    >>> conjuncts(A & B)
    [A, B]
    >>> conjuncts(A | B)
    [(A | B)]
    """
    if isinstance(s, Expr) and s.op == '&': 
        return s.args
    else:
        return [s]

def disjuncts(s):
    """Return a list of the disjuncts in the sentence s.
    >>> disjuncts(A | B)
    [A, B]
    >>> disjuncts(A & B)
    [(A & B)]
    """
    if isinstance(s, Expr) and s.op == '|': 
        return s.args
    else:
        return [s]

#______________________________________________________________________________             

def literal_symbol(literal):
    """The symbol in this literal (without the negation).
    >>> literal_symbol(P)
    P
    >>> literal_symbol(~P)
    P
    """
    if literal.op == '~':
        return literal.args[0]
    else:
        return literal
#______________________________________________________________________________

def unify(x, y, s):
    """Unify expressions x,y with substitution s; return a substitution that
    would make x,y equal, or None if x,y can not unify. x and y can be
    variables (e.g. Expr('x')), constants, lists, or Exprs. [Fig. 9.1]
    >>> ppsubst(unify(x + y, y + C, {}))
    {x: y, y: C}
    """
    if s == None:
        return None
    elif x == y:
        return s
    elif is_variable(x):
        return unify_var(x, y, s)
    elif is_variable(y):
        return unify_var(y, x, s)
    elif isinstance(x, Expr) and isinstance(y, Expr):
        return unify(x.args, y.args, unify(x.op, y.op, s))
    elif isinstance(x, str) or isinstance(y, str) or not x or not y:
        # orig. return if_(x == y, s, None) but we already know x != y
        return None
    elif issequence(x) and issequence(y) and len(x) == len(y):
        # Assert neither x nor y is []
        return unify(x[1:], y[1:], unify(x[0], y[0], s))
    else:
        return None

def is_variable(x):
    "A variable is an Expr with no args and a uppercase symbol as the op."
    return isinstance(x, Expr) and not x.args and is_var_symbol(x.op)

def unify_var(var, x, s):
    if var in s:
        return unify(s[var], x, s)
    elif occur_check(var, x, s):
        return None
    else:
        return extend(s, var, x)

def occur_check(var, x, s):
    """Return true if variable var occurs anywhere in x
    (or in subst(s, x), if s has a binding for x)."""

    if var == x:
        return True
    elif is_variable(x) and s.has_key(x):
        return occur_check(var, s[x], s) # fixed
    # What else might x be?  an Expr, a list, a string?
    elif isinstance(x, Expr):
        # Compare operator and arguments
        return (occur_check(var, x.op, s) or
                occur_check(var, x.args, s))
    elif isinstance(x, list) and x != []:
        # Compare first and rest
        return (occur_check(var, x[0], s) or
                occur_check(var, x[1:], s))
    else:
        # A variable cannot occur in a string
        return False
    
    #elif isinstance(x, Expr):
    #    return var.op == x.op or occur_check(var, x.args)
    #elif not isinstance(x, str) and issequence(x):
    #    for xi in x:
    #        if occur_check(var, xi): return True
    #return False

def extend(s, var, val):
    """Copy the substitution s and extend it by setting var to val;
    return copy.
    
    >>> ppsubst(extend({x: 1}, y, 2))
    {x: 1, y: 2}
    """
    s2 = s.copy()
    s2[var] = val
    return s2
    
def subst(s, x):
    """Substitute the substitution s into the expression x.
    >>> subst({x: 42, y:0}, F(x) + y)
    (F(42) + 0)
    """
    if s is None or len(s) is 0:
        return x
    elif isinstance(x, list): 
        return [subst(s, xi) for xi in x]
    elif isinstance(x, tuple): 
        return tuple([subst(s, xi) for xi in x])
    elif not isinstance(x, Expr): 
        return x
    elif is_var_symbol(x.op):
        if s == None:
            return x
        elif len(x.args) > 0:
            return Expr(x.op, *[subst(s, arg) for arg in x.args])
        else:
            return s.get(x, x)
    # This is for numbers (or numerical constants)        
    elif isnumber(x.op):
        # return s.get(x) if available else return x.op
        # This is because most of the times s will contain Expr as keys.
        # Rarely it will have normal constants as keys
        return s.get(x, x.op)
    elif is_prop_symbol(x.op) and len(x.args) == 0:
        # Some propositional constant or symbol
        return s.get(x, x)
    elif x in s:
        # If expression has entry in the dict, return corresponding value
        return s[x]
    else: 
        return Expr(x.op, *[subst(s, arg) for arg in x.args])
   
def pyswip_subst(s, x):   
    """Use this when s is obtained using pyswip, because the keys 
    of s are string repr of variables. Normally they are expressions
    if using python version of aima. 
    Substitute the substitution s into the expression x.
    >>> subst({'x': 42, 'y':0}, F(x) + y)
    (F(42) + 0)
    """
    if s is None or len(s) is 0:
        return x
    elif isinstance(x, list): 
        return [pyswip_subst(s, xi) for xi in x]
    elif isinstance(x, tuple): 
        return tuple([pyswip_subst(s, xi) for xi in x])
    elif not isinstance(x, Expr): 
        return x
    elif is_var_symbol(x.op):
        if s == None:
            return x
        elif len(x.args) > 0:
            return Expr(x.op, *[pyswip_subst(s, arg) for arg in x.args])
        elif x.op in s:
            # If string repr of expression has entry in the dict, return corresponding value
            return s[x.op]
        else:
            return s.get(x, x)
    # This is for numbers (or numerical constants)        
    elif isnumber(x.op):
        # return s.get(x) if available else return x.op
        # This is because most of the times s will contain Expr as keys.
        # Rarely it will have normal constants as keys
        return s.get(x, x.op)
    elif is_prop_symbol(x.op) and len(x.args) == 0:
        # Some propositional constant or symbol
        return s.get(x, x.op)
    elif x in s:
        # If expression has entry in the dict, return corresponding value
        return s[x]
    else: 
        return Expr(x.op, *[pyswip_subst(s, arg) for arg in x.args])
    
def lgg_subst(s, x):
    """Substitute the substitution s into the expression x.
    >>> subst({x: 42, y:0}, F(x) + y)
    (F(42) + 0)
    """
    if isinstance(x, list): 
        return [lgg_subst(s, xi) for xi in x]
    elif isinstance(x, tuple): 
        return tuple([lgg_subst(s, xi) for xi in x])
    elif not isinstance(x, Expr): 
        return x
    elif is_var_symbol(x.op):
        if s == None:
            return x
        elif len(x.args) > 0:
            return Expr(x.op, *[lgg_subst(s, arg) for arg in x.args])
        else:
            for key in s.keys():
                if isinstance(key, tuple) and x in key:
                    return s.get(key, x) 
            
    # This is for numbers (or numerical constants)        
    elif isnumber(x.op):
        # return s.get(x) if available else return x.op
        # This is because most of the times s will contain Expr as keys.
        # Rarely it will have normal constants as keys
        return s.get(x, x.op)
    elif is_prop_symbol(x.op) and len(x.args) == 0:
        # Some propositional constant or symbol
        for key in s.keys():
            if isinstance(key, tuple) and x in key:
                return s.get(key, x.op)
        
    elif x in s:
        # If expression has entry in the dict, return corresponding value
        return s[x]
    else:
        # keys in s are typles that might have x
        for key in s.keys():
            if isinstance(key, tuple) and x in key:
                return s.get(key, x) 
        # If everything fails, this is the case    
        return Expr(x.op, *[lgg_subst(s, arg) for arg in x.args])
    
def standardize_apart(sentence, dic={}):
    """Replace all the variables in sentence with new variables.
    >>> e = expr('F(a, b, c) & G(c, A, 23)')
    >>> len(variables(standardize_apart(e)))
    3
    >>> variables(e).intersection(variables(standardize_apart(e)))
    set([])
    >>> is_variable(standardize_apart(expr('x')))
    True
    """
    if not isinstance(sentence, Expr):
        return sentence
    elif is_var_symbol(sentence.op): 
        if sentence in dic:
            return dic[sentence]
        else:
            standardize_apart.counter += 1
            v = Expr('V_%d' % standardize_apart.counter)
            dic[sentence] = v
            return v
    else: 
        return Expr(sentence.op,
                    *[standardize_apart(a, dic) for a in sentence.args])

standardize_apart.counter = 0

def variablizer(sentence, vdic={}):
    """Replace all constants in sentence with new variables.
    This assignment is rememembered and used in later cases.
    """
    if not isinstance(sentence, Expr):
        return sentence
    elif not is_var_symbol(sentence.op) and len(sentence.args) is 0: 
        if sentence in vdic:
            return vdic[sentence]
        else:
            if deduce.counter < 24:
                deduce.counter += 1
                v = built_in_vars[deduce.counter]
            else:
                standardize_apart.counter += 1
                v = Expr('V_%d' % standardize_apart.counter)
            vdic[sentence] = v
            return v
    else: 
        return Expr(sentence.op,
                    *[variablizer(a, vdic) for a in sentence.args])
    
def new_variablizer(sentence, vdic={}):
    """Replace all constants in sentence with new variables.
    This assignment is rememembered and used in later cases.
    """
    if not isinstance(sentence, Expr):
        return sentence
    elif not is_var_symbol(sentence.op) and len(sentence.args) is 0: 
        if sentence in vdic:
            return vdic[sentence]
        else:
            if deduce.counter < 24:
                deduce.counter += 1
                v = built_in_vars[deduce.counter]
            else:
                standardize_apart.counter += 1
                v = Expr('V_%d' % standardize_apart.counter)
            vdic[sentence] = v
            return v
    else: 
        return Expr(sentence.op,
                    *[new_variablizer(a, vdic) for a in sentence.args])  

def deduce(sentence, subst_dict={}):
    """Deduce or generalize an expression
    """
    if is_literal(sentence):
        new_args = []
        for i in sentence.args:
            # Check if i is not a simple constant
            if len(i.args) == 0:
                if i not in subst_dict:
                    if deduce.counter < 24:
                        subst_dict[i] = built_in_vars[deduce.counter]                        
                    else:
                        subst_dict[i] = Expr('V_%d' % deduce.counter)
                    deduce.counter += 1
            else:
                subst_dict = deduce(i, subst_dict)
        return subst_dict

def gdeduce(sentence, subst_dict={}):
    """Deduce or generalize an expression
    """
    if is_literal(sentence):
        new_args = []
        if len(sentence.args) == 0:
            if sentence not in subst_dict:
                if gdeduce.counter < 24:
                    subst_dict[sentence] = built_in_vars[gdeduce.counter]                        
                else:
                    subst_dict[sentence] = Expr('V_%d' % gdeduce.counter)
                gdeduce.counter += 1
            return subst_dict
        for i in sentence.args:
            # Check if i is not a simple constant
            if len(i.args) == 0:
                if i not in subst_dict:
                    if gdeduce.counter < 24:
                        subst_dict[i] = built_in_vars[gdeduce.counter]                        
                    else:
                        subst_dict[i] = Expr('V_%d' % gdeduce.counter)
                    gdeduce.counter += 1
            else:
                subst_dict = gdeduce(i, subst_dict)
        return subst_dict

gdeduce.counter = 0        
    
def non_recur_deduce(sentence, subst_dict={}):
    """Deduce or generalize an expression. Doesn't do recursive deduce.
    So ez(2, 3, int(4, 5)) is deduced as ez(a, b, c).
    """
    if is_literal(sentence):
        new_args = []
        for i in sentence.args:
            if i not in subst_dict:
                subst_dict[i] = built_in_vars[deduce.counter]
                deduce.counter += 1
        return subst_dict

deduce.counter = 0        

def lgg(clause_dict, sol_lgg=[], sub_dict={}):
    """Find lgg of two clauses. Input is in the form of dict where
    keys are terms from one clause and corresponding values are terms from the 
    other clause.    
    Note that in Second Order terms like sur(.,.,int1,2)), int(1,2) is considered as
    single item
    """
    if len(clause_dict.keys()) is 0:
        return [True, sol_lgg, sub_dict]
    
    for term in clause_dict:
        term1 = term
        term2 = clause_dict[term]
        if term1.op != term2.op:
            return False, sol_lgg, sub_dict
        #term1, term2 = subst(sub_dict, [term1, term2])
        for i in xrange(0, len(term1.args)):
            #http://www.comlab.ox.ac.uk/activities/machinelearning/Aleph/misc/basic.html#TermLgg
            
            # Use tuples for convenience in hashing 
            # We also push single_key:value pair for facilitating substitution
            if term1.args[i] == term2.args[i]:
                if lgg.counter < 24:
                    sub_dict[term1.args[i]]                 = built_in_vars[lgg.counter]
                    sub_dict[(term1.args[i],term1.args[i])] = built_in_vars[lgg.counter]
                    
                else:
                    sub_dict[term1.args[i]]                 = Expr('V_%d' % lgg.counter)
                    sub_dict[(term1.args[i],term1.args[i])] = Expr('V_%d' % lgg.counter)
                                                        
            elif term1.args[i] != term2.args[i] and (term1.args[i],term2.args[i]) not in sub_dict: 
                if lgg.counter < 24:
                    #sub_dict[term1.args[i]]                 = built_in_vars[lgg.counter]
                    #sub_dict[term2.args[i]]                 = built_in_vars[lgg.counter]
                    sub_dict[(term1.args[i],term2.args[i])] = built_in_vars[lgg.counter]
                    sub_dict[(term2.args[i],term1.args[i])] = built_in_vars[lgg.counter]
                    
                else:
                    #sub_dict[term1.args[i]]                 = Expr('V_%d' % lgg.counter)
                    #sub_dict[term2.args[i]]                 = Expr('V_%d' % lgg.counter)                                    
                    sub_dict[(term1.args[i],term2.args[i])] = Expr('V_%d' % lgg.counter)                        
                    sub_dict[(term2.args[i],term1.args[i])] = Expr('V_%d' % lgg.counter)                        
            # This case is for variables          
            elif term1 == term2:
                if lgg.counter < 24:
                    sub_dict[term1]         = built_in_vars[lgg.counter]
                    sub_dict[(term1,term1)] = built_in_vars[lgg.counter]
                    
                else:
                    sub_dict[term1]         = Expr('V_%d' % lgg.counter)
                    sub_dict[(term1,term1)] = Expr('V_%d' % lgg.counter)
                
            lgg.counter += 1    
        if len(term1.args) is 0:
            if term1 == term2:
                if lgg.counter < 24:
                    sub_dict[term1]         = built_in_vars[lgg.counter]
                    sub_dict[(term1,term1)] = built_in_vars[lgg.counter]
                    
                else:
                    sub_dict[term1]         = Expr('V_%d' % lgg.counter)
                    sub_dict[(term1,term1)] = Expr('V_%d' % lgg.counter)
            else:
                if lgg.counter < 24:
                    sub_dict[term1]         = built_in_vars[lgg.counter]
                    sub_dict[term2]         = built_in_vars[lgg.counter]
                    sub_dict[(term1,term2)] = built_in_vars[lgg.counter]
                    sub_dict[(term2,term1)] = built_in_vars[lgg.counter]
                    
                else:
                    sub_dict[term1]         = Expr('V_%d' % lgg.counter)
                    sub_dict[term2]         = Expr('V_%d' % lgg.counter)                                    
                    sub_dict[(term1,term2)] = Expr('V_%d' % lgg.counter)                        
                    sub_dict[(term2,term1)] = Expr('V_%d' % lgg.counter)                        
            lgg.counter += 1    
     
        sol_lgg.append(lgg_subst(sub_dict,term1))
        temp_clause_dict = clause_dict.copy()
        del temp_clause_dict[term]
        return lgg(temp_clause_dict, sol_lgg, sub_dict)

def match_clauses(clause_dict, sol_lgg=[], sub_dict={}, dis=0):
    """Find lgg of two clauses. Input is in the form of dict where
    keys are terms from one clause and corresponding values are terms from the 
    other clause.    
    Note that in Second Order terms like sur(.,.,int1,2)), int(1,2) is considered as
    single item
    """
    for term in clause_dict:
        term1 = term
        term2 = clause_dict[term]
        if term1.op != term2.op:
            return [False, sol_lgg, sub_dict, dis]
        #term1, term2 = subst(sub_dict, [term1, term2])
        for i in xrange(0, len(term1.args)):
            #http://www.comlab.ox.ac.uk/activities/machinelearning/Aleph/misc/basic.html#TermLgg
            
            # Use tuples for convenience in hashing 
            # We also push single_key:value pair for facilitating substitution
            if term1.args[i] == term2.args[i]:
                for key in sub_dict.keys():
                    if isinstance(key, tuple):
                        if (term1.args[i] == key[0] and term2.args[i] != key[1]) or (term1.args[i] == key[1] and term2.args[i] != key[0]):
                            dis += 1 
                            # There are redundant keys in sub_dict (A,B) and (B,A). So break after looking in one.
                            break
                if lgg.counter < 24:
                    sub_dict[term1.args[i]]                 = built_in_vars[lgg.counter]
                    sub_dict[(term1.args[i],term1.args[i])] = built_in_vars[lgg.counter]
                    
                else:
                    sub_dict[term1.args[i]]                 = Expr('V_%d' % lgg.counter)
                    sub_dict[(term1.args[i],term1.args[i])] = Expr('V_%d' % lgg.counter)
                                                        
            elif term1.args[i] != term2.args[i] and (term1.args[i],term2.args[i]) not in sub_dict: 
                for key in sub_dict.keys():
                    if isinstance(key, tuple):
                        if (term1.args[i] in key and term2.args[i] not in key) or (term2.args[i] in key and term1.args[i] not in key):
                            dis += 1
                            break
                if lgg.counter < 24:
                    #sub_dict[term1.args[i]]                 = built_in_vars[lgg.counter]
                    #sub_dict[term2.args[i]]                 = built_in_vars[lgg.counter]
                    sub_dict[(term1.args[i],term2.args[i])] = built_in_vars[lgg.counter]
                    sub_dict[(term2.args[i],term1.args[i])] = built_in_vars[lgg.counter]
                    
                else:
                    #sub_dict[term1.args[i]]                 = Expr('V_%d' % lgg.counter)
                    #sub_dict[term2.args[i]]                 = Expr('V_%d' % lgg.counter)                                    
                    sub_dict[(term1.args[i],term2.args[i])] = Expr('V_%d' % lgg.counter)                        
                    sub_dict[(term2.args[i],term1.args[i])] = Expr('V_%d' % lgg.counter)                        
                
            lgg.counter += 1    
        if len(term1.args) is 0:
            if term1 == term2:
                for key in sub_dict.keys():
                    if isinstance(key, tuple):
                        if (term1 == key[0] and term2 != key[1]) or (term1 == key[1] and term2 != key[0]):
                            dis += 1 
                            break
                if lgg.counter < 24:
                    sub_dict[term1]         = built_in_vars[lgg.counter]
                    sub_dict[(term1,term1)] = built_in_vars[lgg.counter]
                    
                else:
                    sub_dict[term1]         = Expr('V_%d' % lgg.counter)
                    sub_dict[(term1,term1)] = Expr('V_%d' % lgg.counter)
            else:                
                for key in sub_dict.keys():
                    if isinstance(key, tuple):
                        if (term1 in key and term2 not in key) or (term2 in key and term1 not in key):
                            dis += 1 
                            break
                if lgg.counter < 24:
                    sub_dict[term1]         = built_in_vars[lgg.counter]
                    sub_dict[term2]         = built_in_vars[lgg.counter]
                    sub_dict[(term1,term2)] = built_in_vars[lgg.counter]
                    sub_dict[(term2,term1)] = built_in_vars[lgg.counter]
                    
                else:
                    sub_dict[term1]         = Expr('V_%d' % lgg.counter)
                    sub_dict[term2]         = Expr('V_%d' % lgg.counter)                                    
                    sub_dict[(term1,term2)] = Expr('V_%d' % lgg.counter)                        
                    sub_dict[(term2,term1)] = Expr('V_%d' % lgg.counter)                        
            lgg.counter += 1    
     
        sol_lgg.append(lgg_subst(sub_dict,term1))        
    return [True, sol_lgg, sub_dict, dis]
    
        
# This constant is used in lgg for variable generation                            
lgg.counter = 0                

#______________________________________________________________________________

class FolKB (KB):
    """A knowledge base consisting of first-order definite clauses
    >>> kb0 = FolKB([expr('Farmer(Mac)'), expr('Rabbit(Pete)'),
    ...              expr('(Rabbit(r) & Farmer(f)) ==> Hates(f, r)')])
    >>> kb0.tell(expr('Rabbit(Flopsie)'))
    >>> kb0.retract(expr('Rabbit(Pete)'))
    >>> kb0.ask(expr('Hates(Mac, x)'))[x]
    Flopsie
    >>> kb0.ask(expr('Wife(Pete, x)'))
    False
    """

    def __init__ (self, initial_clauses=[]):
        self.clauses = {}
        self.size = 0
        for clause in initial_clauses:
            self.tell(clause)

    def tell(self, sentence):
        if sentence is None:
            return
        if is_definite_clause(sentence):
            self.size += 1
            if sentence.op in self.clauses:
                self.clauses[sentence.op].append(sentence)
            else:
                self.clauses[sentence.op] = [sentence]
        else:
            raise Exception("Not a definite clause: %s" % sentence)

    def ask_generator(self, query):
        return fol_bc_ask(self, [query])
 
    def retract(self, sentence):
        self.clauses[sentence.op].remove(sentence)
    
    def __len__(self):
        # This if condition will fail if we add to KB after finding the size.
        if self.size is not 0:
            return self.size
        for key in self.clauses.keys():
            self.size += len(self.clauses[key])
        return self.size    

def test_ask(kb, q):
    goals = []
    vars = set([])
    for i in q:
        e = expr(i)
        goals.append(e)
        vars = vars.union(variables(e))
    ans = fol_bc_ask(kb, goals)
    res = []
    for a in ans:
        res.append(pretty(dict([(x, v) for (x, v) in a.items() if x in vars])))
    res.sort(key=str)
    return res
    
def fol_bc_ask_brief(KB, goals, theta={}):
    ans = fol_bc_ask(KB, goals, theta)
    for a in ans:
        return True
    return False

    
def fol_bc_ask(KB, goals, theta={}):
    """A simple backward-chaining algorithm for first-order logic. [Fig. 9.6 in AIMA]
    KB should be an instance of FolKB, and goals a list of literals.

    >>> test_ask('Farmer(x)')
    ['{x: Mac}']
    >>> test_ask('Human(x)')
    ['{x: Mac}', '{x: MrsMac}']
    >>> test_ask('Hates(x, y)')
    ['{x: Mac, y: Pete}']
    >>> test_ask('Loves(x, y)')
    ['{x: MrsMac, y: Mac}', '{x: MrsRabbit, y: Pete}']
    >>> test_ask('Rabbit(x)')
    ['{x: MrsRabbit}', '{x: Pete}']
    """

    if goals == []:
        yield theta
        raise StopIteration()
    
    q1 = subst(theta, goals[0])
    
    # Selecting only facts with q1.op predicate
    # Bug: Will not work for sentences with logical operators like ==>, & etc.
    # Currently my data does not have such sentences. So skip for future correction
    try:
        limited_KB = KB.clauses[q1.op]
    except KeyError:
        raise StopIteration()
            
    for r in limited_KB:
        theta1 = unify(r, q1, {})

        if theta1 is not None:
            new_goals = goals[1:]
            for ans in fol_bc_ask(KB, new_goals, subst_compose(theta1, theta)):
                yield ans

    raise StopIteration()

def fol_bc_ask_eff(KB, goals, theta={}):
    ind = 0
    for goal in goals:
        q1 = subst(theta, goal)
        limited_KB = KB.clauses[q1.op]
        for r in limited_KB:
            theta1 = unify(r, q1, {})
            if theta1 is not None:
                theta = subst_compose(theta1, theta)
                ind += 1
                break
    if ind is len(goals):
        return True
    else:
        return False

def subst_compose (s1, s2):
    """Return the substitution which is equivalent to applying s2 to
    the result of applying s1 to an expression.

    >>> s1 = {x: A, y: B}
    >>> s2 = {z: x, x: C}
    >>> p = F(x) & G(y) & expr('H(z)')
    >>> subst(s1, p)
    ((F(A) & G(B)) & H(z))
    >>> subst(s2, p)
    ((F(C) & G(y)) & H(x))
    
    >>> subst(s2, subst(s1, p))
    ((F(A) & G(B)) & H(x))
    >>> subst(subst_compose(s1, s2), p)
    ((F(A) & G(B)) & H(x))

    >>> subst(s1, subst(s2, p))
    ((F(C) & G(B)) & H(A))
    >>> subst(subst_compose(s2, s1), p)
    ((F(C) & G(B)) & H(A))
    >>> ppsubst(subst_compose(s1, s2))
    {x: A, y: B, z: x}
    >>> ppsubst(subst_compose(s2, s1))
    {x: C, y: B, z: A}
    >>> subst(subst_compose(s1, s2), p) == subst(s2, subst(s1, p))
    True
    >>> subst(subst_compose(s2, s1), p) == subst(s1, subst(s2, p))
    True
    """
    if s1 is None:
        return s2
    if s2 is None:
        return s1
    sc = {}
    for x, v in s1.items():
        if s2.has_key(v):
            w = s2[v]
            sc[x] = w # x -> v -> w
        else:
            sc[x] = v
    for x, v in s2.items():
        if not (s1.has_key(x)):
            sc[x] = v
        # otherwise s1[x] preemptys s2[x]
    return sc

#def distance_between_clauses(clause1, clause2, lgg_clause, lgg_dict):
    #"""Calculates the distance between clauses. Assumes clause1 and clause2
    #are arranged in order of matching. lgg_dict is the dictionary of variable
    #substitutions obtained during construction of lgg.
    #"""
    #dis = 10 * abs(len(clause1) - len(clause2))
    ## Compare class is obtained by substituting the variables from the dictionary in
    ## the given clauses
    ## This is for clause1
    #clauses = [clause1, clause2]
    #for clause in clauses:
        #compare_clause = subst(lgg_dict, clause)
        
        #for i in xrange(0, len(clause)):
            #term1 = lgg_clause[i]
            #term2 = compare_clause[i]
            #if term1.op != term2.op:
                #dis += 10
            #else:
                #max_args = max(len(term1.args), len(term2.args))
                #common_args = len(set(term1.args).intersection(set(term2.args)))
                #dis += (max_args - common_args)             
    #return dis

def distance_between_clauses(clause1, clause2):
    """Calculates the distance between clauses. Assumes clause1 and clause2
    are arranged in order of matching. lgg_dict is the dictionary of variable
    substitutions obtained during construction of lgg.
    """
    dis = 10 * abs(len(clause1) - len(clause2))
    # Compare class is obtained by substituting the variables from the dictionary in
    # the given clauses
    # This is for clause1
    clause1 = local_variablizer(clause1)
    clause2 = local_variablizer(clause2)
    
    for i in xrange(0, len(clause)):
        term1 = clause1[i]
        term2 = clause2[i]
        if term1.op != term2.op:
            dis += 10
        else:
            max_args = max(len(term1.args), len(term2.args))
            common_args = len(set(term1.args).intersection(set(term2.args)))
            dis += (max_args - common_args)             
    return dis

def terms_from_string(qstr,stripspaces=True,opar="(",cpar=")",term_separator=","):
    """Gets a list of terms from a string.
    ex: string1 = "x (a, b, int(1,2)) , y (c, d, int(4,5)) , z (int(1,2))."
        string2 = "x (a, b, int(1,2)) & y (c, d, int(4,5)) & z (int(1,2))."
        terms1 = terms_from_string(string1)
        terms2 = terms_from_string(string2)
    """
    if qstr.count(opar) != qstr.count(cpar):
        raise 'Hypothesis body is not balanced'
   
    if stripspaces == True:
        qstr = qstr.replace(" ","")
    
    if qstr.count('&'):
        # The term separator seems to be '&', so change to it
        term_separator = '&'
     
    start = 0
    par_count = 0
    e = -1
    ind = 0
    terms = []
    for c in qstr:
        if c == '.':
            e = -1
            if par_count != 0:
                raise 'Hypothesis body is not balanced'
            break
        elif c == '(':
            par_count += 1
        elif c == ')':
            par_count -= 1
            if par_count == 0:
                e = ind + 1
                terms.append(qstr[start:e])
        elif c == term_separator and par_count == 0:
            start = ind + 1
        ind += 1      
        
    return expr(terms)        
  
#_______________________________________________________________________________

if __name__ == '__main__':
    from base.ilp.hyp import *
    
    string1 = "x (a, b, int(1,2)) , y (c, d, int(4,5)) , z (int(1,2))."
    string2 = "x (a, b, int(1,2)) & y (c, d, int(4,5)) & z (int(1,2))."    
    string3 = "x (a, b, int(1,2))"    
    
    terms1 = terms_from_string(string1)
    terms2 = terms_from_string(string2)
    terms3 = terms_from_string(string3)
    
    print terms1
    print terms2

    z = expr('vehicle(obj(veh(aircraft(v_12))),int(12,15))')
    z1 = deduce(z)
    
    a = expr('R(Xt1, Xc1)')
    b = expr('P(Xt1, X)')
    c = expr('Q(Xc1, X)')
    d = Expr(['a','b','c'], 'x')
        
    d = expr('R(Xt2, Xc2)')
    s = expr('as(bs(cs(ds)))')
    t = expr('as(bs(cs(ds(es(int(f,g),int(g,f))))))')
    o1 = expr('obj(veh(aircraft(A)))')
    o2 = expr('obj(veh(loader(B)))')
    o3 = expr('obj(person(C))')
    z  = expr('right_zone')
        
    r1 = Expr('sur',[o1,o2,expr('int(T1, T2)')])
    r2 = Expr('con',[o1,o2,expr('int(T3, T4)')])
    r3 = Expr('con',[o1,z,expr('int(T5, T6)')])
    r4 = Expr('con',[z,o3,expr('int(T7, T8)')])
    r5 = Expr('meets',[expr('int(T1, T2)'), expr('int(T3, T4)')])    

    #head = expr('head()')
    #hyp = Clause(head,[r1,r2,r3,r4,r5])
    #new_hyp = refine_by_type(hyp)    
    #print t
    #print t.op
    #print t.args
    e = expr('P(Xt2, Y)')
    f = expr('Q(Xc2, Y)')
    y = expr('Y')
    at = subst({'s':'a'},expr('hi(1,2)'))
    at = pyswip_subst({'Y':'a'},[e,f])
    
    g = expr('r(Xt4, Xc3)')
    h = expr('P(Xt3, Y)')
    i = expr('Q(Xc1, V)')
    print pyswip_subst({'Xt4':1},g)
    res = lgg({a:d,b:e,c:f},[],{})
    res[1].reverse()
    print res[1]
   
    res = lgg({a:g,b:h,c:i},[],{})
    res[1].reverse()
    print res[1]
    
    ilp_test_kb = FolKB(
        map(expr, ['Con(Za, A)',
                    'Sur(Za, A)',
                    'Con(Zb, A)',
                    'Sur(Zb, A)'
                    ])
    )

    pos_ex = FolKB(
        map(expr, ['Enter_Zone(Za, int(A, B))',
                            'Enter_Zone(Zb, int(CA, D))'
                          ])
    )

    neg_ex = FolKB(
        map(expr, ['Enter_Zone(Zd, int(A, B))',
                            'Enter_Zone(Ze, int(CA, D))'
                          ])
    )

    # test_kb and ilp_test_kb are already defined in the script
    KB = FolKB([expr('con(obj_4002,obj_227,int(1355,1370))')])
    goals = [expr('con(obj_4002, E, F)')]
    
    new = standardize_apart(goals[0])
    print new
    new2 = standardize_apart(new)
    print new2
    print deduce.counter
    
    ans = fol_bc_ask(KB,goals)
    #a = expr('con(A,B,int(C,D))')
    a = expr(['con(A,B,int(C,D))', 'con(D,E,int(F,G))'])
    var = variables(a[0])
    print list(ans)
    ex = expr('Enter_Zone(Za)')
    Za = expr('Za')
    a = expr('a')
    theta = {Za:a}
    an = subst(theta,ex)
    goals = [expr('Con(Zb, y)'), expr('Sur(Zb, y)')]
    a = expr('r(1, 2, q(4,5))')
    b = deduce(a)
    a = expr('r(1,1)')
    b = deduce(a)
    a = expr('r(1,1)')
    b = deduce(a)
    ans = fol_bc_ask_brief(ilp_test_kb, goals)
    e = expr('Rabbit(y) & Human(y)')
    f = expr('Farmer(x)')
    a = test_ask(test_kb, ['Farmer(x)', 'Rabbit(y)'])
    b = test_ask(ilp_test_kb, ['Enter_zone(x)', 'Con(x,y)', 'Sur(x,y)'])
    print a
    print b
