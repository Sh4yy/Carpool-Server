from mongoengine import *


class User(Document):

    email = StringField(required=True, primary_key=True)
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

    def update_location(self, location):
        pass

    def send_text(self, text_message):
        pass

    def send_push(self, push_data):
        pass


class RideRequest(Document):

    by_user = ReferenceField(User)
    at_time = FloatField(required=True)
    before_flex = IntField(required=True)
    after_flex = IntField(required=True)

    start = FloatField(required=True)
    end = FloatField(required=True)

    location = PointField(auto_index=True)

    pickup_addr = StringField()
    dest_addr = StringField()

    @classmethod
    def create(cls, by_user, time, before_flex, after_flex, location, pickup_addr, dest_addr):
        req = cls()
        req.by_user = by_user
        req.location = location
        req.pickup_addr = pickup_addr
        req.dest_addr = dest_addr
        req.start = time - before_flex
        req.end = time + after_flex
        req.save()
        return req
