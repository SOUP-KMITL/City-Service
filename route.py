from flask import Flask

# Custom modules and packages
import appconfig
import controller

app = Flask(__name__)
app.config.from_object("appconfig.DefaultConfig")
controller.set_flask_instance(app)

app.add_url_rule(
    appconfig.API_PREFIX + "/<service_id>",
    view_func=controller.delete_service,
    strict_slashes=False,
    methods=["DELETE"])

app.add_url_rule(
    appconfig.API_PREFIX,
    view_func=controller.get_services,
    strict_slashes=False)

app.add_url_rule(
    appconfig.API_PREFIX,
    view_func=controller.create_service,
    strict_slashes=False, methods=["POST"])

app.add_url_rule(
    appconfig.API_PREFIX + "/<service_id>",
    view_func=controller.get_service,
    strict_slashes=False)

app.add_url_rule(
    appconfig.API_PREFIX + "/<service_id>",
    view_func=controller.patch_service,
    strict_slashes=False,
    methods=["PATCH"])

app.add_url_rule(
    appconfig.API_PREFIX + "/<service_id>/thumbnail",
    view_func=controller.upload_thumbnail,
    strict_slashes=False,
    methods=["PUT"])

app.add_url_rule(
    appconfig.API_PREFIX + "/<service_id>/thumbnail",
    view_func=controller.download_thumbnail,
    strict_slashes=False)

app.add_url_rule(
    appconfig.API_PREFIX + "/<service_id>/swagger",
    view_func=controller.upload_swagger,
    strict_slashes=False,
    methods=["PUT"])

app.add_url_rule(
    appconfig.API_PREFIX + "/<service_id>/swagger",
    view_func=controller.download_swagger,
    strict_slashes=False)
