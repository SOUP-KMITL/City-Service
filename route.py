from flask import Flask

# Custom modules and packages
import appconfig
import controller

app = Flask(__name__)
app.config.from_object("appconfig.DefaultConfig")
controller.set_flask_instance(app)

app.add_url_rule(
    appconfig.API_PREFIX,
    view_func=controller.get_services,
    strict_slashes=False)

app.add_url_rule(
    appconfig.API_PREFIX,
    view_func=controller.create_service,
    strict_slashes=False, methods=["POST"])

app.add_url_rule(
    "{}/<service_id>".format(appconfig.API_PREFIX),
    view_func=controller.get_service,
    strict_slashes=False)

app.add_url_rule(
    "{}/<service_id>".format(appconfig.API_PREFIX),
    view_func=controller.patch_service,
    strict_slashes=False,
    methods=["PATCH"])

app.add_url_rule(
    "{}/<service_id>/thumbnail".format(appconfig.API_PREFIX),
    view_func=controller.upload_thumbnail,
    strict_slashes=False,
    methods=["PUT"])

app.add_url_rule(
    "{}/<service_id>".format(appconfig.API_PREFIX),
    view_func=controller.delete_service,
    strict_slashes=False,
    methods=["DELETE"])

app.add_url_rule(
    "{}/<service_id>/thumbnail".format(appconfig.API_PREFIX),
    view_func=controller.download_thumbnail,
    strict_slashes=False)

app.add_url_rule(
    "{}/<service_id>/swagger".format(appconfig.API_PREFIX),
    view_func=controller.upload_swagger,
    strict_slashes=False,
    methods=["PUT"])

app.add_url_rule(
    "{}/<service_id>/swagger".format(appconfig.API_PREFIX),
    view_func=controller.download_swagger,
    strict_slashes=False)

app.add_url_rule(
    "{}/<service_id>/activations".format(appconfig.API_PREFIX),
    view_func=controller.invoke_service,
    strict_slashes=False,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"])

app.add_url_rule(
    "{}/<service_id>/activations/<path:custom_path>"
    .format(appconfig.API_PREFIX),
    view_func=controller.invoke_service,
    strict_slashes=False,
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"])

app.add_url_rule(
    "{}/test".format(appconfig.API_PREFIX),
    view_func=controller.test_empty,
    strict_slashes=False)

app.add_url_rule(
    "{}/test/indy/<service_id>".format(appconfig.API_PREFIX),
    view_func=controller.test_single_record,
    strict_slashes=False)

app.add_url_rule(
    "{}/test/mult/<int:num>".format(appconfig.API_PREFIX),
    view_func=controller.test_multiple_records,
    strict_slashes=False)
