from flask import Flask, request, jsonify, make_response
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import pymongo
***REMOVED***
import uuid
import base64
import binascii
import time

# Custom modules and packages
from utils import wskutil
from utils.template.service import Service
from utils.template.user import User
import appconfig

app = Flask(__name__)
app.config.from_object("appconfig.DefaultConfig")
mongo = PyMongo(app)


@app.route(appconfig.API_PREFIX)
def get_services():
    services = None
    args = request.args
    size = args.get("size", 20, int)
    page = args.get("page", 0, int)
    key = Service.Field.owner
    query = {}

    if key in args:
        query[key] = args.get(key)

    services = mongo.db.service.find(
        query,
        {
            Service.Field.id: False,
            Service.Field.thumbnail: False,
            Service.Field.swagger: False
        }) \
        .skip(page * size) \
        .limit(size) \
        .sort(Service.Field.created_at, pymongo.DESCENDING)

    return jsonify(list(services)), 200


@app.route(appconfig.API_PREFIX, methods=["POST"])
def create_service():
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    valid_keys = [
        Service.Field.service_name,
        Service.Field.owner,
        Service.Field.description,
    ]
    required_keys = valid_keys[:-1]
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = get_user_by_token(token)

    assert_user(user)

    din = get_json_body(request)
    din[Service.Field.owner] = user.get(User.Field.username, "")

    assert_input(din, required_keys, valid_keys)

    action = get_action(
        din.get(Service.Field.owner, ""),
        din.get(Service.Field.service_name, ""))
    service = insert_service(din)

    assert service is not None, (409, "Service " + action + " already exists")

    init_action(action)

    ret_resp[appconfig.SUCCESS] = True
    ret_resp[appconfig.MESSAGE] = "Service " + action + \
        " is successfully created."
    ret_resp[Service.Field.service_id] = \
        service.get(Service.Field.service_id, "")

    return jsonify(ret_resp), 201


@app.route(appconfig.API_PREFIX + "/<service_id>")
def get_service(service_id):
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}

    service = mongo.db.service.find_one(
        {Service.Field.service_id: service_id},
        {
            Service.Field.id: False,
            Service.Field.thumbnail: False,
            Service.Field.swagger: False
        })

    if service is None:
        ret_resp[appconfig.MESSAGE] = "Couldn't find service " + service_id
        return jsonify(ret_resp), 404

    return jsonify(service), 200


@app.route(appconfig.API_PREFIX + "/<service_id>", methods=["DELETE"])
def delete_service(service_id):
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = get_user_by_token(token)

    assert_user(user)

    username = user.get(User.Field.username, "")
    service = mongo.db.service.find_one_and_delete(
        {
            Service.Field.service_id: service_id,
            Service.Field.owner: username
        })

    assert_service_and_owner(service)

    action = get_action(username, service.get(Service.Field.service_name, ""))

***REMOVED***
        wskutil.deleteAction(action)
        wskutil.deletePackage(username)
    except Exception as e:
        http_code = e.args[0]
        if http_code != 409:
    ***REMOVED***

    ret_resp[appconfig.SUCCESS] = True
    ret_resp[appconfig.MESSAGE] = "Service " + service_id + \
        " is successfully deleted"

    return jsonify(ret_resp), 200


@app.route(appconfig.API_PREFIX + "/<service_id>", methods=["PATCH"])
def patch_service(service_id):
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    validKeys = [
        Service.Field.description, Service.Field.endpoint,
        Service.Field.sameple_data, Service.Field.app_link,
        Service.Field.video_link,
        ##################################
        Service.Field.code, Service.Field.kind,
    ]
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = get_user_by_token(token)

    assert_user(user)

    din = get_json_body(request)

    # filtering
    filter_params(din, validKeys)

    assert len(din) > 0, (400, "No required fields found")

    chcode, code, kind = extract_code(din)
    username = user.get(User.Field.username, "")
    service = update_service(service_id, username, din)

    assert_service_and_owner(service)

    action = get_action(username, service.get(Service.Field.service_name, ""))

    if chcode:
        code = base64.b64decode(code).decode()
        wskutil.updateAction(action, kind, code, True)

    ret_resp[appconfig.SUCCESS] = True
    ret_resp[appconfig.MESSAGE] = "Service " + service_id + \
        " is successfully updated"

    return jsonify(ret_resp), 200


