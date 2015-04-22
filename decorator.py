import time


def timeit(method):
  def timed(*args, **kw):
    ts = time.time()
    result = method(*args, **kw)
    te = time.time()

    print '%r (%r, %r) %2.2f sec' % \
          (method.__name__, args, kw, te - ts)
    return result

  return timed


def timing_function(some_function):
  """
  Outputs the time a function takes
  to execute.
  """

  def wrapper():
    t1 = time.time()
    some_function()
    t2 = time.time()
    return "Time it took to run the function: " + str((t2 - t1)) + " sec"

  return wrapper

