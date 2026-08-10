import os

class Config:

    # Base de données SQLite locale à l'application
    SQLALCHEMY_DATABASE_URI = "sqlite:///schoolpay.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "schoolpay-secret-2026"
    )