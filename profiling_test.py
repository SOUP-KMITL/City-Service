from werkzeug.contrib.profiler import ProfilerMiddleware
import route

route.app.config["PROFILE"] = True
route.app.wsgi_app = ProfilerMiddleware(
    route.app.wsgi_app,
    #  restrictions=["^(?!(\{|/usr))"]
    #  restrictions=["CityService/"]
    restrictions=["count|ceil|skip|limit|sort|CityService/"]
)
route.app.run(host="0.0.0.0", port=5000, debug=True)
