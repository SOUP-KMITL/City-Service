from werkzeug.utils import secure_filename
import pymongo
***REMOVED***
import uuid
import time
import math

# Custom modules and packages
from utils.template import Service
from utils.template import User
from utils.template import Page
from utils.error import ServiceException
from utils import wskutil
import appconfig

mongo = None


def set_mongo_instance(m):
    global mongo
    mongo = m


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
    ***REMOVED*** ServiceException(http_code, error)

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
                wskutil.create_package(username)
            wskutil.update_action(action, "nodejs:6", code, False)
            break
        except ServiceException as e:
            if i == 1 or e.http_code != 404:
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


def bin_to_url(cursor):
    service_id = cursor.get(Service.Field.service_id, "")
    thumbnail = cursor.get(Service.Field.thumbnail, None)
    swagger = cursor.get(Service.Field.swagger, None)

    if thumbnail is not None:
        cursor[Service.Field.thumbnail] = appconfig.EXT_API_GATEWAY + \
            "/services/" + service_id + "/thumbnail"

    if swagger is not None:
        cursor[Service.Field.swagger] = appconfig.EXT_API_GATEWAY + \
            "/services/" + service_id + "/swagger"

    return cursor


def get_page(services, page=0, size=20, user=None):
    results = list()
    total_elems = services.count()
    total_pages = math.ceil(total_elems / size)

    services = services.skip(page * size) \
        .limit(size) \
        .sort(Service.Field.created_at, pymongo.DESCENDING)

    num_elems = services.count(with_limit_and_skip=True)

    for service in services:
        if user is None or (user.get(User.Field.username, "") !=
                            service.get(Service.Field.owner, "")):
            service.pop(Service.Field.endpoint, None)
        results.append(bin_to_url(service))

    page = {
        Page.Field.content: results,
        Page.Field.first: True if page == 0 else False,
        Page.Field.last: True if page >= total_pages - 1 else False,
        Page.Field.sort: None,
        Page.Field.size: size,
        Page.Field.total_pages: total_pages,
        Page.Field.total_elems: total_elems,
        Page.Field.num_elems: num_elems,
        Page.Field.curr_page: page,
    }

    return page


def redirect_request(req, ep, path=""):
    url = ep + "/" + path
    method = req.method
    result = None

***REMOVED***
        if method == "GET":
            resp = requests.get(url, params=req.args)
        elif method == "POST" or method == "POST" or method == "PATCH":
    ***REMOVED***
                url,
                data=req.data,
                params=req.args,
                headers=req.headers)
        elif method == "DELETE":
    ***REMOVED***url, params=req.args, headers=req.headers)
    ***REMOVED***
            print("redirect_request: Unsupported HTTP method")
    ***REMOVED*** ServiceException(400, "Unsupported HTTP method")

***REMOVED***
        print("redirect_request: couldn't connect to external service")
***REMOVED***
***REMOVED***
        print("redirect_request: connection to external service timeout")
***REMOVED***
***REMOVED***
    ***REMOVED***
    ***REMOVED***
        except ValueError:
    ***REMOVED*** ServiceException(
                500,
                ("The remote endpoint of this service "
                 "didn't return a valid JSON packet."))

        return resp.status_code, result


def find_service(service_id, projection):
    service = mongo.db.service.find_one(
        {Service.Field.service_id: service_id},
        projection=projection)

    assert service is not None, (404, "Couldn't find service " + service_id)

    return service
