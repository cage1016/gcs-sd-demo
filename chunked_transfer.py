# Copyright 2012 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
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
  $ python chunked_transfer.py gs://bucket/object ~/Desktop/filename
  $ python chunked_transfer.py ~/Desktop/filename gs://bucket/object

"""


import httplib2
import random
import sys
import time

from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from apiclient.http import MediaIoBaseDownload
from json import dumps as json_dumps
from googleapiclient.discovery import build
from oauth2client.client import SignedJwtAssertionCredentials

# Message describing how to use the script.
USAGE = """
Usage examples:
  $ python chunked_transfer.py gs://bucket/object ~/Desktop/filename
  $ python chunked_transfer.py ~/Desktop/filename gs://bucket/object

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
  f = file('<your-p12-file>', 'rb')
  key = f.read()
  f.close()

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with the Credentials. Note that the first parameter, service_account_name,
  # is the Email address created for the Service account. It must be the email
  # address associated with the key that was created.
  credentials = SignedJwtAssertionCredentials(
    '<service-account-email>',
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
  media = MediaFileUpload(filename, chunksize=CHUNKSIZE, resumable=True)
  if not media.mimetype():
    media = MediaFileUpload(filename, DEFAULT_MIMETYPE, resumable=True)
  request = service.objects().insert(bucket=bucket_name, name=object_name,
                                     media_body=media)

  print 'Uploading file: %s to bucket: %s object: %s ' % (filename, bucket_name,
                                                          object_name)

  progressless_iters = 0
  response = None
  while response is None:
    error = None
    try:
      progress, response = request.next_chunk()
      if progress:
        print_with_carriage_return('Upload %d%%' % (100 * progress.progress()))
    except HttpError, err:
      error = err
      if err.resp.status < 500:
        raise
    except RETRYABLE_ERRORS, err:
      error = err

    if error:
      progressless_iters += 1
      handle_progressless_iter(error, progressless_iters)
    else:
      progressless_iters = 0

  print '\nUpload complete!'

  print 'Uploaded Object:'
  print json_dumps(response, indent=2)


def download(argv):
  bucket_name, object_name = argv[1][5:].split('/', 1)
  filename = argv[2]
  assert bucket_name and object_name

  service = get_authenticated_service(SCOPES)

  print 'Building download request...'
  f = file(filename, 'w')
  request = service.objects().get_media(bucket=bucket_name,
                                        object=object_name)
  media = MediaIoBaseDownload(f, request, chunksize=CHUNKSIZE)

  print 'Downloading bucket: %s object: %s to file: %s' % (bucket_name,
                                                           object_name,
                                                           filename)

  progressless_iters = 0
  done = False
  while not done:
    error = None
    try:
      progress, done = media.next_chunk()
      if progress:
        print_with_carriage_return(
          'Download %d%%.' % int(progress.progress() * 100))
    except HttpError, err:
      error = err
      if err.resp.status < 500:
        raise
    except RETRYABLE_ERRORS, err:
      error = err

    if error:
      progressless_iters += 1
      handle_progressless_iter(error, progressless_iters)
    else:
      progressless_iters = 0

  print '\nDownload complete!'


if __name__ == '__main__':
  if len(sys.argv) < 3:
    print 'Too few arguments.'
    print USAGE
  if sys.argv[2].startswith('gs://'):
    upload(sys.argv)
  elif sys.argv[1].startswith('gs://'):
    download(sys.argv)
  else:
    print USAGE
