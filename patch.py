import time

#### MONKEY PATCH for time to first byte.
# neither httplib, nor httplib2 provide a way to get time to first
# byte received. Luckily, Python is monkey patchable.

import httplib

httplib__HTTPResponse__read_status = httplib.HTTPResponse._read_status
httplib__HTTPResponse_begin = httplib.HTTPResponse.begin
httplib__HTTPConnection__send_output = httplib.HTTPConnection._send_output


def perf__read_status(self):
  b = self.fp.read(1)
  # this is our first byte, mark it's time
  self._stop_time = time.time()
  # write back the byte we read to the internal buffer so that it can
  # be used for the status line.
  self.fp._rbuf.write(b)
  return httplib__HTTPResponse__read_status(self)


def perf_begin(self):
  resp = httplib__HTTPResponse_begin(self)
  self.msg.addheader("x---stop-time", self._stop_time)
  return resp


httplib.HTTPResponse._read_status = perf__read_status
httplib.HTTPResponse.begin = perf_begin


def perf__send_output(self, *args):
  # httplib2 gives us access to the connection object
  # within the Http object (it stores it in a dict).
  # Because of this, we can get direct access to this
  # attribute.
  self._start_time = time.time()
  return httplib__HTTPConnection__send_output(self, *args)


httplib.HTTPConnection._send_output = perf__send_output
