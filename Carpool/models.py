from mongoengine import *
from enum import Enum
from secrets import token_hex


class User(Document):

    id = StringField(unique=True, primary_key=True, default=lambda: token_hex(5))
    email = StringField(required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    profile_picture = StringField(required=False)
    phone_number = StringField(required=False)

    # coordinated [x, y], longitude and latitude
    location = PointField(auto_index=True)

    @classmethod
    def register(cls, email, first_name, last_name, profile_picture, phone_number):
        user = cls()
        user.email = email.lower()
        user.first_name = first_name
        user.last_name = last_name
        user.profile_picture = profile_picture
        user.phone_number = phone_number
        user.save()
        return user

    @classmethod
    def find_with_email(cls, email):
        return cls.objects.get(email=email.lower())

    def update_location(self, lon, lat):
        self.location = [lon, lat]
        self.save()

    def send_text(self, text_message):
        pass

    def send_push(self, push_data):
        pass

    def make_json(self):
        json = {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "profile_picture": self.profile_picture,
            "phone_number": self.phone_number,
            "location": {
            }
        }

        if self.location:
            json['location']['longitude'] = self.location[0]
            json['location']['latitude'] = self.location[1]

        return json


class RideRequest(Document):

    id = StringField(unique=True, primary_key=True, default=lambda: token_hex(5))
    by_user = ReferenceField(User)
    at_time = FloatField(required=True)
    before_flex = IntField(required=True)
    after_flex = IntField(required=True)

    start = FloatField(required=True)
    end = FloatField(required=True)

    location = PointField(auto_index=True)
    destination = PointField(auto_index=False)

    @classmethod
    def create(cls, by_user, time, before_flex, after_flex,
               location_lon, location_lat, dest_lon, dest_lat):
        req = cls()
        req.by_user = by_user
        req.location = [location_lon, location_lat]
        req.destination = [dest_lon, dest_lat]
        req.start = time - before_flex
        req.end = time + after_flex
        req.save()
        return req

    @classmethod
    def find_for_user(cls, user):
        return cls.objects(by_user=user)

    @classmethod
    def find_within(cls, lon, lat, radius):
        """ radius is in meters """
        return cls.objects(location__near=[lon, lat], location__max_distance=radius)

    @classmethod
    def find_within_time(cls, lon, lat, radius, start, end):
        """ radius is in meters """
        return cls.objects(location__near=[lon, lat], location__max_distance=radius,
                           start__qe=start, end__lt=end)

    def make_json(self):
        json = {
            "id": self.id,
            "user": self.by_user.make_json(),
            "start": self.start,
            "end": self.end,
            "location": {
                "longitude": self.location[0],
                "latitude": self.location[1]
            },
            "destination": {
                "longitude": self.destination[0],
                "latitude": self.destination[1]
            },
            "before_flex": self.before_flex,
            "after_flex": self.after_flex
        }

        return json


class Ride(Document):

    id = StringField(unique=True, primary_key=True, default=lambda: token_hex(5))
    by_user = ReferenceField(User)
    location = PointField(auto_index=True)
    destination = PointField(auto_index=False)

    start = FloatField()
    end = FloatField()

    @classmethod
    def create(cls, by_user, start, end, location_lon,
               location_lat, dest_lon, dest_lat):
        ride = cls()
        ride.by_user = by_user
        ride.start = start
        ride.end = end
        ride.location = [location_lon, location_lat]
        ride.destination = [dest_lon, dest_lat]
        ride.save()
        return ride

    @classmethod
    def find_for_user(cls, user):
        return cls.objects(by_user=user)

    def make_json(self):
        json = {
            "id": self.id,
            "user": self.by_user.make_json(),
            "start": self.start,
            "end": self.end,
            "location": {
                "longitude": self.location[0],
                "latitude": self.location[1]
            },
            "destination": {
                "longitude": self.destination[0],
                "latitude": self.destination[1]
            },
        }

        return json


class EnumField(object):
    """
    A class to register Enum type (from the package enum34) into mongo
    :param choices: must be of :class:`enum.Enum`: type
        and will be used as possible choices
    """

    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        kwargs['choices'] = [choice for choice in enum]
        super(EnumField, self).__init__(*args, **kwargs)

    def __get_value(self, enum):
        return enum.value if hasattr(enum, 'value') else enum

    def to_python(self, value):
        return self.enum(super(EnumField, self).to_python(value))

    def to_mongo(self, value):
        return self.__get_value(value)

    def prepare_query_value(self, op, value):
        return super(EnumField, self).prepare_query_value(
                op, self.__get_value(value))

    def validate(self, value):
        return super(EnumField, self).validate(self.__get_value(value))

    def _validate(self, value, **kwargs):
        return super(EnumField, self)._validate(
                self.enum(self.__get_value(value)), **kwargs)


class RideMatchingStatus(Enum):

    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class RideMatching(Document):

    id = StringField(unique=True, primary_key=True, default=lambda: token_hex(5))
    driver = ReferenceField(User)
    rider = ReferenceField(User)
    ride = ReferenceField(Ride)
    request = ReferenceField(RideRequest)
    cost = FloatField()
    status = EnumField(RideMatchingStatus)

    @classmethod
    def create(cls, driver, rider, ride, request, cost):
        match = cls()
        match.status = RideMatchingStatus.pending
        match.rider = rider
        match.ride = ride
        match.request = request
        match.cost = cost
        match.driver = driver
        match.save()
        return match

    @classmethod
    def find_with_driver(cls, driver):
        return cls.objects(driver=driver)

    @classmethod
    def find_with_rider(cls, rider):
        return cls.objects(rider=rider)

    @classmethod
    def find_with_ride(cls, ride):
        return cls.objects(ride=ride)

    @classmethod
    def find_with_request(cls, request):
        return cls.objects(request=request)

    def accept(self):
        self.status = RideMatchingStatus.accepted
        self.save()

    def reject(self):
        self.status = RideMatchingStatus.rejected
        self.save()

    def make_json(self):
        json = {
            "id": self.id,
            "rider": self.rider.make_json(),
            "driver": self.driver.make_json(),
            "ride": self.ride.make_json(),
            "request": self.request.make_json(),
            "cost": self.cost,
            "status": self.status
        }

        return json
