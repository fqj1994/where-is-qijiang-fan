#!/usr/bin/env python
# coding: utf-8
from flask import Flask, request, Response
from functools import wraps
import json
from gcm import GCM
from time import time
from redis import Redis
from config import GCM_API_KEY, MAPS_BROSWER_API_KEY, UPDATE_PASSWORD, WEB_TITLE, LOCATION_FLOAT_PASSWORD, ACCURATE_LOCATION_PASSWORD, FLASK_SECRET_KEY, ACCURATE_MODE, USER_IN_CHINA, CHINA_OFFSET_DATA_FILE
from math import sin, cos, pi, asin, log, exp, floor
import struct


kv = Redis()
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

def jsonify(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        return Response(json.dumps(f(*args, **kwargs)), mimetype="application/json")
    return wrapped


def find_china_offset(lat_check, lon_check):
    left, right = 0, 9813675;
    try:
        f = open(CHINA_OFFSET_DATA_FILE, 'rb')
    except:
        return 0, 0
    if not f:
        return 0, 0
    while left <= right:
        f.seek(floor((left + right) / 2) * 8)
        c = f.read(8)
        lon, lat, x, y = struct.unpack('HHHH', c)
        if lon == lon_check and lat == lat_check:
            f.close()
            return y, x
        elif (lon, lat) < (lon_check, lat_check):
            left = floor((left + right) / 2) + 1
        elif (lon, lat) > (lon_check, lat_check):
            right = floor((left + right) / 2) - 1
    f.close()
    return 0, 0



def map_offset_in_china(lat, lon):
    global china_offset_data
    lat, lon = float(lat), float(lon)
    lat_check = int(lat * 100)
    lon_check = int(lon * 100)
    lat_off, lon_off = find_china_offset(lat_check, lon_check)
    siny = sin(lat * pi / 180.0)
    y = log((1 + siny) / ( 1 - siny))
    latpix = (128 << 18) * (1 - y / (2 * pi)) + lat_off
    y = 2 * pi * (1 - latpix/ (128 << 18))
    z = exp(y)
    siny = (z - 1) / (z + 1)
    new_lat = asin(siny) * 180 / pi
    lonpix = (lon + 180) * (256 << 18) / 360.0 + lon_off;
    new_lon = lonpix * 360 / (256 << 18) - 180
    return (new_lat, new_lon)


@app.route("/location_request")
@jsonify
def location_request():
    gcm = GCM(GCM_API_KEY)
    data = {"request": "positioning", "time": int(time())}
    if int(kv.get(app.secret_key + "_last_push") or 0) < time() - 60:
        res = gcm.json_request(
            registration_ids = [kv.get(app.secret_key + "_regid")],
            collapse_key = "positioning",
            data = data,
            time_to_live = 60,
            delay_while_idle = False,
        )
        kv.set(app.secret_key + "_last_push", int(time()))
        return res
    else:
        return {'mark': 'too_frequent'}

@app.route("/update_regid")
@jsonify
def update_regid():
    kv.set(app.secret_key + "_regid", request.args.get(UPDATE_PASSWORD))
    return {}

@app.route("/update_location")
@jsonify
def update_location():
    loc = request.args.get(UPDATE_PASSWORD).split(",")
    data = {
        'latitude': loc[0],
        "longtitude": loc[1],
        "accuracy": loc[2],
    }
    kv.setex(app.secret_key + "_last_known_location", json.dumps(data), 60)
    return {}

@app.route("/get_best_location")
def get_best_location():
    if request.args.get("password") in ACCURATE_LOCATION_PASSWORD:
        r = kv.get(app.secret_key + "_last_known_location") or "{}"
        if USER_IN_CHINA and CHINA_OFFSET_DATA_FILE:
            r["latitude"], r["longtitude"] = map_offset_in_china(r["latitude"], r["longtitude"])
        return Response(r, mimetype='application/json')
    else:
        return Response("{}", mimetype='application/json')

@app.route('/get_location')
@jsonify
def get_location():
    r = kv.get(app.secret_key + "_last_known_location") or "{}"
    if len(r) >= 3:
        j = json.loads(r)
        if USER_IN_CHINA and CHINA_OFFSET_DATA_FILE:
            j["latitude"], j["longtitude"] = map_offset_in_china(j["latitude"], j["longtitude"])
        if ACCURATE_MODE:
            return j
        now = time() + LOCATION_FLOAT_PASSWORD
        float_angel = ((now / 10000) % 3600 * 0.1) * pi / 180
        float_distance = 5000 + now % 10000 * 0.5
        R = sin((90 - float(j['latitude'])) * pi / 180) * 6371000
        distance_move_north = float_distance * cos(float_angel)
        distance_move_east = float_distance * sin(float_angel)
        print float_distance ** 2, distance_move_east * distance_move_east +  distance_move_north * distance_move_north
        j["accuracy"] = str(float(j["accuracy"]) + float_distance * 2)
        degree_move_north = distance_move_north / (6371000.0 / 90)
        degree_move_east = distance_move_east / (2 * pi * R / 360.0)
        j["latitude"] = str(float(j["latitude"]) + degree_move_north)
        j["longtitude"] = str(float(j["longtitude"]) + degree_move_east)
        return j
    else:
        return {}



@app.route("/")
def homepage():
    html = """<!doctype html>
<html>
<head>
    <meta charset="UTF-8"/>
    <title>""" + WEB_TITLE + """</title>
    <link href="//jquery-loadmask.googlecode.com/svn/trunk/src/jquery.loadmask.css" rel="stylesheet" type="text/css" />
    <script src="//ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>
    <script src="//jquery-loadmask.googlecode.com/svn/trunk/src/jquery.loadmask.js"></script>
"""
    if USER_IN_CHINA and request.args.get('https') != '1':
        html += "<script type=\"text/javascript\" src=\"http://ditu.google.cn/maps/api/js?sensor=false&language=cn\"></script>"
    else:
        html += """<script type="text/javascript" src="https://maps.googleapis.com/maps/api/js?key=""" + MAPS_BROSWER_API_KEY + """&sensor=true"></script>"""
    html += """<style>
    html, body, #map-canvas, #map-canvas-mask {
        margin: 0;
        padding: 0;
        height: 100%;
    }
    </style>
    <script type="text/javascript">
        retry = 15;
        have_once = 0;
        function set_marker(myloc, data) {
        lastmarker = new google.maps.Marker({
                            position: myloc,
                            map: map,
                            title: "我在這裏"
                        })
                        var mylocCircle = {
                            strokeColor: '#FF0000',
                            strokeOpacity: 0.8,
                            strokeWeight: 2,
                            fillColor: '#FF0000',
                            fillOpacity: 0.35,
                            map: map,
                            center: myloc,
                            radius: parseFloat(data["accuracy"])
                        };
                        lastcircle = new google.maps.Circle(mylocCircle);
        }
        function check_result() {
            if (retry > 0) {
                retry = retry - 1;
                $.get("/get_location", function(data) {
                    if (data["accuracy"]) {
                        have_once = 1;
                        $("#map-canvas-mask").unmask();
                        var myloc = new google.maps.LatLng(data["latitude"], data["longtitude"]);
                        var div4 = parseFloat(data["accuracy"]) * 100;
                        var zoomlevel = 1;
                        var table = {
                            1: 591657550.500000,
                            2: 295828775.300000,
                            3: 147914387.600000,
                            4: 73957193.820000,
                            5: 36978596.910000,
                            6: 18489298.450000,
                            7: 9244649.227000,
                            8: 4622324.614000,
                            9: 2311162.307000,
                            10: 1155581.153000,
                            11: 577790.576700,
                            12: 288895.288400,
                            13: 144447.644200,
                            14: 72223.822090,
                            15: 36111.911040,
                            16: 18055.955520,
                            17: 9027.977761,
                            18: 4513.988880,
                            19: 2256.994440,
                            20: 1128.497220
                        }
                        for (var i = 1; i <= 20; i++) {
                            if (div4 < table[i]) zoomlevel = i;
                            else break;
                        }
                        map.panTo(myloc);
                        map.setZoom(zoomlevel);
                        if (lastmarker)
                            lastmarker.setMap(null);
                        if (lastcircle)
                            lastcircle.setMap(null);
                        setTimeout(function() { set_marker(myloc, data); }, 100);
                        setTimeout(send_request, 60000);
                    } else {
                        setTimeout(check_result, 5000);
                    }
                })
            } else if (retry == 0) {
                $("#map-canvas-mask").unmask()
                if (have_once == 0) {
                    $("#map-canvas-mask").mask("無法取得我現在的位置");
                }
                setTimeout(send_request, 60000);
            }
        }
        function send_request() {
            if (have_once == 0) {
                lastmarker = null;
                lastcircle = null;
                $("#map-canvas-mask").mask("正在嘗試取得我的位置");
            } else {
                //$("#map-canvas-mask").mask("正在嘗試獲取新位置");
            }
            $.get("location_request", function(data) {
                retry = 12;
                setTimeout(check_result, 5000);
            })
        }
        function initialize() {
            var mapOptions = {
                center: new google.maps.LatLng(0, 0),
                zoom: 2,
                mapTypeId: google.maps.MapTypeId.ROADMAP
            };
            map = new google.maps.Map(document.getElementById("map-canvas"),
                mapOptions);
            send_request()
        }
        google.maps.event.addDomListener(window, 'load', initialize);
    </script>
</head>
<body style="overflow: hidden;">
    <div id="map-canvas-mask">
        <div id="map-canvas"/>
    </div>
    <script type="text/javascript">
    </script>
"""
    html += "</body>\n</html>"
    return Response(html, mimetype="text/html;charset=UTF-8")


if __name__ == "__main__":
    app.run("0.0.0.0", debug=True)
