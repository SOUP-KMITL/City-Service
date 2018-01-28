from flask import Flask, request, jsonify
from flask_pymongo import PyMongo
from pymongo.errors import DuplicateKeyError
***REMOVED***
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


@app.route(appconfig.API_PREFIX + "/", methods=['POST'])
def createService():
    retResp = {"success": False, "message": ""}

    if not request.is_json:
        retResp["message"] = "Invalid request body type, expected JSON"
        return jsonify(retResp), 500

    incomData = request.get_json()
    username = incomData.get("username", "")
    serviceName = incomData.get("serviceName", "")
    incomData["namespace"] = username

    if not insertService(incomData):
        retResp["message"] = "Service " + serviceName + " already exists"
        return jsonify(retResp), 400

    if not updateNamespace(username, 1):
        retResp["message"] = "Couldn't update/inset namespace " + username
        return jsonify(retResp), 500

    auth = mongo.db.namespace.find_one({"name": username}, {"_id": False})
    f = open(appconfig.TEMPLATE, "r")
    #  code = repr(f.read())
    code = f.read()

***REMOVED***
        wskutil.createAction(
                auth.get("authUser", ""),
                auth.get("authPass", ""),
                serviceName, "nodejs:6", code)
        wskutil.createApi(
                auth.get("authUser", ""),
                auth.get("authPass", ""),
                serviceName,
                incomData.get("basePath", "/base"),
                incomData.get("path", "/path"), "GET")
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    except Exception as e:
        retResp["message"] = e.args[1]
        return jsonify(retResp), e.args[0]

    retResp["message"] = "service " + serviceName + " is created."
    retResp["success"] = True

    return jsonify(retResp), 201


@app.route(appconfig.API_PREFIX + "/<serviceId>/", methods=['DELETE'])
def deleteService(serviceId):
    retResp = {"success": False, "message": ""}

    service = mongo.db.service.find_one_and_delete({"serviceId": serviceId})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 400

    namespace = service.get("namespace", "")

    if not updateNamespace(namespace, -1):
        retResp["message"] = "Couldn't update/delete namespace " + namespace
        return jsonify(retResp), 500

    retResp["success"] = True
    retResp["message"] = "Service " + \
        service.get("serviceName", "") + \
        " is successfully deleted"

    return jsonify(retResp), 200


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
***REMOVED***
        namespace = mongo.db.namespace.find_one(
                {"name": name},
                {"_id": False})

        if namespace.get("serviceCount", 0) == 0:
            mongo.db.namespace.delete_one({"name": name})
            isDeleted, result = wskutil.deleteUser(name)

            if isDeleted:
                success = True
    ***REMOVED***
            success = True

    return success


def insertService(data):
***REMOVED***
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
    ***REMOVED***)
    except DuplicateKeyError:
        return False

    return True
