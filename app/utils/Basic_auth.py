from flask import Response, request
from flask_httpauth import HTTPBasicAuth
from Credentials import APIusername, APIpassword

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == APIusername and password == APIpassword:
        return True
    return False

 