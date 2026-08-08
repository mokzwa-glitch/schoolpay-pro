from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ==========================================================
# ROLES
# ==========================================================

class Role(db.Model):

    __tablename__ = "roles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nom = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    utilisateurs = db.relationship(
        "Utilisateur",
        back_populates="role",
        lazy=True
    )

    def __repr__(self):
        return f"<Role {self.nom}>"




class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)

    titre = db.Column(db.String(150))

    message = db.Column(db.Text)

    type = db.Column(db.String(30))

    lu = db.Column(db.Boolean, default=False)

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )



# ==========================================================
# UTILISATEURS
# ==========================================================

class Utilisateur(db.Model):
    __tablename__ = "utilisateurs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    photo = db.Column(db.String(255))

    nom = db.Column(
        db.String(100),
        nullable=False
    )

    postnom = db.Column(db.String(100))

    prenom = db.Column(db.String(100))

    username = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    telephone = db.Column(db.String(30))

    email = db.Column(db.String(100))

    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id")
    )

    actif = db.Column(
        db.Boolean,
        default=True
    )

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    role = db.relationship(
        "Role",
        back_populates="utilisateurs"
    )

    paiements = db.relationship(
        "Paiement",
        back_populates="utilisateur",
        lazy=True
    )

    def __repr__(self):
        return f"<Utilisateur {self.username}>"


 

# ==================================================
# CREATION DES ROLES
# ==================================================

def creer_roles():

    roles = [

        "Administrateur",

        "Directeur",

        "Comptable",

        "Secrétaire"

    ]

    for nom in roles:

        existe = Role.query.filter_by(
            nom=nom
        ).first()

        if not existe:

            db.session.add(

                Role(

                    nom=nom

                )

            )

    db.session.commit()



# ==========================================================
# ANNEES SCOLAIRES
# ==========================================================

class AnneeScolaire(db.Model):
    __tablename__ = "annees_scolaires"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    annee = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    eleves = db.relationship(
        "Eleve",
        back_populates="annee",
        lazy=True
    )

    def __repr__(self):
        return f"<AnneeScolaire {self.annee}>"


# ==========================================================
# CLASSES
# ==========================================================

class Classe(db.Model):
    __tablename__ = "classes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nom = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    option = db.Column(
        db.String(100)
    )

    niveau = db.Column(
        db.String(50)
    )

    titulaire = db.Column(
        db.String(150)
    )

    eleves = db.relationship(
        "Eleve",
        back_populates="classe",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Classe {self.nom}>"

    
 # ==========================================================
# ELEVES
# ==========================================================

class Eleve(db.Model):
    __tablename__ = "eleves"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    photo = db.Column(
        db.String(255)
    )

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

    date_naissance = db.Column(
        db.Date
    )

    lieu_naissance = db.Column(
        db.String(100)
    )

    adresse = db.Column(
        db.String(255)
    )

    telephone = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(100)
    )

    nom_parent = db.Column(
        db.String(150)
    )

    telephone_parent = db.Column(
        db.String(30)
    )

    profession_parent = db.Column(
        db.String(100)
    )

    classe_id = db.Column(
        db.Integer,
        db.ForeignKey("classes.id"),
        nullable=False
    )

    annee_id = db.Column(
        db.Integer,
        db.ForeignKey("annees_scolaires.id")
    )

    date_inscription = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    actif = db.Column(
        db.Boolean,
        default=True
    )

    # ==========================
    # RELATIONS
    # ==========================

    classe = db.relationship(
        "Classe",
        back_populates="eleves"
    )

    annee = db.relationship(
        "AnneeScolaire",
        back_populates="eleves"
    )

    paiements = db.relationship(
        "Paiement",
        back_populates="eleve",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Eleve {self.matricule}>"


# ==========================================================
# MOTIFS DE PAIEMENT
# ==========================================================

class MotifPaiement(db.Model):
    __tablename__ = "motifs_paiement"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nom = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.String(255)
    )

    paiements = db.relationship(
        "Paiement",
        back_populates="motif",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<MotifPaiement {self.nom}>"





# ==========================================================
# PAIEMENTS
# ==========================================================

class Paiement(db.Model):

    __tablename__ = "paiements"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    numero_recu = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    eleve_id = db.Column(
        db.Integer,
        db.ForeignKey("eleves.id"),
        nullable=False
    )

    motif_id = db.Column(
        db.Integer,
        db.ForeignKey("motifs_paiement.id"),
        nullable=False
    )

    utilisateur_id = db.Column(
        db.Integer,
        db.ForeignKey("utilisateurs.id"),
        nullable=False
    )

    montant = db.Column(
        db.Float,
        nullable=False
    )

    devise = db.Column(
        db.String(10),
        default="USD",
        nullable=False
    )

    mode_paiement = db.Column(
        db.String(50),
        default="Espèces",
        nullable=False
    )

    reference = db.Column(
        db.String(100),
        nullable=True
    )

    observation = db.Column(
        db.Text,
        nullable=True
    )

    date_paiement = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ==========================
    # RELATIONS
    # ==========================

    eleve = db.relationship(
        "Eleve",
        back_populates="paiements"
    )

    motif = db.relationship(
        "MotifPaiement",
        back_populates="paiements"
    )

    utilisateur = db.relationship(
        "Utilisateur",
        back_populates="paiements"
    )

    def __repr__(self):
        return f"<Paiement {self.numero_recu}>"

    
    
# ==========================================================
# PARAMETRES
# ==========================================================

class Parametre(db.Model):
    __tablename__ = "parametres"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nom_ecole = db.Column(
        db.String(150),
        nullable=False,
        default="SchoolPay Pro"
    )

    logo = db.Column(
        db.String(255),
        nullable=True
    )

    adresse = db.Column(
        db.String(255),
        nullable=True
    )

    telephone = db.Column(
        db.String(50),
        nullable=True
    )

    email = db.Column(
        db.String(100),
        nullable=True
    )

    site_web = db.Column(
        db.String(150),
        nullable=True
    )

    devise = db.Column(
        db.String(20),
        nullable=False,
        default="USD"
    )

    directeur = db.Column(
        db.String(150),
        nullable=True
    )

    signature = db.Column(
        db.String(255),
        nullable=True
    )

    cachet = db.Column(
        db.String(255),
        nullable=True
    )

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Parametre {self.nom_ecole}>"


# ==================================================
# HISTORIQUE
# ==================================================

class Historique(db.Model):

    __tablename__ = "historiques"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    utilisateur = db.Column(
        db.String(100),
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

# ==========================================================
# SAUVEGARDES
# ==========================================================

class Sauvegarde(db.Model):
    __tablename__ = "sauvegardes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nom_fichier = db.Column(
        db.String(255),
        nullable=False
    )

    taille = db.Column(
        db.String(30)
    )

    utilisateur = db.Column(
        db.String(100)
    )

    date_sauvegarde = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<Sauvegarde {self.nom_fichier}>"


# ==========================================================
# CARTE D'ELEVE
# ==========================================================

class CarteEleve(db.Model):
    __tablename__ = "cartes_eleves"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    eleve_id = db.Column(
        db.Integer,
        db.ForeignKey("eleves.id"),
        nullable=False,
        unique=True
    )

    numero_carte = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    qr_code = db.Column(
        db.String(255)
    )

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    eleve = db.relationship(
        "Eleve",
        backref=db.backref(
            "carte",
            uselist=False
        )
    )

    def __repr__(self):
        return f"<CarteEleve {self.numero_carte}>"