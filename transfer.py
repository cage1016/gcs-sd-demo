# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Uploads or downloads files between Google Cloud Storage and the filesystem.

The file is transfered in CHUNKSIZE pieces, and the process can resume in case
of some failures.

Usage examples:
  $ python transfer.py gs://bucket/object ~/Desktop/filename
  $ python transfer.py ~/Desktop/filename gs://bucket/object

"""
from pprint import pprint
import sys
import random
import time
import httplib2
import urllib2
import io

from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload
from json import dumps as json_dumps
from googleapiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

from decorator import timing_function, timeit
from mymeidaiobasedownload import *

import patch

# Message describing how to use the script.
USAGE = """
Usage examples:
  $ python transfer.py gs://bucket/object ~/Desktop/filename
  $ python transfer.py ~/Desktop/filename gs://bucket/object

"""

SCOPES = ['https://www.googleapis.com/auth/devstorage.read_write',
          'https://www.googleapis.com/auth/devstorage.read_only']

# Retry transport and file IO errors.
RETRYABLE_ERRORS = (httplib2.HttpLib2Error, IOError)

# Number of times to retry failed downloads.
NUM_RETRIES = 5

# Number of bytes to send/receive in each request.
CHUNKSIZE = 2 * 1024 * 1024

# Mimetype to use if one can't be guessed from the file extension.
DEFAULT_MIMETYPE = 'application/octet-stream'


def get_authenticated_service(scope):
  # Load the key in PKCS 12 format that you downloaded from the Google API
  # Console when you created your Service account.
  f = file('mitac-miwatermark-bfcdb27a1b33.p12', 'rb')
  key = f.read()
  f.close()

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with the Credentials. Note that the first parameter, service_account_name,
  # is the Email address created for the Service account. It must be the email
  # address associated with the key that was created.
  credentials = SignedJwtAssertionCredentials(
    '449185255153-tp4ndg73f5b06dj9fausbgb5ld8i4ndo@developer.gserviceaccount.com',
    key,
    scope=scope)
  http = httplib2.Http()
  http = credentials.authorize(http)

  return build("storage", "v1", http=http)


def handle_progressless_iter(error, progressless_iters):
  if progressless_iters > NUM_RETRIES:
    print 'Failed to make progress for too many consecutive iterations.'
    raise error

  sleeptime = random.random() * (2 ** progressless_iters)
  print ('Caught exception (%s). Sleeping for %s seconds before retry #%d.'
         % (str(error), sleeptime, progressless_iters))
  time.sleep(sleeptime)


def print_with_carriage_return(s):
  sys.stdout.write('\r' + s)
  sys.stdout.flush()


def upload(argv):
  filename = argv[1]
  bucket_name, object_name = argv[2][5:].split('/', 1)
  assert bucket_name and object_name

  service = get_authenticated_service(SCOPES)

  print 'Building upload request...'
  media = MediaFileUpload(filename)
  if not media.mimetype():
    media = MediaFileUpload(filename, DEFAULT_MIMETYPE)
  request = service.objects().insert(bucket=bucket_name, name=object_name, media_body=media)

  print 'Uploading file: %s to bucket: %s object: %s ' % (filename, bucket_name,
                                                          object_name)
  response = request.execute()

  print 'Uploaded Object:'
  print json_dumps(response, indent=2)


@timeit
def download_with_timer(argv):
  """
  test function to measure http request time

  output message:

  Building download request...
  Downloading bucket: nearline-sd-test object: main.py to file: ./a.py
  'new_request' ((u'https://www.googleapis.com/storage/v1/b/nearline-sd-test/o/main.py?alt=media',), {'headers': {}}) 3.31 sec
  ttfb(time till first byte) 3.28957819939 sec
  Download complete!
  'download' ((['transfer.py', 'gs://nearline-sd-test/main.py', './a.py'],), {}) 4.34 sec

  explain:

  1. 3.31 sec -> whole http request response time
  2. 3.28957819939 sec -> ttfb (time till first byte) time
  3. 4.34 sec -> download_with_timer execute time

  """


  bucket_name, object_name = argv[1][5:].split('/', 1)
  filename = argv[2]
  assert bucket_name and object_name

  service = get_authenticated_service(SCOPES)

  print 'Building download request...'

  fh = io.FileIO(filename, mode='wb')
  request = service.objects().get_media(bucket=bucket_name,
                                        object=object_name)

  print 'Downloading bucket: %s object: %s to file: %s' % (bucket_name,
                                                           object_name,
                                                           filename)

  downloader = MyMediaIoBaseDownload(fh, request)
  response, content = downloader.execute()

  if len(service._http.connections) > 1:
    logging.debug("Uh oh, we got pwned. More connections in our Http() than we expected.")

  c = service._http.connections.popitem()[1]

  print 'ttfb(time till first byte) %s sec' % (response.get('x---stop-time') - c._start_time)
  print 'Download complete!'


def download(argv):
  bucket_name, object_name = argv[1][5:].split('/', 1)
  filename = argv[2]
  assert bucket_name and object_name

  service = get_authenticated_service(SCOPES)

  # get object metadata
  req = service.objects().get(bucket=bucket_name, object=object_name)
  resp = req.execute()

  # download object via media link
  response, content = service._http.request(resp.get('mediaLink'))

  fh = io.FileIO(filename, mode='wb')
  fh.write(content)
  fh.close()


if __name__ == '__main__':
  if len(sys.argv) < 3:
    print 'Too few arguments.'
    print USAGE
  if sys.argv[2].startswith('gs://'):
    upload(sys.argv)
  elif sys.argv[1].startswith('gs://'):
    # download(sys.argv)
    download_with_timer(sys.argv)
  else:
    print USAGE
