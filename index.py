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
wskutil.initSshSession(
        appconfig.SSH_HOST,
        appconfig.SSH_USER,
        appconfig.SSH_PRIV)


@app.route(appconfig.API_PREFIX + "/")
def getServices():
    services = None
    args = request.args

    if "userId" in args:
        services = mongo.db.service.find(
                {"userId": args.get("userId", "")},
                {"_id": False})
***REMOVED***
        services = mongo.db.service.find(projection={"_id": False})

    return jsonify(list(services)), 200


@app.route(appconfig.API_PREFIX + "/", methods=['POST'])
def createService():
    retResp = {"success": False, "message": ""}
    validKeys = [
            "username", "serviceName", "userId",
            "path", "basePath", "description", "icon"
            ]
    requiredKeys = validKeys[:-3]

    if not request.is_json:
        retResp["message"] = "Invalid request body type, expected JSON"
        return jsonify(retResp), 400

    incomData = request.get_json()

    if not all(key in incomData for key in requiredKeys):
        retResp["message"] = "Required fileds are missing: " + \
                ", ".join(requiredKeys)
        return jsonify(retResp), 400

    validateParams(incomData, validKeys)
    basePath = incomData.get("basePath", "/")
    username = incomData.get("username")
    serviceName = incomData.get("serviceName")
    success, authUser, authPass = updateNamespace("name", username, 1)

    if not success:
        retResp["message"] = "Couldn't update/insert namespace for " + username
        return jsonify(retResp), 500
***REMOVED***
        incomData["namespace"] = authUser

    if not insertService(incomData):
        retResp["message"] = "Service with basePath '" + \
                basePath + "' OR with serviceName '" + \
                serviceName + "' already exists"
        updateNamespace("name", username, -1)
        return jsonify(retResp), 400

    f = open(appconfig.TEMPLATE, "r")
    code = f.read()

***REMOVED***
        wskutil.updateAction(
                authUser,
                authPass,
                serviceName,
                "nodejs:6",
                code,
                False)
        wskutil.createApi(
                authUser,
                authPass,
                serviceName,
                basePath,
                incomData.get("path"),
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


@app.route(appconfig.API_PREFIX + "/<serviceId>/", methods=['DELETE'])
def deleteService(serviceId):
    retResp = {"success": False, "message": ""}

    service = mongo.db.service.find_one_and_delete({"serviceId": serviceId})

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    success, authUser, authPass = updateNamespace(
            "authUser",
            service.get("namespace"), -1)

    if not success:
        retResp["message"] = "Couldn't update/delete namespace " + authUser
        return jsonify(retResp), 500

    serviceName = service.get("serviceName")

***REMOVED***
        wskutil.deleteApi(authUser, authPass, service.get("basePath", ""))
        wskutil.deleteAction(authUser, authPass, serviceName)
    except (requests.ConnectionError, requests.ConnectTimeout) as e:
        retResp["message"] = e.__str__()
        return jsonify(retResp), 500
    except Exception as e:
        retResp["message"] = e.args[1]
        return jsonify(retResp), e.args[0]

    retResp["success"] = True
    retResp["message"] = "Service " + serviceName + " is successfully deleted"

    return jsonify(retResp), 200


@app.route(appconfig.API_PREFIX + "/<serviceId>/", methods=["PATCH"])
def patchService(serviceId):
    retResp = {"success": False, "message": ""}
    validKeys = [
            "description", "basePath", "path",
            "icon", "example", "appLink",
            "videoLink", "swagger",
            ##################################
            "code", "kind", "method",
            ]

    if not request.is_json:
        retResp["message"] = "Invalid request body type, expected JSON"
        return jsonify(retResp), 400

    incomData = request.get_json()
    validateParams(incomData, validKeys)
    chcode, chpath = validateCodeAndPath(incomData)

    if len(incomData) == 0:
        retResp["message"] = "No required fields found"
        return jsonify(retResp), 400

    service, code, kind, method = updateService(serviceId, incomData)

    if service is None:
        retResp["message"] = "Couldn't find serviceId " + serviceId
        return jsonify(retResp), 404

    if chcode or chpath:
        auth = mongo.db.namespace.find_one(
                {"authUser": service.get("namespace")},
                {"_id": False})
        authUser = auth.get("authUser", "")
        authPass = auth.get("authPass", "")
        serviceName = service.get("serviceName")

    ***REMOVED***
            if chcode:
                code = base64.b64decode(code).decode()
                wskutil.updateAction(
                        authUser, authPass, serviceName, kind, code, True)
            if chpath:
                wskutil.deleteApi(authUser, authPass, service.get("basePath"))
                wskutil.createApi(
                        authUser,
                        authPass,
                        serviceName,
                        incomData.get("basePath"),
                        incomData.get("path"),
                        method)
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
    retResp["message"] = "serviceId " + serviceId + " is successfully updated"

    return jsonify(retResp), 200


def updateService(serviceId, data):
    code = data.pop("code", None)
    kind = data.pop("kind", None)
    meth = data.pop("method", None)

    service = mongo.db.service.find_one_and_update(
            {"serviceId": serviceId},
            {"$set": data},
            projection={"_id": False})

    return service, code, kind, meth


# If you want to create a namespace, strictly use "name" as the key.
# In case you want to minus the serviceCount, use either "name" or "authUser."
# Besides the above constraints, do not use any other keys.
def updateNamespace(key, val, num):
    success = False
    authUser = None
    authPass = None

    namespace = mongo.db.namespace.find_one_and_update(
        {key: val},
        {"$inc": {"serviceCount": num}},
        projection={"_id": False},
        upsert=True)

    if namespace is None:
        isCreated, authUser, authPass = wskutil.createUser(val)

        if isCreated:
            mongo.db.namespace.update_one(
                    {key: val},
                    {"$set": {"authUser": authUser, "authPass": authPass}})
            success = True
***REMOVED***
        authUser = namespace.get("authUser", "")
        authPass = namespace.get("authPass", "")
        serviceCount = namespace.get("serviceCount", 1)

        if serviceCount == -num:
            mongo.db.namespace.delete_one({key: val})
            isDeleted, result = wskutil.deleteUser(namespace.get("name"))

            if isDeleted:
                success = True
    ***REMOVED***
            success = True

    return success, authUser, authPass


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
                    "userId": data.get("userId", "")
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


def validateCodeAndPath(d):
    chcode = False
    chpath = False

    if not ("code" in d and "kind" in d):
        d.pop("code", None)
        d.pop("kind", None)
***REMOVED***
        chcode = True

    if not ("path" in d and "method" in d):
        d.pop("basePath", None)
        d.pop("path", None)
        d.pop("method", None)
***REMOVED***
        d["basePath"] = d.get("basePath", "/")
        chpath = True

    return chcode, chpath
