from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError
import requests
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
    else:
        services = mongo.db.service.find(projection={"_id": False})

    return jsonify(list(services)), 200


@app.route(appconfig.API_PREFIX, methods=['POST'])
def createService():
    retResp = {"success": False, "message": ""}
    validKeys = ["username", "serviceName",
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

    try:
        httpCode = None

        for i in range(2):
            httpCode = wskutil.updateAction(action, "nodejs:6", code, False)
            if httpCode == 200:
                break
            elif httpCode == 404 and i == 0:
                wskutil.createPackage(username)

    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    else:
        if httpCode != 200:
            retResp["message"] = ("Unknown external "
                                  "service error: ") + str(httpCode)
            return jsonify(retResp), 500

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


@app.route(appconfig.API_PREFIX + "/<serviceId>", methods=['DELETE'])
def deleteService(serviceId):
    retResp = {"success": False, "message": ""}

    service = mongo.db.service.find_one_and_delete({"serviceId": serviceId})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    username, serviceName, action = getAction(service)

    try:
        httpCode = wskutil.deleteAction(action)

        if httpCode == 200:
            httpCode = wskutil.deletePackage(username)

    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    else:
        if httpCode != 200 and httpCode != 409:
            retResp["message"] = ("Unknown external "
                                  "service error: ") + str(httpCode)
            return jsonify(retResp), 500

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

    service = updateService(serviceId, incomData)

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    if chcode:
        try:
            username, serviceName, action = getAction(service)
            code = base64.b64decode(incomData.get("code")).decode()
            httpCode = wskutil.updateAction(
                action, incomData.get("kind"), code, True)
        except (requests.ConnectionError, requests.ConnectTimeout) as e:
            retResp["message"] = e.__str__()
            return jsonify(retResp), 500
        except binascii.Error:
            retResp["message"] = "Invalid base64 encoded message"
            return jsonify(retResp), 400
        else:
            if httpCode != 200:
                retResp["message"] = ("Unknown external "
                                      "service error: ") + str(httpCode)
                return jsonify(retResp), 500

    retResp["success"] = True
    retResp["message"] = "service " + action + " is successfully updated"

    return jsonify(retResp), 200


def updateService(serviceId, data):
    service = mongo.db.service.find_one_and_update(
            {"serviceId": serviceId},
            {"$set": data},
            projection={"_id": False})

    return service


def insertService(data):
    try:
        mongo.db.service.insert_one(
                {
                    "serviceId": str(uuid.uuid1()),
                    "serviceName": data.get("serviceName", ""),
                    "description": data.get("description", ""),
                    "thumbnail": data.get("icon", ""),
                    "owner": data.get("username", ""),
                    "endpoint": "",
                })
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
    username = validateName(d.get("owner", d.get("username", "")))
    serviceName = validateName(d.get("serviceName", ""))
    action = username + "/" + serviceName

    return username, serviceName, action


def validateCode(d):
    if not ("code" in d and "kind" in d):
        d.pop("code", None)
        d.pop("kind", None)
        return False
    else:
        return True
