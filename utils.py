import base64
import requests
import json
import random
import os
import boto3

# import dotenv
# from dotenv import load_dotenv

# load_dotenv()

CUSTOMER_KEY = os.getenv('CUSTOMER_KEY')
CUSTOMER_SECRET = os.getenv('CUSTOMER_SECRET')

TEMP_TOKEN = os.getenv('TEMP_TOKEN')
APP_ID = os.getenv('APP_ID')
APP_CERTIFICATE = os.getenv('APP_CERTIFICATE')
UID = str(random.randint(1, 12500))
RESOURCE_ID = None

SECRET_KEY = os.getenv('SECRET_KEY')
ACCESS_KEY = os.getenv('ACCESS_KEY')
BUCKET_NAME = os.getenv('BUCKET_NAME')


def generate_credential():
    # Generate encoded token based on customer key and secret
    credentials = CUSTOMER_KEY + ":" + CUSTOMER_SECRET #"{}:{}".format(CUSTOMER_KEY,CUSTOMER_SECRET)#

    base64_credentials = base64.b64encode(credentials.encode("utf8"))
    credential = base64_credentials.decode("utf8")
    return credential


credential = generate_credential()


def generate_resource(channel):

    payload = {
        "cname": channel,
        "uid": str(UID),
        "clientRequest": {
            "resourceExpiredHour": 24,
            "scene": 0
        }
    }

    headers = {}

    headers['Authorization'] = 'basic ' + credential

    headers['Content-Type'] = 'application/json'
    headers['Access-Control-Allow-Origin'] = '*'

    url = f"https://api.agora.io/v1/apps/{APP_ID}/cloud_recording/acquire"
    res = requests.post(url, headers=headers, data=json.dumps(payload))

    data = res.json()

    return data


def start_cloud_recording(channel,temp_token, uid, project):
    global UID
    global RESOURCE_ID
    
    # if uid is not None:
    #     UID = uid
    resource_data = generate_resource(channel)
    if 'resourceId' not in resource_data:
        return {'success': False, 'message': "resourceId not found", 'server_response': resource_data, 'channel': channel}
    RESOURCE_ID = resource_data["resourceId"]
    url = f"https://api.agora.io/v1/apps/{APP_ID}/cloud_recording/resourceid/{RESOURCE_ID}/mode/mix/start"
    payload = {
        "cname": channel,
        "uid": UID,
        "clientRequest": {
            "token": TEMP_TOKEN,

            "recordingConfig": {
                "maxIdleTime": 30,
                "streamTypes": 0,
                "channelType": 0,
                "videoStreamType": 0,
                "subscribeUidGroup": 0
            },

            "storageConfig": {
                "secretKey": SECRET_KEY,
                "vendor": 1,  # 1 is for AWS
                "region": 0,
                "bucket": BUCKET_NAME,
                "accessKey": ACCESS_KEY,
                "fileNamePrefix": [
                    "agora",
                    project
                ]
            },

            "recordingFileConfig": {
                "avFileType": [
                    "hls",
                    "mp4"
                ]
            },
        },
    }

    headers = {}

    headers['Authorization'] = 'basic ' + credential

    headers['Content-Type'] = 'application/json'
    headers['Access-Control-Allow-Origin'] = '*'

    res = requests.post(url, headers=headers, data=json.dumps(payload))
    data = res.json()

    if 'code' in data:
        return {'success': False, 'message': "Start Failed", 'server_response': data, 'channel': channel}
    sid = data["sid"]
    print('sid '+ sid+ " resource_id "+RESOURCE_ID)
    return {'success': True, 'sid': sid, "resource_id": RESOURCE_ID}


def query_cloud_recording(channel, sid):
    url = f"https://api.agora.io/v1/apps/{APP_ID}/cloud_recording/resourceid/{RESOURCE_ID}/sid/{sid}/mode/mix/query"
    payload = {}

    headers = {}

    headers['Authorization'] = 'basic ' + credential

    headers['Content-Type'] = 'application/json'
    headers['Access-Control-Allow-Origin'] = '*'

    res = requests.get(url, headers=headers, data=json.dumps(payload))
    data = res.json()

    if 'serverResponse' not in data or len(data['serverResponse']['fileList']) == 0:
        return {'success': False, 'message': "Parsing Failed", 'server_response': data, 'channel': channel}

    return {'success': True, "fileList": data['serverResponse']['fileList'], "status": data['serverResponse']['status'], 'sid': sid}


