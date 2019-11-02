from .OrangeDB import Orange
from mongoengine import connect
from redis import Redis

config = Orange("config.json", load=True)
connect(config['database']['mongo']['url'])
redis = Redis(host=config['database']['redis']['url'])
