from flask import Flask, request, jsonify, make_response
from flask_pymongo import PyMongo
import pymongo
import requests
import base64
import binascii

# Custom modules and packages
from utils import wskutil
from utils.template.service import Service
from utils.template.user import User
from utils.error import ServiceException
import helper
import appconfig

app = Flask(__name__)
app.config.from_object("appconfig.DefaultConfig")
mongo = PyMongo(app)
helper.set_mongo_instance(mongo)


@app.route(appconfig.API_PREFIX, strict_slashes=False)
def get_services():
    services = None
    args = request.args
    size = args.get("size", 20, int)
    page = args.get("page", 0, int)
    key = Service.Field.owner
    query = {}

    if key in args:
        query[key] = args.get(key)

    services = mongo.db.service.find(query, {Service.Field.id: False})

    if page < 0:
        page = 0

    if size < 0:
        size = 20

    page = helper.get_page(services, page, size)

    return jsonify(page), 200


@app.route(appconfig.API_PREFIX, strict_slashes=False, methods=["POST"])
def create_service():
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    valid_keys = [
        Service.Field.service_name,
        Service.Field.owner,
        Service.Field.description,
    ]
    required_keys = valid_keys[:-1]
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = helper.get_user_by_token(token)

    helper.assert_user(user)

    din = helper.get_json_body(request)
    din[Service.Field.owner] = user.get(User.Field.username, "")

    helper.assert_input(din, required_keys, valid_keys)

    action = helper.get_action(
        din.get(Service.Field.owner, ""),
        din.get(Service.Field.service_name, ""))
    service = helper.insert_service(din)

    assert service is not None, (409, "Service " + action + " already exists")

    helper.init_action(action)

    ret_resp[appconfig.SUCCESS] = True
    ret_resp[appconfig.MESSAGE] = "Service " + action + \
        " is successfully created."
    ret_resp[Service.Field.service_id] = \
        service.get(Service.Field.service_id, "")

    return jsonify(ret_resp), 201


@app.route(appconfig.API_PREFIX + "/<service_id>", strict_slashes=False)
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


@app.route(
    appconfig.API_PREFIX + "/<service_id>",
    strict_slashes=False,
    methods=["DELETE"])
def delete_service(service_id):
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = helper.get_user_by_token(token)

    helper.assert_user(user)

    username = user.get(User.Field.username, "")
    service = mongo.db.service.find_one_and_delete(
        {
            Service.Field.service_id: service_id,
            Service.Field.owner: username
        })

    helper.assert_service_and_owner(service)

    action = helper.get_action(
        username,
        service.get(Service.Field.service_name, ""))

    try:
        wskutil.deleteAction(action)
        wskutil.deletePackage(username)
    except ServiceException as e:
        if e.http_code != 409:
            raise

    ret_resp[appconfig.SUCCESS] = True
    ret_resp[appconfig.MESSAGE] = "Service " + service_id + \
        " is successfully deleted"

    return jsonify(ret_resp), 200


@app.route(
    appconfig.API_PREFIX + "/<service_id>",
    strict_slashes=False,
    methods=["PATCH"])
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
    user = helper.get_user_by_token(token)

    helper.assert_user(user)

    din = helper.get_json_body(request)

    # filtering
    helper.filter_params(din, validKeys)

    assert len(din) > 0, (400, "No required fields found")

    chcode, code, kind = helper.extract_code(din)
    username = user.get(User.Field.username, "")
    service = helper.update_service(service_id, username, din)

    helper.assert_service_and_owner(service)

    action = helper.get_action(
        username,
        service.get(Service.Field.service_name, ""))

    if chcode:
        code = base64.b64decode(code).decode()
        wskutil.updateAction(action, kind, code, True)

    ret_resp[appconfig.SUCCESS] = True
    ret_resp[appconfig.MESSAGE] = "Service " + service_id + \
        " is successfully updated"

    return jsonify(ret_resp), 200


@app.route(
    appconfig.API_PREFIX + "/<service_id>/thumbnail",
    strict_slashes=False,
    methods=["PUT"])
def upload_thumbnail(service_id):
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = helper.get_user_by_token(token)

    helper.assert_user(user)

    f = request.files.get(appconfig.FILE, None)

    helper.assert_file(f)

    buf = f.read()

    helper.assert_valid_file(f, buf, helper.allowed_image)

    service = helper.update_service(
        service_id,
        user.get(User.Field.username, ""),
        {Service.Field.thumbnail: buf})

    helper.assert_service_and_owner(service)

    ret_resp[appconfig.SUCCESS] = "Thumbnail is uploaded successful"
    ret_resp[appconfig.MESSAGE] = True

    return jsonify(ret_resp), 200


@app.route(
    appconfig.API_PREFIX + "/<service_id>/thumbnail",
    strict_slashes=False)
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


@app.route(
    appconfig.API_PREFIX + "/<service_id>/swagger",
    strict_slashes=False,
    methods=["PUT"])
def upload_swagger(service_id):
    ret_resp = {appconfig.SUCCESS: False, appconfig.MESSAGE: ""}
    token = request.headers.get(appconfig.AUTH_HEAD, None)
    user = helper.get_user_by_token(token)

    helper.assert_user(user)

    f = request.files.get(appconfig.FILE, None)

    helper.assert_file(f)

    buf = f.read()

    helper.assert_valid_file(f, buf, helper.allowed_YAML)

    service = helper.update_service(
        service_id,
        user.get(User.Field.username, ""),
        {Service.Field.swagger: buf})

    helper.assert_service_and_owner(service)

    ret_resp[appconfig.SUCCESS] = True
    ret_resp[appconfig.MESSAGE] = "File is uploaded successful"

    return jsonify(ret_resp), 200


@app.route(
    appconfig.API_PREFIX + "/<service_id>/swagger",
    strict_slashes=False)
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
    return jsonify(helper.direct_err(e)), 500


@app.errorhandler(requests.ConnectTimeout)
def timeout_err_handler(e):
    return jsonify(helper.direct_err(e)), 500


@app.errorhandler(ServiceException)
def custom_err_handler(e):
    ret_resp = {"success": False, "message": e.message}
    return jsonify(ret_resp), e.http_code


@app.errorhandler(binascii.Error)
def base64_err_handler(e):
    ret_resp = {"success": False, "message": "Invalid base64 encoded message"}
    return jsonify(ret_resp), 400


@app.errorhandler(AssertionError)
def assert_err_handler(e):
    ret_resp = {"success": False, "message": e.args[0][1]}
    return jsonify(ret_resp), e.args[0][0]
