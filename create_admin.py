from app import app
from database.models import db, Utilisateur
from werkzeug.security import generate_password_hash

with app.app_context():

    # Supprimer l'ancien admin s'il existe
    admin = Utilisateur.query.filter_by(username="admin").first()

    if admin:
        db.session.delete(admin)
        db.session.commit()
        print("Ancien administrateur supprimé.")

    # Créer un nouvel administrateur
    admin = Utilisateur(
        username="admin",
        password=generate_password_hash("admin123"),
        role="Administrateur"
    )

    db.session.add(admin)
    db.session.commit()

    print("===================================")
    print("Administrateur créé avec succès !")
    print("Utilisateur : admin")
    print("Mot de passe : admin123")
    print("===================================")