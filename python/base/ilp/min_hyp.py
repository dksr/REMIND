import re

def isnumber(x):
    "Is x a number? We say it is if it has a __int__ method."
    return hasattr(x, '__int__')

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
        
def is_symbol(s):
    "A string s is a symbol if it starts with an alphabetic char."
    return isinstance(s, str) and len(s) != 0 and s[0].isalpha()

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

def unique(seq):
    """Remove duplicate elements from seq. Assumes hashable elements.
    >>> unique([1, 2, 3, 2, 1])
    [1, 2, 3]
    """
    return list(set(seq))

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
                return '%s(%s)' % (self.op, ', '.join(map(repr, self.args)))
            else:
                op_str = '('.join(op_list)
                expr_str = '%s(%s' % (op_str, ', '.join(map(repr, self.args)))
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
    return eval(s, {'Expr':Expr})


class Clause(Expr):
    """Class definition for hypothesis"""
    def __init__(self, head, body, hyp_id, types={}):
        # Sample input: hyp = Hyp(e,[[f,g],[g,f]]) where e,f,g are valid
        # expressions and definite clauses.
        self.head = head
        self.body = []
        # score is [score, pos_ex_covered, tot_neg_ex_covered, tot_pos_ex]
        self.score = [-100000, [], 0, 0]
        self.all_vars = []
        self.all_vars_avail = []
        self.prunable = False
        self.pruned = False
        self.scored = False
        self.expandable  = True 
        self.goal_tested = False
        self.bottom_clause_ind = -1
        self.spatial_predicate_count = 0
        self.spatial_expandable  = True
        self.temporal_expandable = True
        self.parent_score = [-100000, [], 0, 0]
        self.generic_types = types
        self.hyp_id        = hyp_id
        self.kids          = []
        self.pos_inst      = []
        self.neg_inst      = []
        
        # There can be many terms in the body. So add all of them.
        if body  != None:
            for term in body:
                self.body.append(term)

        self.predicates = []
        
    def get_string(self):
        return Clause.__repr__(self)

    def get_head(self):
        return self.head

    def get_body(self):
        return self.body
    
    def get_all_predicates(self):
        """Returns all predicates as a list, also includes head predicate"""
        if len(self.predicates) is not 0:
            return self.predicates
        # First get the list of predicates from the body
        self.predicates = map(lambda x: x.op, self.body)
        # Now add the head predicate
        self.predicates.append(self.head.op)
        return self.predicates   
      
    def get_all_args(self):
        """Will only work for upto depth one. Need to improve """
        all_args = set([])
        all_args = all_args.union(self.head.args)
        for term in self.body:
            all_args = all_args.union(term.args)
        return all_args

    def get_all_args_avail(self):
        """Repitition is allowed unlike get_all_args where args are unique."""
        all_args = self.head.args[:]
        for term in self.body:
            all_args.append(term.args)
        return list(flatten(all_args))

    def get_all_vars(self):
        """Returns all unique variables as a list"""
        # If all_vars already computed return it.
        if len(self.all_vars) is not 0:
            return self.all_vars
        self.all_vars = unique(self.get_all_vars_avail())
        return self.all_vars
       
    def get_all_vars_avail(self):
        """Returns all unique variables as a list"""
        # Not sure why sometimes self.all_vars_avail is getting values from
        # If all_vars already computed return it.
        if len(self.all_vars_avail) is not 0:
            return self.all_vars_avail
        self.all_vars_avail.append(list(variables(self.head)))
        for term in self.body:
            self.all_vars_avail.append(list(variables(term)))
        # Flatten the list of lists and return as list instead of generator    
        self.all_vars_avail = list(flatten(self.all_vars_avail))
        return self.all_vars_avail
        
    def __repr__(self):
        if len(self.body) < 1: return str(self.head) + ' :- '      
        terms = [str(term) for term in self.body]    
        body_str = "%s%s" %(', '.join(terms),'.')
        return "%s%s%s"%(self.head.op,' :- ', body_str)

    def __eq__(self, other):
        """x and y are equal iff their heads and clauses are equal."""
        return (other is self) or (isinstance(other, Clause)
            and self.head == other.head and self.body == other.body)

    def __hash__(self):
        """Need a hash method so Hyps can live in dicts."""
        # Normal set objects are unhashable, so use frozenset
        return hash(frozenset(self.body))
        #return hash(self.head) ^ hash(tuple(self.body))

    def copy(self):
        """Creates and returns a duplicate hypothesis"""
        head = copy.copy(self.head)
        body = self.body[:]
        return Clause(head, body, self.hyp_id, self.generic_types)
        
    def reset_score(self):
        self.score = [-100000, [], 0, 0]
 
if __name__ == "__main__":
    e = expr('enter_zone(X)')
    f = expr('con(X, Y)')
    g = expr('sur(X, Y)')
    ex = expr('enter_zone(za)')
    c1 = Clause(e,[f,g], 0)
    print c1