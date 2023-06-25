import os

class Config:
    UPLOAD_FOLDER = os.path.abspath(os.path.dirname(__file__)) + '/uploads'
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024
