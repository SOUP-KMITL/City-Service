import paramiko
import requests
import json

sshclient = None
HOST = "https://cityservice.smartcity.kmitl.io/api/v1"
HOST_NS = HOST + "/namespaces/_"
HEADERS = {"Content-Type": "application/json"}


def initSshSession(host, user, priv):
    global sshclient

    key = paramiko.RSAKey.from_private_key_file(priv)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
            hostname=host,
            username=user,
            pkey=key)
    sshclient = client


# It is meant to be called only with ONE command!
def execCommand(cmd):
    cmd = cmd + "; echo $?"
    ssh_stdin, ssh_stdout, ssh_stderr = sshclient.exec_command(cmd)
    output = ssh_stdout.read().decode()

    # Get output of each command separated by '\n'
    output = output.split("\n")
    success = not bool(int(output[1]))

    return success, output[0]


def createUser(uname):
    username = None
    password = None
    cmd = "wskadmin user create " + uname

    success, result = execCommand(cmd)

    if success:
        output = result.split(":")
        username = output[0]
        password = output[1]

    return success, username, password


def deleteUser(username):
    cmd = "wskadmin user delete " + username
    success, result = execCommand(cmd)

    return success, result


def createAction(authUser, authPass, actionName, kind, code):
    httpCode = 400
    data = {
            "namespace": "_",
            "name": actionName,
            "exec": {
                "kind": kind,
                "code": code},
            "annotations": [
                {"key": "web-export", "value": True},
                {"key": "raw-http", "value": False},
                {"key": "final", "value": True}]
            }
    try:
        resp = requests.put(
                HOST_NS + "/actions/" + actionName,
                json=data,
                auth=(authUser, authPass),
                headers=HEADERS)

        httpCode = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("createAction: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("createAction: connection to external service timeout")
        raise
    else:
        if httpCode != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("createAction: " + error)
            raise Exception(httpCode, error)


# All capitalized characters for <method>
def createApi(authUser, authPass, actionName, basePath, path, method):
    backendUrl = HOST + "/web/_/default/" + actionName + ".http"
    data = {
            "apidoc": {
                "namespace": "_",
                "gatewayBasePath": basePath,
                "gatewayPath": path,
                "gatewayMethod": method,
                "id": "API:_:" + basePath,
                "action": {
                    "name": actionName,
                    "namespace": "_",
                    "backendMethod": method,
                    "backendUrl": backendUrl,
                    "authkey": authUser + ":" + authPass
                    }
                }
            }
    try:
        resp = requests.post(
                HOST + ("/web/whisk.system/apimgmt/"
                        "createApi.http?accesstoken=DUMMY+TOKEN&"
                        "responsetype=json&spaceguid=") + authUser,
                json=data,
                auth=(authUser, authPass),
                headers=HEADERS)

        httpCode = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("createApi: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("createApi: connection to external service timeout")
        raise
    else:
        if httpCode != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("createApi: " + error)
            raise Exception(httpCode, error)
