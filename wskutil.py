from urllib.parse import quote
import paramiko
***REMOVED***

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


def updateAction(authUser, authPass, actionName, kind, code, overwrite):
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
***REMOVED***
                HOST_NS + "/actions/" + actionName,
***REMOVED***
                auth=(authUser, authPass),
***REMOVED***
***REMOVED***

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("updateAction: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("updateAction: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("updateAction: " + error)
    ***REMOVED*** Exception(httpCode, error)


def deleteAction(authUser, authPass, actionName):
***REMOVED***
***REMOVED***
                HOST_NS + "/actions/" + actionName,
                auth=(authUser, authPass))

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("deleteAction: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("deleteAction: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("deleteAction: " + error)
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


def deleteApi(authUser, authPass, basePath):
    middleUrl = ("/web/whisk.system/apimgmt/deleteApi.http?"
                 "accesstoken=DUMMY+TOKEN&basepath=")
    tailUrl = quote(basePath) + "&spaceguid=" + authUser
***REMOVED***
***REMOVED***
                HOST + middleUrl + tailUrl,
                auth=(authUser, authPass))

        httpCode = resp.status_code
***REMOVED***

***REMOVED***
        print("deleteApi: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("deleteApi: connection to external service timeout")
***REMOVED***
***REMOVED***
        if httpCode != 200:
***REMOVED***
***REMOVED***
            print("deleteApi: " + error)
    ***REMOVED*** Exception(httpCode, error)
