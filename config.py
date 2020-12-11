import os
from dotenv import load_dotenv
import datetime

JWT_SECRET_KEY = "potatoes"

JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(minutes=20)
JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(days=60)

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{}:{}@{}/{}".format(
    os.getenv("DB_USER"),
    os.getenv("DB_PASSWORD"),
    os.getenv("DB_HOST"),
    os.getenv("DB_NAME"),
)