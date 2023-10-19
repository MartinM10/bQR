from os import environ as env

from dotenv import load_dotenv

load_dotenv()

DEBUG = env['DEBUG']
USER_EMAIL = env['USER_EMAIL']
PASSWORD_EMAIL = env['PASSWORD_EMAIL']
DOMAIN = env['DOMAIN']
SECRET_KEY = env['SECRET_KEY']
