from .OrangeDB import Orange
from mongoengine import connect
from redis import Redis
from twilio.rest import Client
import requests

config = Orange("config.json", load=True)
connect("db", host=config['database']['mongo']['url'])
redis = Redis(host=config['database']['redis']['url'])
twilio_client = Client(config['twilio']['account_sid'], config['twilio']['auth_token'])


def find_location(query):
    params = {'key': config['google']['api_key']}
    params.update(query)
    print(params)

    resp = requests.get(
        'https://maps.googleapis.com/maps/api/geocode/json',
        params=params,).json()

    if len(resp['results']) < 1:
        return

    return resp['results'][0]
