from flask import Blueprint, jsonify, abort, request
from .models import *
from .utils import find_location
import json
from pprint import pprint
from .utils import find_location, find_business

mod = Blueprint("routes", __name__)


@mod.route('/user/<email>', methods=['GET'])
def get_user_info(email):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    return jsonify(user.make_json())


@mod.route("/user", methods=['POST'])
def register_user():

    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone_number = data.get('phone_number')
    profile_picture = data.get('profile_picture')

    user = User.register(email=email, first_name=first_name,
                         last_name=last_name, phone_number=phone_number,
                         profile_picture=profile_picture)

    try:
        user.send_text(f"Hey {user.first_name.capitalize()}, thank you for registering on InstaPool!")
    except Exception as e:
        print(e)

    return jsonify(user.make_json())


@mod.route('/user/<email>/location', methods=['UPDATE'])
def update_user_location(email):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    longitude = request.json['location']['longitude']
    latitude = request.json['location']['latitude']
    user.update_location(lon=longitude, lat=latitude)

    return jsonify(user.make_json())


@mod.route('/user/<email>/ride/request', methods=['POST'])
def request_new_ride(email):

    user = User.find_with_email(email)
    data = request.json

    if not user:
        return abort(404, "user not found")

    time = data.get('time')
    before_flex = data.get('before_flex')
    after_flex = data.get('after_flex')

    location_lon = data['location']['longitude']
    location_lat = data['location']['latitude']

    dest_lon = data['destination']['longitude']
    dest_lat = data['destination']['latitude']

    req = RideRequest.create(
        by_user=user, time=time, before_flex=before_flex,
        after_flex=after_flex, location_lon=location_lon,
        location_lat=location_lat, dest_lon=dest_lon, dest_lat=dest_lat)

    return jsonify(req.make_json())


@mod.route('/user/<email>/ride/request', methods=['GET'])
def get_ride_requests(email):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    requests = RideRequest.find_for_user(user)
    return jsonify(list(map(lambda x: x.make_json(), requests)))


@mod.route('/user/<email>/ride', methods=['POST'])
def post_new_ride(email):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    data = request.data
    data = json.loads(data.decode())

    start = data['start']
    end = data['end']

    location_lon = data['location']['longitude']
    location_lat = data['location']['latitude']

    dest_lon = data['destination']['longitude']
    dest_lat = data['destination']['latitude']

    ride = Ride.create(
        by_user=user, location_lon=location_lon, location_lat=location_lat,
        dest_lon=dest_lon, dest_lat=dest_lat, start=start, end=end
    )

    return jsonify(ride.make_json())


@mod.route('/user/<email>/ride', methods=['GET'])
def get_user_rides(email):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    rides = Ride.find_for_user(user)
    return jsonify(list(map(lambda x: x.make_json(), rides)))


@mod.route('/user/<email>/ride/<ride_id>/match', methods=['POST'])
def start_matching_ride(email, ride_id):

    # todo perform matching process
    # find users in route
    # create a match
    # notify users
    # return matches

    driver = User.find_with_email(email)
    print("here 1")
    if not driver:
        return abort(404, "driver not found")
    print("here 2")

    ride = Ride.objects.get(uid=ride_id)
    matched_requests = RideRequest.find_within_time(
        lon=ride.location['coordinates'][0], lat=ride.location['coordinates'][1],
        radius=50 * 1000, start=ride.start, end=ride.end)

    print("matched", matched_requests)

    for req in matched_requests:
        match = RideMatching.create(
            driver=ride.by_user, rider=req.by_user,
            ride=ride, request=req, cost=req.calculate_cost())

        # todo notify match
        req.by_user.send_text(
            f"""{req.by_user.first_name}, we have matched your ride with {driver.first_name},
                please confirm your pool"""
        )

    matches = RideMatching.find_with_ride(ride)
    return jsonify(list(map(lambda x: x.make_json(), matches)))


