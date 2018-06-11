import os

env    = os.environ.get("FLASK_ENV", "DEV")
dbhost = os.environ.get("DB_HOST", "mongodb")


# Example configuration
class DefaultConfig(object):
    MONGO_DBNAME = "data_market"
    MONGO_HOST   = dbhost
    MONGO_PORT   = 27017
    DEBUG        = False if env == "PROD" else True


API_VER = 1
EXT_API_PORT = 443
INT_API_PORT = 80

TEMPLATE = "./template.js"

EXT_API_GATEWAY = "https://api.smartcity.kmitl.io:" + \
    str(EXT_API_PORT) + "/api/v1"
#  EXT_API_GATEWAY = "https://203.154.59.55:" + str(EXT_API_PORT) + "/api/v1"
#  EXT_API_GATEWAY = "https://kohpai.com:" + str(EXT_API_PORT) + "/api/v1"

if env == "PROD":
    #  Production (public server) configuration
    API_PREFIX     = "/services"
    COLLECTION_API = "http://collection-service:{}".format(str(INT_API_PORT))
    USER_API       = "http://user-service:{}".format(str(INT_API_PORT))
    LOGIN_API      = "{}/login".format(USER_API)
    METER_API      = "http://meter-service:{}".format(str(INT_API_PORT))
    AC_API         = "http://access-control-service:{}" \
        .format(str(INT_API_PORT))
else:
    #  Development (local) configuration
    API_PREFIX     = "/api/v" + str(API_VER) + "/services"
    COLLECTION_API = EXT_API_GATEWAY + "/collections"
    USER_API       = EXT_API_GATEWAY + "/users"
    LOGIN_API      = USER_API + "/login"
    METER_API      = EXT_API_GATEWAY + "/meters"
    AC_API         = EXT_API_GATEWAY + "/accesscontrol"
