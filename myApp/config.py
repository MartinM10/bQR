from os import environ as env

from dotenv import load_dotenv

load_dotenv()

DEBUG = env['DEBUG']
USER_EMAIL = env['USER_EMAIL']
PASSWORD_EMAIL = env['PASSWORD_EMAIL']
DOMAIN = env['DOMAIN']
SECRET_KEY = env['SECRET_KEY']

# Google Auth
GOOGLE_CLIENT_ID = env['GOOGLE_CLIENT_ID']
GOOGLE_SECRET = env['GOOGLE_SECRET']

# Plan configurations
PLANS = {
    'FREE': {
        'price_monthly': float(env.get('FREE_PLAN_PRICE_MONTHLY', 0)),
        'price_yearly': float(env.get('FREE_PLAN_PRICE_YEARLY', 0)),
        'duration_days': int(env.get('FREE_PLAN_DURATION_DAYS', 365)),
        'notifications_per_month': int(env.get('FREE_PLAN_NOTIFICATIONS_PER_MONTH', 3)),
        'max_items': int(env.get('FREE_PLAN_MAX_ITEMS', 1)),
        'can_modify_notification_hours': False,
        'can_choose_notification_type': False,
    },
    'PREMIUM': {
        'price_monthly': float(env.get('PREMIUM_PLAN_PRICE_MONTHLY', 9.99)),
        'price_yearly': float(env.get('PREMIUM_PLAN_PRICE_YEARLY', 99.99)),
        'duration_days': int(env.get('PREMIUM_PLAN_DURATION_DAYS', 365)),
        'notifications_per_month': int(env.get('PREMIUM_PLAN_NOTIFICATIONS_PER_MONTH', 100)),
        'max_items': int(env.get('PREMIUM_PLAN_MAX_ITEMS', 5)),
        'can_modify_notification_hours': True,
        'can_choose_notification_type': True,
    },
    'PRO': {
        'price_monthly': float(env.get('PRO_PLAN_PRICE_MONTHLY', 19.99)),
        'price_yearly': float(env.get('PRO_PLAN_PRICE_YEARLY', 199.99)),
        'duration_days': int(env.get('PRO_PLAN_DURATION_DAYS', 365)),
        'notifications_per_month': int(env.get('PRO_PLAN_NOTIFICATIONS_PER_MONTH', 500)),
        'max_items': int(env.get('PRO_PLAN_MAX_ITEMS', 10)),
        'can_modify_notification_hours': True,
        'can_choose_notification_type': True,
    }
}
