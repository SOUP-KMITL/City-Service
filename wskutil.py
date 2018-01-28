import paramiko
***REMOVED***
import json

sshclient = None
***REMOVED***
***REMOVED***
***REMOVED***


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
***REMOVED***
***REMOVED***
            "name": actionName,
***REMOVED***
***REMOVED***
***REMOVED***
            "annotations": [
                {"key": "web-export", "value": True},
                {"key": "raw-http", "value": False},
                {"key": "final", "value": True}]
***REMOVED***
***REMOVED***
***REMOVED***
                HOST_NS + "/actions/" + actionName,
***REMOVED***
                auth=(authUser, authPass),
***REMOVED***

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("createAction: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("createAction: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("createAction: " + error)
    ***REMOVED*** Exception(httpCode, error)


# All capitalized characters for <method>
def createApi(authUser, authPass, actionName, basePath, path, method):
    backendUrl = HOST + "/web/_/default/" + actionName + ".http"
***REMOVED***
            "apidoc": {
    ***REMOVED***
                "gatewayBasePath": basePath,
                "gatewayPath": path,
                "gatewayMethod": method,
                "id": "API:_:" + basePath,
                "action": {
                    "name": actionName,
        ***REMOVED***
                    "backendMethod": method,
                    "backendUrl": backendUrl,
                    "authkey": authUser + ":" + authPass
        ***REMOVED***
    ***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
                HOST + ("/web/whisk.system/apimgmt/"
                        "createApi.http?accesstoken=DUMMY+TOKEN&"
                        "responsetype=json&spaceguid=") + authUser,
***REMOVED***
                auth=(authUser, authPass),
***REMOVED***

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("createApi: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("createApi: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("createApi: " + error)
    ***REMOVED*** Exception(httpCode, error)
