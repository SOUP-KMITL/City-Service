import requests
import os

AUTH_USER = os.environ.get("AUTH_USER", "16dd0556-0a33-43c3-94ce-213b854909b0")
AUTH_PASS = os.environ.get("AUTH_PASS", ("S6of8Ay3Q25MzDv6e3s5Qi6e7hItL317"
                                         "M68BxkRMZrbV1ae3ij9n9YJFgVXhqj7p"))
HOST = "https://cityservice.smartcity.kmitl.io/api/v1"
HOST_NS = HOST + "/namespaces/_"
HEADERS = {"Content-Type": "application/json"}


def createPackage(pname):
    data = {"namespace": "_", "name": pname}
    query = {"overwrite": False}

    try:
        resp = requests.put(
                HOST_NS + "/packages/" + pname,
                json=data,
                auth=(AUTH_USER, AUTH_PASS),
                params=query,
                headers=HEADERS)

        httpCode = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("createPackage: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("createPackage: connection to external service timeout")
        raise
    else:
        if httpCode != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("createPackage: " + error)
    finally:
        return httpCode


def deletePackage(pname):
    try:
        resp = requests.delete(
                HOST_NS + "/packages/" + pname,
                auth=(AUTH_USER, AUTH_PASS))

        httpCode = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("deletePackage: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("deletePackage: connection to external service timeout")
        raise
    else:
        if httpCode != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("deletePackage: " + error)
    finally:
        return httpCode


def updateAction(action, kind, code, overwrite):
    data = {
            "namespace": "_",
            "name": action,
            "exec": {
                "kind": kind,
                "code": code},
            }
    query = {"overwrite": overwrite}

    try:
        resp = requests.put(
                HOST_NS + "/actions/" + action,
                json=data,
                auth=(AUTH_USER, AUTH_PASS),
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
    finally:
        return httpCode


def deleteAction(action):
    try:
        resp = requests.delete(
                HOST_NS + "/actions/" + action,
                auth=(AUTH_USER, AUTH_PASS))

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
    finally:
        return httpCode