@app.route(appconfig.API_PREFIX + "/<service_id>/thumbnail", methods=["PUT"])
def upload_thumbnail(service_id):
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = get_user_by_token(token)

    assert_user(user)

    f = request.files.get(appconfig.FILE, None)

    assert_file(f)

    buf = f.read()

    assert_valid_file(f, buf, allowed_image)

    service = update_service(
        service_id,
        user.get(User.Field.username, ""),
        {Service.Field.thumbnail: buf})

    assert_service_and_owner(service)

    ret_resp[appconfig.SUCCESS] = "Thumbnail is uploaded successful"
    ret_resp[appconfig.MESSAGE] = True

    return jsonify(ret_resp), 200


@app.route(appconfig.API_PREFIX + "/<service_id>/thumbnail")
def download_thumbnail(service_id):
    thumbnail = mongo.db.service.find_one(
        {Service.Field.service_id: service_id},
        {Service.Field.id: False, Service.Field.thumbnail: True}) \
        .get(Service.Field.thumbnail, None)

    assert thumbnail is not None, (404, "No thumbnail file found")

    resp = make_response(thumbnail)
    resp.headers[appconfig.TYPE_HEAD] = "image/png"
    resp.status_code = 200

    return resp


@app.route(appconfig.API_PREFIX + "/<service_id>/swagger", methods=["PUT"])
def upload_swagger(service_id):
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = get_user_by_token(token)

    assert_user(user)

    f = request.files.get(appconfig.FILE, None)

    assert_file(f)

    buf = f.read()

    assert_valid_file(f, buf, allowed_YAML)

    service = update_service(
        service_id,
        user.get(User.Field.username, ""),
        {Service.Field.swagger: buf})

    assert_service_and_owner(service)

    ret_resp[appconfig.SUCCESS] = True
    ret_resp[appconfig.MESSAGE] = "File is uploaded successful"

    return jsonify(ret_resp), 200


@app.route(appconfig.API_PREFIX + "/<service_id>/swagger")
def download_swagger(service_id):
    swagger = mongo.db.service.find_one(
        {Service.Field.service_id: service_id},
        {
            Service.Field.id: False,
            Service.Field.swagger: True
        }).get(Service.Field.swagger, None)

    assert swagger is not None, (404, "No swagger file found")

    resp = make_response(swagger)
    resp.headers[appconfig.TYPE_HEAD] = "text/plain"
    resp.status_code = 200

    return resp


#  @app.route(appconfig.API_PREFIX + "/<serviceId>/activations",
#  methods=["POST"])
#  def invokeService(serviceId):
#      ret_resp = {"success": False, "message": ""}
#      params = None

#      if request.is_json:
#          params = request.get_json()

#      service = mongo.db.service.find_one(
#          {"serviceId": serviceId},
#          {"_id": False})

#      if service is None:
#          ret_resp["message"] = "Couldn't find serviceId " + serviceId
#          return jsonify(ret_resp), 404

#      username, serviceName, action = getAction(service)

#      http_code, data = wskutil.invokeAction(action, params)
#      ret_resp = data

#      return jsonify(ret_resp), 200


#  @app.route(appconfig.API_PREFIX + "/<serviceId>/data")
#  def getDataService(serviceId):
#      ret_resp = {"success": False, "message": ""}
#      service = mongo.db.service.find_one(
#          {"serviceId": serviceId},
#          {"_id": False})

#      if service is None:
#          ret_resp["message"] = "Couldn't find serviceId " + serviceId
#          return jsonify(ret_resp), 404

#      username, serviceName, action = getAction(service)

#      http_code, data = wskutil.invokeAction(action, None)
#      ret_resp = data

#      return jsonify(ret_resp), 200


@app.errorhandler(requests.ConnectionError)
def conn_err_handler(e):
    return jsonify(direct_err(e)), 500


@app.errorhandler(requests.ConnectTimeout)
def timeout_err_handler(e):
    return jsonify(direct_err(e)), 500


@app.errorhandler(Exception)
def custom_err_handler(e):
    ret_resp = {"success": False, "message": e.args[1]}
    return jsonify(ret_resp), e.args[0]


@app.errorhandler(binascii.Error)
def base64_err_handler(e):
    ret_resp = {"success": False, "message": "Invalid base64 encoded message"}
    return jsonify(ret_resp), 400


@app.errorhandler(AssertionError)
def assert_err_handler(e):
    ret_resp = {"success": False, "message": e.args[0][1]}
    return jsonify(ret_resp), e.args[0][0]


