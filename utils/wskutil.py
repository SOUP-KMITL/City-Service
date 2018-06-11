import requests
import os

from .error import ServiceException

AUTH_USER = os.environ.get("AUTH_USER", "A-VALID-OPENWHISK-USER")
AUTH_PASS = os.environ.get("AUTH_PASS", "A-VALID-OPENWHISK-PASS")
HOST = "https://cityservice.smartcity.kmitl.io/api/v1"
HOST_NS = HOST + "/namespaces/_"
HEADERS = {"Content-Type": "application/json"}


def create_package(pname):
    data = {"namespace": "_", "name": pname}
    query = {"overwrite": False}

    try:
        resp = requests.put(
                HOST_NS + "/packages/" + pname,
                json=data,
                auth=(AUTH_USER, AUTH_PASS),
                params=query,
                headers=HEADERS)

        http_code = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("create_package: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("create_package: connection to external service timeout")
        raise
    else:
        if http_code != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("create_package: " + error)
            raise ServiceException(http_code, error)


def delete_package(pname):
    try:
        resp = requests.delete(
                HOST_NS + "/packages/" + pname,
                auth=(AUTH_USER, AUTH_PASS))

        http_code = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("delete_package: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("delete_package: connection to external service timeout")
        raise
    else:
        if http_code != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("delete_package: " + error)
            raise ServiceException(http_code, error)


def update_action(action, kind, code, overwrite):
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

        http_code = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("update_action: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("update_action: connection to external service timeout")
        raise
    else:
        if http_code != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("update_action: " + error)
            raise ServiceException(http_code, error)


def delete_action(action):
    try:
        resp = requests.delete(
                HOST_NS + "/actions/" + action,
                auth=(AUTH_USER, AUTH_PASS))

        http_code = resp.status_code
        result = resp.json()

    except requests.ConnectionError:
        print("delete_action: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("delete_action: connection to external service timeout")
        raise
    else:
        if http_code != 200:
            error = result.get("error", "Couldn't find error") + \
                    " => " + str(result.get("code", 0))
            print("delete_action: " + error)
            raise ServiceException(http_code, error)


def invoke_action(action, params):
    query = {"blocking": True, "result": True}

    try:
        resp = requests.post(
                HOST_NS + "/actions/" + action,
                json=params,
                auth=(AUTH_USER, AUTH_PASS),
                params=query,
                headers=HEADERS)

    except requests.ConnectionError:
        print("invoke_action: couldn't connect to external service")
        raise
    except requests.ConnectTimeout:
        print("invoke_action: connection to external service timeout")
        raise
    else:
        return resp.status_code, resp.json()
