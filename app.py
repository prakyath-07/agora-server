from flask import Flask, render_template, jsonify, request
import json
from flask_cors import CORS

from utils import start_cloud_recording, stop_cloud_recording, start_transcription, stop_transcription, query_cloud_recording

app = Flask(__name__)
CORS(app)


@app.route('/',)
def endpoints():
    app_routes = ['/start-recording/<channel>',
                  '/stop-recording/<channel>/<sid>/<resource_id>', '/start-transcribing/<channel>', '/stop-transcribing/<task_id>/<builder_token>']
    return jsonify(app_routes)


@app.route('/start-recording/<path:channel>', methods=['GET', 'POST'])
def start_recording(channel):
    uid = request.args.get("uid", None)
    project = request.args.get("project", 'agora')
    temp_token = request.args.get("temp_token", 'agora')
    context = start_cloud_recording(channel,temp_token, uid, project)
    return jsonify(context)

@app.route('/query-recording/<path:channel>/<path:sid>', methods=['GET', 'POST'])
def query_recording(channel, sid):
    context = query_cloud_recording(channel, sid)
    return jsonify(context)


@app.route('/stop-recording/<path:channel>/<path:sid>', methods=['GET', 'POST'])
def stop_recording(channel, sid,):
    data = stop_cloud_recording(channel, sid)
    return jsonify(data)

# @app.route('/users/<path:channel>', methods=['GET', 'POST'])
# def users(channel):
#     data = get_user_list(channel)
#     return jsonify(data)


@app.route('/start-transcribing/<path:channel>', methods=['GET', 'POST'])
def start_transcribing(channel):
    context = start_transcription(channel)
    return jsonify(context)


@app.route('/stop-transcribing/<path:task_id>/<path:builder_token>/', methods=['GET', 'POST', 'DELETE'])
def stop_transcribing(task_id, builder_token):
    data = stop_transcription(task_id, builder_token)
    context = {}
    return jsonify(data)


if __name__ == '__main__':
    app.run(debug=True)
