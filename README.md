Google Cloud Storage Sample
===========================

fork from [google-cloud-platform-samples](https://code.google.com/p/google-cloud-platform-samples/source/browse/file-transfer-json/chunked_transfer.py?repo=storage)

#### Install google api python client library

```sh
pip install google-api-python-client==1.4.0
```

#### Create Service Account

1.	Click **APIs & Auth** > **credential**.
2.	Click **Click new Client ID**.
3.	Choose **Service Account**.
4.	Key type : **P12 Key**
5.	Click **Create Client ID**
6.	**P12.Key**

### Create GCS bucket

1.	Click **Storage** > **Cloud Storage** > **Storage browser**.
2.	Click **Create bucket**.
3.	Fill bucket **Name**
4.	Storage class: choose **NearLine**
5.	Location: choose what you want.

#### Modify google cloud storage authentication settings.

```python
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
```

#### Usage

```sh
# upload
python chunked_transfer.py ./chunked_transfer.py gs://nearline-sd-test//chunked_transfer.py

# download
python chunked_transfer.py gs://nearline-sd-test//chunked_transfer.py ./c.py
```

#### [2015/4/22 update] measure http request time

```python
@timeit
def download_with_timer(argv):

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
```

add `@timeit` decorator, `MyMediaIoBaseDownload` (fork from apiclient.http without chucked download) and httplib patch to measure http response time.

#### Testing

#####Testing Env

-	n1-standard-1
-	us-central1-f

#####Testing parameters

-	files[0]="Hallstatt, Austria.jpg" #4.37.59KB
-	files[1]="HBase Essentials.pdf" #2.06MB
-	files[2]="Google BigQuery Analytics.pdf" # 8.35mb

try to download **3** files **10** times from standard bucket and nearline bucket

[GCS standard vs nearline testing on GCE](https://docs.google.com/spreadsheets/d/1k5AiFiu-QScr2n2ys5Aa-XMF0qvBRD9KIE05tA2_qS8/edit?usp=sharing)
