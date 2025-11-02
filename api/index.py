from http.server import BaseHTTPRequestHandler
from frontend.app import app as application

def handler(event, context):
    return application(event, context)