@mod.route('/user/<email>/ride/<ride_id>/match', methods=['GET'])
def get_matching_rides(email, ride_id):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    ride = Ride.objects.get(uid=ride_id)
    matches = RideMatching.find_with_ride(ride)
    return jsonify(list(map(lambda x: x.make_json(), matches)))


@mod.route('/user/<email>/ride/rider/matches', methods=['GET'])
def get_rider_match_offers(email):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    matches = RideMatching.objects(rider=user)
    return jsonify(list(map(lambda x: x.make_json(), matches)))


@mod.route('/user/<email>/ride/driver/matches', methods=['GET'])
def get_driver_match_offers(email):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    matches = RideMatching.objects(driver=user)
    return jsonify(list(map(lambda x: x.make_json(), matches)))


@mod.route('/user/<email>/ride/<ride_id>/match/accept', methods=['POST'])
def accept_ride_match(email, ride_id):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    ride = Ride.objects.get(uid=ride_id)
    ride_match = RideMatching.objects.get(ride=ride, rider=user)
    if not ride_match:
        return abort(404)

    ride_match.accept()
    return jsonify(ride_match.make_json())


@mod.route('/user/<email>/ride/<ride_id>/match/reject', methods=['POST'])
def reject_ride_match(email, ride_id):

    user = User.find_with_email(email)
    if not user:
        return abort(404, "user not found")

    ride = Ride.objects.get(uid=ride_id)
    ride_match = RideMatching.objects.get(ride=ride, rider=user)
    if not ride_match:
        return abort(404)

    ride_match.reject()
    ride_match.delete()
    return jsonify(ride_match.make_json())


@mod.route('/user/<email>/feed', methods=['GET'])
def get_user_feed(email):

    user = User.find_with_email(email)

    user_driving_rides = Ride.find_for_user(user)
    user_riding_rides = []

    print(user_driving_rides)

    matches = RideMatching.find_with_rider(user, status=RideMatchingStatus.accepted)
    for match in matches:
        if match.ride not in user_riding_rides:
            user_riding_rides.append(match.ride)

    ride_set = set(user_driving_rides).union(set(user_riding_rides))
    result = []

    for ride in ride_set:

        if ride in user_driving_rides:
            pickup = find_location({"latlng": f"{ride.location['coordinates'][1]}, {ride.location['coordinates'][0]}"})['formatted_address']
            dest = find_location({"latlng": f"{ride.destination['coordinates'][1]}, {ride.destination['coordinates'][0]}"})['formatted_address']
        else:
            match = RideMatching.objects.get(ride=ride, rider=user, status=RideMatchingStatus.accepted.value)
            pickup = find_location({"latlng": f"{match.request.location['coordinates'][1]}, {match.request.location['coordinates'][0]}"})['formatted_address']
            dest = find_location({"latlng": f"{match.request.destination['coordinates'][1]}, {match.request.destination['coordinates'][0]}"})['formatted_address']

        temp = {'ride': ride.make_json(),
                'pickup': pickup,
                'destination': dest,
                'matches': list(map(lambda x: x.make_json(), RideMatching.find_with_ride(ride, status=RideMatchingStatus.accepted)))}
        result.append(temp)

    pprint(result)
    return jsonify(result)


@mod.route('/geo/address', methods=['GET'])
def get_address():

    # latlng = 40.714224, -73.961452
    # address= 1113 Mitchell Building, College Park, MD

    address = request.json.get('address')
    coordinates = find_location({"address": address})['geometry']['location']

    return jsonify(coordinates)


@mod.route('/geo/coordinate', methods=['GET'])
def get_coordinate():

    lat = request.json.get('lat')
    lang = request.json.get('lang')

    address = find_location({"latlng": f"{lat}, {lang}"})['formatted_address']

    return jsonify({"address": address})


@mod.route('/geo/business/<business_name>', methods=['GET'])
def find_business_by_name(business_name):

    location = request.json.get("location")

    business = find_business({"radius": 1500,
                              "name": business_name,
                              "location": f"{location['lat']},{location['long']}"})

    return jsonify({"location": business["geometry"]["location"],
                    "name": business["name"]})
