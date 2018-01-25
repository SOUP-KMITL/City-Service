from flask import Flask, request, jsonify
#  from flask_pymongo import PyMongo
#  ***REMOVED***
#  import time
#  import uuid
import paramiko

# Custom modules and packages
import appconfig

app = Flask(__name__)
app.config.from_object("appconfig.DefaultConfig")
#  mongo = PyMongo(app)
key = paramiko.RSAKey.from_private_key_file("./cityservice_key")
sshclient = paramiko.SSHClient()
sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
sshclient.connect(
        hostname="cityservice.smartcity.kmitl.io",
        username="ubuntu",
        pkey=key)


@app.route(appconfig.API_PREFIX + "/", methods=['POST'])
def createService():
    retResp = {"success": False, "message": ""}
    httpCode = 400

    if not request.is_json:
        retResp["message"] = "Invalid request body type, expected JSON"
        return jsonify(retResp), httpCode

    incomData = request.get_json()
    username = incomData.get("username", "")

    isCreated, name, pswd = createOpenWhiskUser(username)

    retResp = {
            "isCreated": isCreated,
            "username": name,
            "password": pswd
    }

    httpCode = 200

    return jsonify(retResp), httpCode


@app.route(appconfig.API_PREFIX + "/<serviceId>/", methods=['GET', 'DELETE'])
def deleteService(serviceId):
    retResp = {"success": False, "message": ""}
    httpCode = 400

    if request.method == 'GET':
        retResp["message"] = "Recieve only DELETE message for now"
        return jsonify(retResp), httpCode

    isDeleted, result = deleteOpenWhiskUser(serviceId)

    if not isDeleted:
        retResp["message"] = result
        return jsonify(retResp), httpCode

    retResp["success"] = True
    retResp["message"] = result

    httpCode = 200

    return jsonify(retResp), httpCode


def createOpenWhiskUser(uname):
    username = None
    password = None
    cmd = "wskadmin user create " + uname

    success, result = execCommand(cmd)

    if success:
        output = result.split(":")
        username = output[0]
        password = output[1]

    return success, username, password


def deleteOpenWhiskUser(username):
    cmd = "wskadmin user delete " + username
    success, result = execCommand(cmd)

    return success, result


# It is meant to be called only with ONE command!
def execCommand(cmd):
    cmd = cmd + "; echo $?"
    ssh_stdin, ssh_stdout, ssh_stderr = sshclient.exec_command(cmd)
    output = ssh_stdout.read().decode()

    # Get output of each command separated by '\n'
    output = output.split("\n")
    success = not bool(int(output[1]))

    return success, output[0]
