from .OrangeDB import Orange
from mongoengine import connect
from redis import Redis
from twilio.rest import Client


config = Orange("config.json", load=True)
connect("db", host=config['database']['mongo']['url'])
redis = Redis(host=config['database']['redis']['url'])
twilio_client = Client(config['twilio']['account_sid'], config['twilio']['auth_token'])
