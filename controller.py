from flask import request, jsonify, make_response
from flask_pymongo import PyMongo
import requests
import base64
import binascii
import time

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
    f.register_error_handler(requests.ReadTimeout, direct_err)
    f.register_error_handler(ServiceException, custom_err_handler)
    f.register_error_handler(binascii.Error, base64_err_handler)
    f.register_error_handler(UnicodeDecodeError, base64_err_handler)
    f.register_error_handler(AssertionError, assert_err_handler)


def get_services():
    services = None
    token = request.headers.get(AUTH_HEAD, None)
    user = helper.get_user_by_token(token)
    args = request.args
    size = args.get("size", 20, int)
    offset = args.get("page", 0, int)
    owner = Service.Field.owner
    keyword = Service.Field.keyword
    query = {}
    projection = {Service.Field.id: False}

    if owner in args:
        query[owner] = args[owner]

    if keyword in args:
        query["$text"] = {"$search": "\"{}\"".format(args[keyword])}

    if user is None:
        projection[Service.Field.endpoint] = False
    else:
        query[owner] = user.get(User.Field.username, "")

    if offset < 0:
        offset = 0

    if size <= 0:
        size = 20

    page = helper.get_page(query, projection, offset, size)

    return jsonify(page), 200


def create_service():
    ret_resp = {SUCCESS: False, MESSAGE: ""}
    field_owner = Service.Field.owner
    field_service_name = Service.Field.service_name
    valid_keys = [
        field_service_name,
        field_owner,
        Service.Field.description,
    ]
    required_keys = valid_keys[:-1]
    token = request.headers.get(AUTH_HEAD, None)
    user = helper.get_user_by_token(token)

    helper.assert_user(user)

    din = helper.get_json_body(request)
    username = user.get(User.Field.username, "")
    din[field_owner] = username

    helper.assert_input(din, required_keys, valid_keys)

    action = helper.get_action(
        din.get(field_owner, ""),
        din.get(field_service_name, ""))
    service = helper.insert_service(din)

    assert service is not None, \
        (409, "Service {} already exists".format(action))

    helper.init_action(action)
    field_service_id = Service.Field.service_id
    service_id = service.get(field_service_id, "")
    helper.create_ac_node(service_id, username, True)

    ret_resp[SUCCESS] = True
    ret_resp[MESSAGE] = "Service {} is successfully created.".format(action)
    ret_resp[field_service_id] = service_id

    return jsonify(ret_resp), 201


def get_service(service_id):
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
        #  wskutil.delete_package(username)
    except ServiceException as e:
        if e.http_code != 409:
            raise

    helper.delete_ac_node(service_id)

    ret_resp[SUCCESS] = True
    ret_resp[MESSAGE] = "Service {} is successfully deleted".format(service_id)

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
    ret_resp[MESSAGE] = "Service {} is successfully updated".format(service_id)

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
    ticket = request.headers.get(AUTH_HEAD, None)

    assert helper.verify_ticket(ticket, service_id) is True, \
        (401, "Unauthorized ticket")

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


def test_empty():
    return "", 200


def test_multiple_records(num=1):
    services = mongo.db.service.find(
        {},
        {
            Service.Field.id: False,
            Service.Field.thumbnail: False,
            Service.Field.swagger: False
        }).limit(num)
    return jsonify(list(services)), 200


def test_single_record(service_id):
    service = helper.find_service(service_id, {Service.Field.id: False})
    return jsonify(service), 200


def test_create():
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
    din[Service.Field.service_name] = str(time.time())

    helper.assert_input(din, required_keys, valid_keys)

    action = helper.get_action(
        din.get(Service.Field.owner, ""),
        din.get(Service.Field.service_name, ""))
    service = helper.insert_service(din)

    assert service is not None, \
        (409, "Service {} already exists".format(action))

    helper.init_action(action)

    ret_resp[SUCCESS] = True
    ret_resp[MESSAGE] = "Service {} is successfully created.".format(action)
    ret_resp[Service.Field.service_id] = \
        service.get(Service.Field.service_id, "")

    return jsonify(ret_resp), 201


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
