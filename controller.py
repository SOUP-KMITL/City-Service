from flask import request, jsonify, make_response
from flask_pymongo import PyMongo
import requests
import base64
import binascii

# Custom modules and packages
from utils import wskutil
from utils.error import ServiceException
from utils.template import Service
from utils.template import User
import helper

# Constant variables
AUTH_HEAD = "Authorization"
TYPE_HEAD = "Content-Type"
SUCCESS = "success"
MESSAGE = "message"
FILE = "file"

mongo = None


def set_flask_instance(f):
    global mongo

    mongo = PyMongo(f)
    helper.set_mongo_instance(mongo)
    f.register_error_handler(requests.ConnectionError, direct_err)
    f.register_error_handler(requests.ConnectTimeout, direct_err)
    f.register_error_handler(ServiceException, custom_err_handler)
    f.register_error_handler(binascii.Error, base64_err_handler)
    f.register_error_handler(AssertionError, assert_err_handler)


def get_services():
    services = None
    token = request.headers.get(AUTH_HEAD, None)
    user = helper.get_user_by_token(token)
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

    page = helper.get_page(services, page, size, user)

    return jsonify(page), 200


def create_service():
    ret_resp = {SUCCESS: False, MESSAGE: ""}
    valid_keys = [
        Service.Field.service_name,
        Service.Field.owner,
        Service.Field.description,
    ]
    required_keys = valid_keys[:-1]
    token = request.headers.get(AUTH_HEAD, None)
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

    ret_resp[SUCCESS] = True
    ret_resp[MESSAGE] = "Service " + action + \
        " is successfully created."
    ret_resp[Service.Field.service_id] = \
        service.get(Service.Field.service_id, "")

    return jsonify(ret_resp), 201


def get_service(service_id):
    ret_resp = {SUCCESS: False, MESSAGE: ""}
    token = request.headers.get(AUTH_HEAD, None)
    user = helper.get_user_by_token(token)

    service = helper.find_service(service_id, {Service.Field.id: False})

    if user is None or (user.get(User.Field.username, "") !=
                        service.get(Service.Field.owner, "")):
        service.pop(Service.Field.endpoint, None)


    helper.bin_to_url(service)

    return jsonify(service), 200


def delete_service(service_id):
    ret_resp = {SUCCESS: False, MESSAGE: ""}
    token = request.headers.get(AUTH_HEAD, None)
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
        wskutil.delete_action(action)
        wskutil.delete_package(username)
    except ServiceException as e:
        if e.http_code != 409:
            raise

    ret_resp[SUCCESS] = True
    ret_resp[MESSAGE] = "Service " + service_id + \
        " is successfully deleted"

    return jsonify(ret_resp), 200


def patch_service(service_id):
    ret_resp = {SUCCESS: False, MESSAGE: ""}
    validKeys = [
        Service.Field.description, Service.Field.endpoint,
        Service.Field.sameple_data, Service.Field.app_link,
        Service.Field.video_link,
        ##################################
        Service.Field.code, Service.Field.kind,
    ]
    token = request.headers.get(AUTH_HEAD, None)
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
        wskutil.update_action(action, kind, code, True)

    ret_resp[SUCCESS] = True
    ret_resp[MESSAGE] = "Service " + service_id + \
        " is successfully updated"

    return jsonify(ret_resp), 200


def upload_thumbnail(service_id):
    ret_resp = {SUCCESS: False, MESSAGE: ""}
    token = request.headers.get(AUTH_HEAD, None)
    user = helper.get_user_by_token(token)

    helper.assert_user(user)

    f = request.files.get(FILE, None)

    helper.assert_file(f)

    buf = f.read()

    helper.assert_valid_file(f, buf, helper.allowed_image)

    service = helper.update_service(
        service_id,
        user.get(User.Field.username, ""),
        {Service.Field.thumbnail: buf})

    helper.assert_service_and_owner(service)

    ret_resp[SUCCESS] = "Thumbnail is uploaded successful"
    ret_resp[MESSAGE] = True

    return jsonify(ret_resp), 200


def download_thumbnail(service_id):
    service = helper.find_service(
        service_id,
        {Service.Field.id: False, Service.Field.thumbnail: True})
    thumbnail = service.get(Service.Field.thumbnail, None)

    assert thumbnail is not None, (404, "No thumbnail file found")

    resp = make_response(thumbnail)
    resp.headers[TYPE_HEAD] = "image/png"
    resp.status_code = 200

    return resp


def upload_swagger(service_id):
    ret_resp = {SUCCESS: False, MESSAGE: ""}
    token = request.headers.get(AUTH_HEAD, None)
    user = helper.get_user_by_token(token)

    helper.assert_user(user)

    f = request.files.get(FILE, None)

    helper.assert_file(f)

    buf = f.read()

    helper.assert_valid_file(f, buf, helper.allowed_YAML)

    service = helper.update_service(
        service_id,
        user.get(User.Field.username, ""),
        {Service.Field.swagger: buf})

    helper.assert_service_and_owner(service)

    ret_resp[SUCCESS] = True
    ret_resp[MESSAGE] = "File is uploaded successful"

    return jsonify(ret_resp), 200


def download_swagger(service_id):
    service = helper.find_service(
        service_id,
        {Service.Field.id: False, Service.Field.swagger: True})
    swagger = service.get(Service.Field.swagger, None)

    assert swagger is not None, (404, "No swagger file found")

    resp = make_response(swagger)
    resp.headers[TYPE_HEAD] = "text/plain"
    resp.status_code = 200

    return resp


def invoke_service(service_id, custom_path=""):
    service = helper.find_service(service_id, {Service.Field.id: False})
    endpoint = service.get(Service.Field.endpoint, "")

    if endpoint:
        http_code, result = helper.redirect_request(
            request,
            endpoint,
            custom_path)
        return make_response((jsonify(result), http_code))

    params = None

    if request.is_json:
        params = request.get_json()

    action = helper.get_action(
        service.get(Service.Field.owner, ""),
        service.get(Service.Field.service_name, ""))
    http_code, result = wskutil.invoke_action(action, params)

    return make_response((jsonify(result), http_code))


def direct_err(e):
    ret_resp = {"success": False, "message": e.__str__()}
    return jsonify(ret_resp), 500


def custom_err_handler(e):
    ret_resp = {"success": False, "message": e.message}
    return jsonify(ret_resp), e.http_code


def base64_err_handler(e):
    ret_resp = {"success": False, "message": "Invalid base64 encoded message"}
    return jsonify(ret_resp), 400


def assert_err_handler(e):
    ret_resp = {"success": False, "message": e.args[0][1]}
    return jsonify(ret_resp), e.args[0][0]
