from app import app
from database.models import db, Utilisateur
from werkzeug.security import generate_password_hash

with app.app_context():

    admin = Utilisateur.query.filter_by(username="admin").first()

    if admin:
        print("L'administrateur existe déjà.")

    else:

        admin = Utilisateur(
            username="admin",
            password=generate_password_hash("admin123")
        )

        db.session.add(admin)
        db.session.commit()

        print("Administrateur créé avec succès !")