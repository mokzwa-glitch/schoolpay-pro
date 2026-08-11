import os


class Config:

    # ==========================================================
    # BASE DE DONNÉES
    # ==========================================================

    database_url = os.getenv("DATABASE_URL")

    if database_url:

        # Ancien format PostgreSQL
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://",
                "postgresql://",
                1
            )

        # Format PostgreSQL recommandé
        SQLALCHEMY_DATABASE_URI = database_url

    else:

        # ------------------------------------------------------
        # Développement local
        # ------------------------------------------------------
        # Si DATABASE_URL n'existe pas, l'application utilise
        # SQLite localement.
        # ------------------------------------------------------

        SQLALCHEMY_DATABASE_URI = (
            "sqlite:///schoolpay.db"
        )

    # ==========================================================
    # FLASK-SQLALCHEMY
    # ==========================================================

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================================
    # SÉCURITÉ
    # ==========================================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "schoolpay-secret-2026"
    )