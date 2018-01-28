from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError
import requests
import uuid

# Custom modules and packages
import appconfig
import wskutil

app = Flask(__name__)
app.config.from_object("appconfig.DefaultConfig")
mongo = PyMongo(app)
wskutil.initSshSession(
        appconfig.SSH_HOST,
        appconfig.SSH_USER,
        appconfig.SSH_PRIV)


@app.route(appconfig.API_PREFIX, methods=['POST'])
def createService():
    retResp = {"success": False, "message": ""}

    if not request.is_json:
        retResp["message"] = "Invalid request body type, expected JSON"
        return jsonify(retResp), 500

    incomData = request.get_json()
    username = incomData.get("username", "")
    serviceName = incomData.get("serviceName", "")

    if not updateNamespace(username, 1):
        retResp["message"] = "Couldn't update/inset namespace " + username
        return jsonify(retResp), 500

    auth = mongo.db.namespace.find_one({"name": username}, {"_id": False})
    authUser = auth.get("authUser", "")
    authPass = auth.get("authPass", "")
    basePath = incomData.get("basePath", "")
    incomData["namespace"] = authUser

    if not insertService(incomData):
        retResp["message"] = "Service with basePath '" + \
                basePath + "' OR with serviceName '" + \
                serviceName + "' already exists"
        updateNamespace(username, -1)
        return jsonify(retResp), 400

    f = open(appconfig.TEMPLATE, "r")
    code = f.read()

    try:
        wskutil.createAction(authUser, authPass, serviceName, "nodejs:6", code)
        wskutil.createApi(
                authUser,
                authPass,
                serviceName,
                basePath,
                incomData.get("path", ""),
                "GET")
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    except Exception as e:
        retResp["message"] = e.args[1]
        return jsonify(retResp), e.args[0]

    retResp["message"] = "service " + serviceName + " is created."
    retResp["success"] = True

    return jsonify(retResp), 201


@app.route(appconfig.API_PREFIX + "/")
def getServices():
    services = None
    args = request.args

    if "userId" in args:
        services = mongo.db.service.find(
                {"userId": args.get("userId", "")},
                {"_id": False})
    else:
        services = mongo.db.service.find(projection={"_id": False})

    return jsonify(list(services)), 200


@app.route(appconfig.API_PREFIX + "/<serviceId>", methods=['DELETE'])
def deleteService(serviceId):
    retResp = {"success": False, "message": ""}

    service = mongo.db.service.find_one_and_delete({"serviceId": serviceId})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    auth = mongo.db.namespace.find_one(
            {"authUser": service.get("namespace", "")},
            {"_id": False})
    authUser = auth.get("authUser", "")
    authPass = auth.get("authPass", "")
    username = auth.get("name", "")
    serviceName = service.get("serviceName", "")

    try:
        wskutil.deleteApi(authUser, authPass, service.get("basePath", ""))
        wskutil.deleteAction(authUser, authPass, serviceName)
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    except Exception as e:
        retResp["message"] = e.args[1]
        return jsonify(retResp), e.args[0]

    if not updateNamespace(username, -1):
        retResp["message"] = "Couldn't update/delete namespace " + username
        return jsonify(retResp), 500

    retResp["success"] = True
    retResp["message"] = "Service " + serviceName + " is successfully deleted"

    return jsonify(retResp), 200


@app.route(appconfig.API_PREFIX + "/<serviceId>/")
def getService(serviceId):
    retResp = {"success": False, "message": ""}

    service = mongo.db.service.find_one(
            {"serviceId": serviceId},
            {"_id": False})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    return jsonify(service), 200


def updateNamespace(name, num):
    success = False

    updateResult = mongo.db.namespace.update_one(
        {"name": name},
        {"$inc": {"serviceCount": num}},
        upsert=True)

    if updateResult.upserted_id is not None:
        isCreated, authUser, authPass = wskutil.createUser(name)

        if isCreated:
            mongo.db.namespace.update_one(
                    {"name": name},
                    {"$set": {"authUser": authUser, "authPass": authPass}})
            success = True
    else:
        namespace = mongo.db.namespace.find_one(
                {"name": name},
                {"_id": False})

        if namespace.get("serviceCount", 0) == 0:
            mongo.db.namespace.delete_one({"name": name})
            isDeleted, result = wskutil.deleteUser(name)

            if isDeleted:
                success = True
        else:
            success = True

    return success


def insertService(data):
    try:
        mongo.db.service.insert_one(
                {
                    "serviceId": str(uuid.uuid1()),
                    "serviceName": data.get("serviceName", ""),
                    "namespace": data.get("namespace", ""),
                    "description": data.get("description", ""),
                    "basePath": data.get("basePath", ""),
                    "path": data.get("path", ""),
                    "icon": data.get("icon", ""),
                    "userId": data.get("userId", ""),
                    #  "example": data.get("example", ""),
                    #  "appLink": data.get("appLink", ""),
                    #  "videoLink": data.get("videoLink", ""),
                    #  "swaggerApi": data.get("swaggerApi", "")
                })
    except DuplicateKeyError:
        return False

    return True