def stop_cloud_recording(channel, sid):
    global RESOURCE_ID
    url = f"https://api.agora.io/v1/apps/{APP_ID}/cloud_recording/resourceid/{RESOURCE_ID}/sid/{sid}/mode/mix/stop"

    headers = {}

    headers['Authorization'] = 'basic ' + credential

    headers['Content-Type'] = 'application/json;charset=utf-8'
    headers['Access-Control-Allow-Origin'] = '*'

    payload = {
        "cname": channel,
        "uid": str(UID),
        "clientRequest": {
        }
    }

    res = requests.post(url, headers=headers, data=json.dumps(payload))
    data = res.json()

    if 'serverResponse' not in data or len(data['serverResponse']['fileList']) == 0:
        return {'success': False, 'message': "Parsing Failed", 'server_response': data, 'channel': channel}

    resource_id = data['resourceId']
    sid = data['sid']
    server_response = data['serverResponse']
    mp4_link = server_response['fileList'][0]['fileName']
    m3u8_link = server_response['fileList'][1]['fileName']

    formatted_data = {'success': True, 'resource_id': resource_id, 'sid': sid,
                      'mp4_link': mp4_link, 'm3u8_link': m3u8_link, 'signed_mp4_link': create_presigned_url(mp4_link)}

    return formatted_data


def rtt_generate_resource(channel):

    payload = {
        "instanceId": 'asdda',
    }

    headers = {}

    headers['Authorization'] = 'basic ' + credential

    headers['Content-Type'] = 'application/json'
    headers['Access-Control-Allow-Origin'] = '*'

    url = f"https://api.agora.io/v1/projects/{APP_ID}/rtsc/speech-to-text/builderTokens"
    res = requests.post(url, headers=headers, data=json.dumps(payload))

    data = res.json()
    return data


def start_transcription(channel):
    builderTokens = rtt_generate_resource(channel)
    tokenName = builderTokens["tokenName"]
    url = f"https://api.agora.io/v1/projects/{APP_ID}/rtsc/speech-to-text/tasks?builderToken={tokenName}"
    payload = {
        "audio": {
            "subscribeSource": "AGORARTC",
            "agoraRtcConfig": {
                "channelName": channel,
                "uid": str(UID),
                # "token": "{{channelToken}}",
                "channelType": "LIVE_TYPE",
                "subscribeConfig": {
                    "subscribeMode": "CHANNEL_MODE"
                },
                "maxIdleTime": 60
            }
        },
        "config": {
            "features": [
                "RECOGNIZE"
            ],
            "recognizeConfig": {
                "language": "en-US,es-ES",
                "model": "Model",
                "output": {
                    "destinations": [
                        "AgoraRTCDataStream",
                        "Storage"
                    ],
                    "agoraRTCDataStream": {
                        "channelName": channel,
                        "uid": "101",
                        # "token": "{{channelToken}}"
                    },
                    "cloudStorage": [
                        {
                            "format": "HLS",
                            "storageConfig": {
                                "accessKey": ACCESS_KEY,
                                "secretKey": SECRET_KEY,
                                "bucket": BUCKET_NAME,
                                "vendor": 1,
                                "region": 1,
                                "fileNamePrefix": [
                                    "rtt"
                                ]
                            }
                        }
                    ]
                }
            }
        }
    }

    headers = {}

    headers['Authorization'] = 'basic ' + credential

    headers['Content-Type'] = 'application/json'

    res = requests.post(url, headers=headers, data=json.dumps(payload))
    data = res.json()
    if 'taskId' not in data:
        return {'success': False, 'message': "Parsing Failed", 'server_response': data, 'builderTokens': builderTokens}
    taskID = data["taskId"]

    return {'taskId': taskID, 'builderToken': tokenName}


def stop_transcription(task_id, builder_token):
    url = f"https://api.agora.io/v1/projects/{APP_ID}/rtsc/speech-to-text/tasks/{task_id}?builderToken={builder_token}"

    headers = {}

    headers['Authorization'] = 'basic ' + credential

    headers['Content-Type'] = 'application/json'

    payload = {}

    res = requests.delete(url, headers=headers, data=payload)
    data = res.json()
    return data


def create_presigned_url(object):
    try:
        key = object
        location = boto3.client('s3', aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY).get_bucket_location(
            Bucket=BUCKET_NAME)['LocationConstraint']
        s3_client = boto3.client(
            's3',
            region_name=location,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
        )
        url = s3_client.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': key, },
            ExpiresIn=600000,
        )
    except Exception as e:
        print(e)
        return None
    return url
