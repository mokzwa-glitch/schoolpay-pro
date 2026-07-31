import os

class Config:
    # Utilise DATABASE_URL si elle existe (Render/Railway),
    # sinon utilise la base locale.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost/schoolpay"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "schoolpay-secret-2026"
    )