import os

class Config:
    UPLOAD_FOLDER = os.path.abspath(os.path.dirname(__file__)) + '/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024
