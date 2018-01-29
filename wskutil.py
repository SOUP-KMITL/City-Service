from urllib.parse import quote
import paramiko
import requests

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


def updateAction(authUser, authPass, actionName, kind, code, overwrite):
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
    query = {"overwrite": overwrite}

    try:
        resp = requests.put(
                HOST_NS + "/actions/" + actionName,
                json=data,
                auth=(authUser, authPass),
                params=query,
                headers=HEADERS)

        httpCode = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("updateAction: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("updateAction: connection to external service timeout")
        raise
    else:
        if httpCode != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("updateAction: " + error)
            raise Exception(httpCode, error)


def deleteAction(authUser, authPass, actionName):
    try:
        resp = requests.delete(
                HOST_NS + "/actions/" + actionName,
                auth=(authUser, authPass))

        httpCode = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("deleteAction: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("deleteAction: connection to external service timeout")
        raise
    else:
        if httpCode != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("deleteAction: " + error)
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


def deleteApi(authUser, authPass, basePath):
    middleUrl = ("/web/whisk.system/apimgmt/deleteApi.http?"
                 "accesstoken=DUMMY+TOKEN&basepath=")
    tailUrl = quote(basePath) + "&spaceguid=" + authUser
    try:
        resp = requests.delete(
                HOST + middleUrl + tailUrl,
                auth=(authUser, authPass))

        httpCode = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("deleteApi: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("deleteApi: connection to external service timeout")
        raise
    else:
        if httpCode != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("deleteApi: " + error)
            raise Exception(httpCode, error)
