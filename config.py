import os


class Config:

    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Railway peut fournir mysql:// ou mysql+mysqldb://.
        # Notre application utilise PyMySQL.
        if database_url.startswith("mysql://"):
            database_url = database_url.replace(
                "mysql://",
                "mysql+pymysql://",
                1
            )

        elif database_url.startswith("mysql+mysqldb://"):
            database_url = database_url.replace(
                "mysql+mysqldb://",
                "mysql+pymysql://",
                1
            )

    SQLALCHEMY_DATABASE_URI = database_url or (
        "mysql+pymysql://root:@localhost/schoolpay"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "schoolpay-secret-2026"
    )