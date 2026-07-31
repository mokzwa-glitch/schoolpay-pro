from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ==========================
# UTILISATEURS
# ==========================
class Utilisateur(db.Model):
    __tablename__ = "utilisateurs"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False,
        default="Secretaire"
    )

    def __repr__(self):
        return f"<Utilisateur {self.username}>"


# ==========================
# CLASSES
# ==========================
class Classe(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    eleves = db.relationship(
        "Eleve",
        backref="classe",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Classe {self.nom}>"


# ==========================
# ELEVES
# ==========================
class Eleve(db.Model):
    __tablename__ = "eleves"

    id = db.Column(db.Integer, primary_key=True)

    matricule = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    nom = db.Column(
        db.String(100),
        nullable=False
    )

    postnom = db.Column(
        db.String(100),
        nullable=False
    )

    prenom = db.Column(
        db.String(100),
        nullable=False
    )

    sexe = db.Column(
        db.String(10),
        nullable=False
    )

    classe_id = db.Column(
        db.Integer,
        db.ForeignKey("classes.id"),
        nullable=False
    )

    paiements = db.relationship(
        "Paiement",
        backref="eleve",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Eleve {self.matricule}>"


# ==========================
# PAIEMENTS
# ==========================
class Paiement(db.Model):
    __tablename__ = "paiements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    eleve_id = db.Column(
        db.Integer,
        db.ForeignKey("eleves.id"),
        nullable=False
    )

    montant = db.Column(
        db.Float,
        nullable=False
    )

    motif = db.Column(
        db.String(100),
        nullable=False
    )

    date_paiement = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Paiement {self.id}>"


# ==========================
# PARAMETRES
# ==========================
class Parametre(db.Model):
    __tablename__ = "parametres"

    id = db.Column(db.Integer, primary_key=True)

    nom_ecole = db.Column(db.String(150))
    adresse = db.Column(db.String(200))
    telephone = db.Column(db.String(50))
    email = db.Column(db.String(100))
    devise = db.Column(db.String(20), default="USD")

    def __repr__(self):
        return f"<Parametre {self.nom_ecole}>"


# ==========================
# HISTORIQUE
# ==========================
class Historique(db.Model):
    __tablename__ = "historique"

    id = db.Column(db.Integer, primary_key=True)

    utilisateur = db.Column(
        db.String(50),
        nullable=False
    )

    action = db.Column(
        db.String(255),
        nullable=False
    )

    date_action = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Historique {self.utilisateur}>"