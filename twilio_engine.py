import os
from twilio.rest import Client

def get_twilio_sid():
    return os.environ.get('TWILIO_ACCOUNT_SID', None)

def get_twilio_auth_token():
    return os.environ.get('TWILIO_AUTH_TOKEN', None)

def get_twilio_phone_number():
    return os.environ.get('TWILIO_PHONE_NUMBER', None)


def get_twilio_client():
    return Client(get_twilio_sid(), get_twilio_auth_token())


def get_twilio_messages():
    client = get_twilio_client()
    messages = client.messages.list()
    return messages