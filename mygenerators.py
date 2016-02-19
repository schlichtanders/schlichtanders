import pylab as pl
import itertools as it
from itertools import izip
import operator as op
from timeit import default_timer


def deleteallbutone(elm, l):
    one = False
    for i in l:
        if i == elm and not one:
            one = True
            yield i
        elif i == elm:
            continue #pass
        else:
            yield i


def merge(*args):
    """merges args into an already existing list of tuples structure (e.g. created by previous zip or product)"""
    # read first elements to get to know what are tuples, what not
    iters = map(iter, args)
    firsts = map(next, iters)
    istuple = [isinstance(f, tuple) for f in firsts]

    def merge_row(row):
        # TODO maybe use list as intermediate type to prevent copying??
        return reduce(op.add, (x if t else (x,) for t, x in izip(istuple, row)))

    yield merge_row(firsts) # yield initials
    for row in izip(*iters): # yield all the rest
        yield merge_row(row)

def merge_dyn(*args):
    """merges args into an already existing list of tuples structure (e.g. created by previous zip or product)
    slightly slower, but less code =), and more dynamic
    """
    def merge_row(row):
        # TODO maybe use list as intermediate type to prevent copying??
        return reduce(op.add,
            (x if isinstance(x, tuple) else (x,) for x in row)
        )
    for row in izip(*args):
        yield merge_row(row)


def accumulate(iterable, func=operator.add, base=None):
    'Return running totals'
    # accumulate([1,2,3,4,5]) --> 1 3 6 10 15
    # accumulate([1,2,3,4,5], operator.mul) --> 1 2 6 24 120
    it = iter(iterable)
    if base is None:
        base = next(it)
        yield base
    for element in it:
        base = func(base, element)
        yield base


def flatten(iterable):
    for i in iterable:
        if hasattr(i, "__iter__"):
            for n in flatten(i):
                yield n
        else:
            yield i


def enumerate_(iterable):
    for i, x in enumerate(iterable):
        yield (i,) + x


def time_gen(generator):
    start_time = default_timer()
    for e in generator:
        yield e, default_timer() - start_time


def product(*args):
    for l in _product(args):
        yield tuple(l)

def _product(args):
    """alternative to itertools.product which works with infinite series"""
    if not args:
        yield []
    else:
        for i in args[0]:
            for j in _product(args[1:]):
                j.insert(0, i)
                yield j

def eat(gen, n=1):
    for _ in xrange(n):
        next(gen)

def hist(iterable, history_size=1, filler="None"):
    gen = iter(iterable)
    if filler != "None":
        gen = it.chain(it.repeat(filler, history_size), gen)
    gens = it.tee(gen, 1 + history_size)
    for i, g in enumerate(gens):
        eat(g, i) # eat history, last gen has most eaten
    return izip(*gens)

def compress_idx(data, selectors):
    """
    Return data elements where indexes correspond to  selector elements.
    Forms a shorter iterator from selected data elements using the
    selectors to choose the data elements.
    """
    idxs = iter(selectors)
    idx = next(idxs)
    for i, d in enumerate(data):
        if i == idx:
            yield d
            idx = next(idxs)

def int_exponentials(base=2):
    for i in it.count(0):
        yield int(base**i)

def succint_exponentials(base=2):
    OFFSET = 0
    for o, a in hist(int_exponentials(base), filler=-inf):
        if a + OFFSET == o + OFFSET:
            OFFSET += 1
        yield a + OFFSET

def takewhile1(predicate, iterable):
    # takewhile1(lambda x: x<5, [1,4,6,4,1]) --> 1 4 6
    for x in iterable:
        if predicate(x):
            yield x
        else:
            yield x
            break


def recurse(func, initial, stop_criterion = lambda a, b, n: n>500):
    yield initial
    b = initial
    for n in it.count(0):
        a = b
        b = func(a)
        yield b
        if stop_criterion(a,b,n):
            break

def converge(func, initial, stop_criterion = lambda a, b, n: n>500):
    b = initial
    for n in it.count(0):
        a = b
        b = func(a)
        if stop_criterion(a,b,n):
            break
    return b, n


def recurse_stepwise(func, initial, *ARGS, **kwargs):
    stop_criterion = kwargs.pop('stop_criterion', lambda a, b, n: n>5000)
    yield initial
    b = initial
    for n, args in product(it.count(0), zip(*ARGS)):
        a = b
        b = func(a, *args)
        yield b
        if stop_criterion(a,b,n):
            break

def converge_stepwise(func, initial, *ARGS, **kwargs):
    stop_criterion = kwargs.pop('stop_criterion', lambda a, b, n: n>5000)
    b = initial
    for i, n, args in enumerate_(product(it.count(0), zip(*ARGS))):
        a = b
        b = func(a, *args)
        if stop_criterion(a,b,n):
            break
    return b, i, n
