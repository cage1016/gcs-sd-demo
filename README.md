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
