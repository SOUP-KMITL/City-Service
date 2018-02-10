from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError
***REMOVED***
import uuid
import base64
import binascii

# Custom modules and packages
import appconfig
import wskutil

app = Flask(__name__)
app.config.from_object("appconfig.DefaultConfig")
mongo = PyMongo(app)


@app.route(appconfig.API_PREFIX)
def getServices():
    services = None
    args = request.args

    if "owner" in args:
        services = mongo.db.service.find(
                {"owner": args.get("owner")},
                {"_id": False})
***REMOVED***
        services = mongo.db.service.find(projection={"_id": False})

    return jsonify(list(services)), 200


@app.route(appconfig.API_PREFIX, methods=["POST"])
def createService():
    retResp = {"success": False, "message": ""}
    validKeys = ["owner", "serviceName",
                 "thumbnail", "description"]
    requiredKeys = validKeys[:-2]

    if not request.is_json:
        retResp["message"] = "Invalid request body type, expected JSON"
        return jsonify(retResp), 400

    incomData = request.get_json()
    validateParams(incomData, validKeys)

    if not all(key in incomData for key in requiredKeys):
        retResp["message"] = "Required fileds are missing: " + \
                ", ".join(requiredKeys)
        return jsonify(retResp), 400

    username, serviceName, action = getAction(incomData)

    if not insertService(incomData):
        retResp["message"] = "Service " + action + " already exists"
        return jsonify(retResp), 409

    f = open(appconfig.TEMPLATE, "r")
    code = f.read()

    for i in range(2):
    ***REMOVED***
            if i == 1:
                wskutil.createPackage(username)
            wskutil.updateAction(action, "nodejs:6", code, False)
        except (requests.ConnectionError, requests.ConnectTimeout) as e:
            retResp["message"] = e.__str__()
            return jsonify(retResp), 500
        except Exception as e:
            httpCode = e.args[0]
            if i == 1 or httpCode != 404:
                retResp["message"] = e.args[1]
                return jsonify(retResp), httpCode

    retResp["message"] = "service " + action + " is successfully created."
    retResp["success"] = True

    return jsonify(retResp), 201


@app.route(appconfig.API_PREFIX + "/<serviceId>")
def getService(serviceId):
    retResp = {"success": False, "message": ""}

    service = mongo.db.service.find_one(
            {"serviceId": serviceId},
            {"_id": False})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    return jsonify(service), 200


@app.route(appconfig.API_PREFIX + "/<serviceId>", methods=["DELETE"])
def deleteService(serviceId):
    retResp = {"success": False, "message": ""}

    service = mongo.db.service.find_one_and_delete({"serviceId": serviceId})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    username, serviceName, action = getAction(service)

***REMOVED***
        wskutil.deleteAction(action)
        wskutil.deletePackage(username)
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    except Exception as e:
        httpCode = e.args[0]
        if httpCode != 409:
            retResp["message"] = e.args[1]
            return jsonify(retResp), httpCode

    retResp["success"] = True
    retResp["message"] = "Service " + action + " is successfully deleted"

    return jsonify(retResp), 200


@app.route(appconfig.API_PREFIX + "/<serviceId>", methods=["PATCH"])
def patchService(serviceId):
    retResp = {"success": False, "message": ""}
    validKeys = [
        "description", "thumbnail", "endpoint",
        "sampleData", "appLink", "videoLink", "swagger",
        ##################################
        "code", "kind",
    ]

    if not request.is_json:
        retResp["message"] = "Invalid request body type, expected JSON"
        return jsonify(retResp), 400

    incomData = request.get_json()
    validateParams(incomData, validKeys)
    chcode = validateCode(incomData)

    if len(incomData) == 0:
        retResp["message"] = "No required fields found"
        return jsonify(retResp), 400

    code, kind, service = updateService(serviceId, incomData)

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    username, serviceName, action = getAction(service)

    if chcode:
        code = base64.b64decode(code).decode()

    ***REMOVED***
            wskutil.updateAction(action, kind, code, True)
        except (requests.ConnectionError, requests.ConnectTimeout) as e:
            retResp["message"] = e.__str__()
            return jsonify(retResp), 500
        except binascii.Error:
            retResp["message"] = "Invalid base64 encoded message"
            return jsonify(retResp), 400
        except Exception as e:
            retResp["message"] = e.args[1]
            return jsonify(retResp), e.args[0]

    retResp["success"] = True
    retResp["message"] = "service " + action + " is successfully updated"

    return jsonify(retResp), 200


@app.route(appconfig.API_PREFIX + "/<serviceId>/activations", methods=["POST"])
def invokeService(serviceId):
    retResp = {"success": False, "message": ""}
    params = None

    if request.is_json:
        params = request.get_json()

    service = mongo.db.service.find_one(
        {"serviceId": serviceId},
        {"_id": False})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    username, serviceName, action = getAction(service)

***REMOVED***
        httpCode, data = wskutil.invokeAction(action, params)
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    except Exception as e:
        retResp["message"] = e.args[1]
        return jsonify(retResp), e.args[0]
***REMOVED***
        retResp = data

    return jsonify(retResp), 200


@app.route(appconfig.API_PREFIX + "/<serviceId>/data")
def getDataService(serviceId):
    retResp = {"success": False, "message": ""}
    service = mongo.db.service.find_one(
        {"serviceId": serviceId},
        {"_id": False})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    username, serviceName, action = getAction(service)

***REMOVED***
        httpCode, data = wskutil.invokeAction(action, None)
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    except Exception as e:
        retResp["message"] = e.args[1]
        return jsonify(retResp), e.args[0]
***REMOVED***
        retResp = data

    return jsonify(retResp), 200


def updateService(serviceId, data):
    code = data.pop("code", None)
    kind = data.pop("kind", None)
    service = None

    if data:
        service = mongo.db.service.find_one_and_update(
            {"serviceId": serviceId},
            {"$set": data},
            projection={"_id": False})
***REMOVED***
        service = mongo.db.service.find_one(
            {"serviceId": serviceId},
            {"_id": False})

    return code, kind, service


def insertService(data):
***REMOVED***
        mongo.db.service.insert_one(
                {
                    "serviceId": str(uuid.uuid1()),
                    "serviceName": data.get("serviceName", ""),
                    "description": data.get("description", ""),
                    "thumbnail": data.get("thumbnail", None),
                    "owner": data.get("owner", ""),
                    "endpoint": None,
    ***REMOVED***)
    except DuplicateKeyError:
        return False

    return True


def validateParams(d, vkeys):
    invalidKeys = []

    for key, value in d.items():
        if key not in vkeys or not value:
            invalidKeys.append(key)

    for key in invalidKeys:
        d.pop(key)


def validateName(name):
    return name.replace(" ", "-")


def getAction(d):
    username = validateName(d.get("owner", ""))
    serviceName = validateName(d.get("serviceName", ""))
    action = username + "/" + serviceName

    return username, serviceName, action


def validateCode(d):
    if not ("code" in d and "kind" in d):
        d.pop("code", None)
        d.pop("kind", None)
        return False
***REMOVED***
        return True
