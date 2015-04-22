import time
import random
import logging

from googleapiclient.errors import HttpError
from oauth2client import util

from decorator import timing_function, timeit


class MyMediaIoBaseDownload(object):
  """"Download media resources.

  fork MediaIoBaseDownload from apiclient.http


  Note that the Python file object is compatible with io.Base and can be used
  with this class also.


  Example:
    request = farms.animals().get_media(id='cow')
    fh = io.FileIO('cow.png', mode='wb')
    downloader = MediaIoBaseDownload(fh, request)

    status, done = downloader.execute()

    print "Download Complete!"
  """

  @util.positional(3)
  def __init__(self, fd, request):
    """Constructor.

    Args:
      fd: io.Base or file object, The stream in which to write the downloaded
        bytes.
      request: googleapiclient.http.HttpRequest, the media request to perform in
        chunks.
    """
    self._fd = fd
    self._request = request
    self._uri = request.uri
    self._progress = 0
    self._total_size = None
    self._done = False

    # Stubs for testing.
    self._sleep = time.sleep
    self._rand = random.random

  @util.positional(1)
  def execute(self, num_retries=0):
    """Get the next chunk of the download.

    Args:
      num_retries: Integer, number of times to retry 500's with randomized
            exponential backoff. If all retries fail, the raised HttpError
            represents the last request. If zero (default), we attempt the
            request only once.

    Returns:
      (status, done): (MediaDownloadStatus, boolean)
         The value of 'done' will be True when the media has been fully
         downloaded.

    Raises:
      googleapiclient.errors.HttpError if the response was not a 2xx.
      httplib2.HttpLib2Error if a transport error has occured.
    """
    headers = {}
    http = self._request.http

    for retry_num in range(num_retries + 1):
      if retry_num > 0:
        self._sleep(self._rand() * 2 ** retry_num)
        logging.warning(
          'Retry #%d for media download: GET %s, following status: %d'
          % (retry_num, self._uri, resp.status))

      func = timeit(http.request)
      resp, content = func(self._uri, headers=headers)
      if resp.status < 500:
        break

    if resp.status in [200, 206]:
      if 'content-location' in resp and resp['content-location'] != self._uri:
        self._uri = resp['content-location']
      self._progress += len(content)
      self._fd.write(content)

      if 'content-range' in resp:
        content_range = resp['content-range']
        length = content_range.rsplit('/', 1)[1]
        self._total_size = int(length)
      elif 'content-length' in resp:
        self._total_size = int(resp['content-length'])

      return resp, content
    else:
      raise HttpError(resp, content, uri=self._uri)
