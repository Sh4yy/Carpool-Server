from flask import Blueprint, jsonify, abort, request
from .models import *

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
    if not driver:
        return abort(404, "driver not found")

    ride = Ride.objects.get(id=ride_id)
    matched_requests = RideRequest.find_within_time(
        lon=ride.location[0], lat=ride.location[1],
        radius=10 * 1000, start=ride.start, end=ride.end)

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

    ride = Ride.objects.get(id=ride_id)
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

    ride = Ride.objects.get(id=ride_id)
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

    ride = Ride.objects.get(id=ride_id)
    ride_match = RideMatching.objects.get(ride=ride, rider=user)
    if not ride_match:
        return abort(404)

    ride_match.reject()
    return jsonify(ride_match.make_json())