def direct_err(e):
    ret_resp = {"success": False, "message": e.__str__()}
    return ret_resp


def update_service(service_id, u, d):
    service = None

    if d:
        d[Service.Field.updated_at] = int(time.time())
        service = mongo.db.service.find_one_and_update(
            {Service.Field.service_id: service_id, Service.Field.owner: u},
            {"$set": d},
            projection={Service.Field.id: False})
***REMOVED***
        service = mongo.db.service.find_one(
            {Service.Field.service_id: service_id, Service.Field.owner: u},
            {Service.Field.id: False})

    return service


def insert_service(data):
    currentTime = int(time.time())

    doc = {
        Service.Field.service_id: str(uuid.uuid1()),
        Service.Field.service_name: data.get(Service.Field.service_name, ""),
        Service.Field.description: data.get(Service.Field.description, ""),
        Service.Field.thumbnail: data.get(Service.Field.thumbnail, None),
        Service.Field.swagger: data.get(Service.Field.swagger, None),
        Service.Field.sameple_data: data.get(Service.Field.sameple_data, None),
        Service.Field.app_link: data.get(Service.Field.app_link, ""),
        Service.Field.video_link: data.get(Service.Field.video_link, ""),
        Service.Field.owner: data.get(Service.Field.owner, ""),
        Service.Field.endpoint: data.get(Service.Field.endpoint, ""),
        Service.Field.created_at: currentTime,
        Service.Field.updated_at: currentTime,
    }

***REMOVED***
        mongo.db.service.insert_one(doc)
    except pymongo.errors.DuplicateKeyError:
        return None

    return doc


def filter_params(d, vkeys):
    invalidKeys = []

    for key, value in d.items():
        if key not in vkeys or not value:
            invalidKeys.append(key)

    for key in invalidKeys:
        d.pop(key)


def get_action(owner, service_name):
    username = secure_filename(owner)
    serviceName = secure_filename(service_name)
    action = username + "/" + serviceName

    return action


def extract_code(d):
    code = d.pop("code", None)
    kind = d.pop("kind", None)
    ret = False

    if "code" in d and "kind" in d:
        ret = True

    return ret, code, kind


def get_user_by_token(t):
    if t is None:
        return None

    query = {"token": t}
    resp = None

***REMOVED***
        resp = requests.get(appconfig.USER_API, params=query)
***REMOVED***
        print("get_user_by_token: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("get_user_by_token: connection to external service timeout")
***REMOVED***
***REMOVED***
***REMOVED***
***REMOVED***
            error = "Unknown external service error"
            print("get_user_by_token: " + error)
    ***REMOVED*** Exception(http_code, error)

    result = resp.json()

    return result[0] if len(result) == 1 else None


def allowed_image(name, size):
    # 1MB maximum
    if size > 1 * 1024 * 1024:
        return False

    ext = name.split(".")[-1]

    if ext != "png" and ext != "jpg" and ext != "jpeg":
        return False

    return True


def allowed_YAML(name, size):
    # 1MB maximum
    if size > 1 * 1024 * 1024:
        return False

    ext = name.split(".")[-1]

    if ext != "yaml" and ext != "yml":
        return False

    return True


def init_action(action):
    f = open(appconfig.TEMPLATE, "r")
    code = f.read()
    username = action.split("/")[0]

    for i in range(2):
    ***REMOVED***
            if i == 1:
                wskutil.createPackage(username)
            wskutil.updateAction(action, "nodejs:6", code, False)
            break
        except Exception as e:
            http_code = e.args[0]
            if i == 1 or http_code != 404:
        ***REMOVED***


def assert_user(u):
    assert u is not None, (401, "Unauthorized access token")


def assert_input(din, rkeys, vkeys):
    filter_params(din, vkeys)
    res = all(key in din for key in rkeys)

    assert res, (400, "Required fileds are missing: " + ", ".join(rkeys))


def assert_service_and_owner(service):
    assert service is not None, \
        (404, "Couldn't find the service or unauthorized access token")


def assert_file(f):
    assert f is not None, (400, "Couldn't find the file being uploaded")


def assert_valid_file(f, buf, func):
    assert f.filename and func(f.filename, len(buf)), \
        (400, "File being uploaded is incorrect")


def get_json_body(req):
    assert req.is_json, (400, "Invalid request body type, expected JSON")
    return req.get_json()
