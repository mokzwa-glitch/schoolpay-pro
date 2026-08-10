# ==================================================
# IMPORTATION DES MODELES
# ==================================================

from database.models import (
    db,
    Role,
    Utilisateur,
    Classe,
    Eleve,
    AnneeScolaire,
    MotifPaiement,
    Paiement,
    Parametre,
    Historique,
    Notification,
    Sauvegarde,
    CarteEleve
)

# ==================================================
# IMPORTS
# ==================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

from functools import wraps
from datetime import datetime

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

from openpyxl import Workbook

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph
)


from sqlalchemy import text
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import os
import qrcode 
import subprocess
import shutil

from config import Config

# ==================================================
# APPLICATION
# ==================================================

app = Flask(__name__)

app.config.from_object(Config)

app.secret_key = app.config["SECRET_KEY"]

db.init_app(app)

# ==================================================
# DOSSIERS
# ==================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "static",
    "uploads"
)

BACKUP_FOLDER = os.path.join(
    app.root_path,
    "backups"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

os.makedirs(
    BACKUP_FOLDER,
    exist_ok=True
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["BACKUP_FOLDER"] = BACKUP_FOLDER

# ==================================================
# HISTORIQUE
# ==================================================

def enregistrer_action(action):

    try:

        utilisateur = session.get("user", "Administrateur")

        historique = Historique(

            utilisateur=utilisateur,

            action=action,

            date_action=datetime.utcnow()

        )

        db.session.add(historique)

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        print("Erreur historique :", e)
        

# ==================================================
# LOGIN REQUIRED
# ==================================================

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if session.get("user") is None:

            flash(
                "Veuillez vous connecter.",
                "warning"
            )

            return redirect(
                url_for("login")
            )

        return f(*args, **kwargs)

    return decorated_function

# ==================================================
# ADMIN REQUIRED
# ==================================================

def admin_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if session.get("role") != "Administrateur":

            flash(
                "Accès refusé.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return f(*args, **kwargs)

    return decorated_function

# ==================================================
# NOTIFICATIONS
# ==================================================

@app.route("/notifications")
@login_required
def notifications():

    notifications = Notification.query.order_by(
        Notification.date_creation.desc()
    ).all()

    return render_template(
        "notifications.html",
        notifications=notifications
    )




def ajouter_notification(titre, message, type="info"):

    notification = Notification(

        titre=titre,

        message=message,

        type=type

    )

    db.session.add(notification)

    db.session.commit()


@app.route("/notification/lue/<int:id>")
@login_required
def notification_lue(id):

    notification = Notification.query.get_or_404(id)

    notification.lu = True

    db.session.commit()

    return redirect(
        url_for("notifications")
    )



# ==================================================
# VARIABLES GLOBALES POUR TOUS LES TEMPLATES
# ==================================================

@app.context_processor
def inject_global_variables():

    try:
        nb_notifications = Notification.query.filter_by(
            lue=False
        ).count()
    except Exception:
        nb_notifications = 0

    param = Parametre.query.first()

    return dict(
        nb_notifications=nb_notifications,
        param=param
    )


# ==================================================
# CREATION DES ROLES
# ==================================================

def creer_roles():

    if Role.query.count() > 0:
        return

    roles = [

        "Administrateur",

        "Directeur",

        "Secrétaire",

        "Comptable",

        "Caissier"

    ]

    for nom in roles:

        db.session.add(

            Role(

                nom=nom

            )

        )

    db.session.commit()

    print("Rôles créés.")


# ==================================================
# CREATION DES MOTIFS
# ==================================================

def creer_motifs():

    if MotifPaiement.query.count() > 0:
        return

    liste = [

        "Inscription",

        "Réinscription",

        "Frais scolaires",

        "Uniforme",

        "Transport",

        "Cantine",

        "Bibliothèque",

        "Examen",

        "Activités culturelles",

        "Autres"

    ]

    for nom in liste:

        db.session.add(

            MotifPaiement(

                nom=nom

            )

        )

    db.session.commit()

    print("Motifs créés.")


# ==================================================
# CREATION DE L'ADMINISTRATEUR
# ==================================================

def creer_admin():

    admin = Utilisateur.query.filter_by(

        username="admin"

    ).first()

    if admin:

        return

    role = Role.query.filter_by(

        nom="Administrateur"

    ).first()

    if role is None:

        print("Le rôle Administrateur est introuvable.")

        return

    admin = Utilisateur(

        nom="Administrateur",

        postnom="",

        prenom="",

        username="admin",

        password=generate_password_hash("admin123"),

        telephone="",

        email="",

        role_id=role.id,

        actif=True

    )

    db.session.add(admin)

    db.session.commit()

    print("Administrateur créé.")


# ==================================================
# ACCUEIL
# ==================================================

@app.route("/")
def index():

    if "user" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# ==================================================
# LOGIN
# ==================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        utilisateur = Utilisateur.query.filter_by(
            username=username
        ).first()

        if utilisateur and check_password_hash(
            utilisateur.password,
            password
        ):

            # ==========================
            # Création de la session
            # ==========================

            session.clear()

            session["user"] = utilisateur.username
            session["user_id"] = utilisateur.id

            if utilisateur.role:
                session["role"] = utilisateur.role.nom
            else:
                session["role"] = "Utilisateur"

            enregistrer_action("Connexion")

            flash(
                f"Bienvenue {utilisateur.username}",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Nom d'utilisateur ou mot de passe incorrect.",
            "danger"
        )

    return render_template("login.html")

# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
@login_required
def logout():

    enregistrer_action("Déconnexion")

    session.clear()

    flash(
        "Déconnexion réussie.",
        "success"
    )

    return redirect(url_for("login"))


# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
@login_required
def dashboard():

    total_eleves = Eleve.query.count()

    total_classes = Classe.query.count()

    total_paiements = Paiement.query.count()

    total_utilisateurs = Utilisateur.query.count()

    montant_total = db.session.query(
        db.func.sum(Paiement.montant)
    ).scalar() or 0

    aujourd_hui = datetime.utcnow().date()

    montant_jour = db.session.query(
        db.func.sum(Paiement.montant)
    ).filter(
        db.func.date(Paiement.date_paiement)
        == aujourd_hui
    ).scalar() or 0

    derniers_paiements = Paiement.query.order_by(
        Paiement.date_paiement.desc()
    ).limit(5).all()

    derniers_eleves = Eleve.query.order_by(
        Eleve.id.desc()
    ).limit(5).all()

    return render_template(

        "dashboard.html",

        utilisateur=session.get("user"),

        role=session.get("role"),

        total_eleves=total_eleves,

        total_classes=total_classes,

        total_paiements=total_paiements,

        total_utilisateurs=total_utilisateurs,

        montant_total=montant_total,

        montant_jour=montant_jour,

        derniers_paiements=derniers_paiements,

        derniers_eleves=derniers_eleves

    )


# ==================================================
# ELEVES
# ==================================================

@app.route("/eleves", methods=["GET", "POST"])
@login_required
def eleves():

    # ==========================================
    # MATRICULE AUTOMATIQUE
    # ==========================================

    dernier = Eleve.query.order_by(Eleve.id.desc()).first()

    if dernier:
        numero = dernier.id + 1
    else:
        numero = 1

    matricule = f"ELV-{datetime.now().year}-{numero:05d}"

    # ==========================================
    # AJOUT D'UN ELEVE
    # ==========================================

    if request.method == "POST":

        try:

            matricule_form = request.form.get(
                "matricule",
                ""
            ).strip()

            nom = request.form.get(
                "nom",
                ""
            ).strip()

            postnom = request.form.get(
                "postnom",
                ""
            ).strip()

            prenom = request.form.get(
                "prenom",
                ""
            ).strip()

            sexe = request.form.get(
                "sexe",
                ""
            ).strip()

            date_naissance = (
                request.form.get("date_naissance")
                or None
            )

            lieu_naissance = request.form.get(
                "lieu_naissance",
                ""
            ).strip()

            adresse = request.form.get(
                "adresse",
                ""
            ).strip()

            telephone = request.form.get(
                "telephone",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip()

            nom_parent = request.form.get(
                "nom_parent",
                ""
            ).strip()

            telephone_parent = request.form.get(
                "telephone_parent",
                ""
            ).strip()

            profession_parent = request.form.get(
                "profession_parent",
                ""
            ).strip()

            classe_id = request.form.get(
                "classe_id"
            )

            # ======================================
            # VÉRIFICATIONS
            # ======================================

            if not nom or not postnom or not prenom:
                flash(
                    "Veuillez remplir le nom, le postnom et le prénom.",
                    "danger"
                )

                return redirect(
                    url_for("eleves")
                )

            if not classe_id:
                flash(
                    "Veuillez sélectionner une classe.",
                    "danger"
                )

                return redirect(
                    url_for("eleves")
                )

            if Eleve.query.filter_by(
                matricule=matricule_form
            ).first():

                flash(
                    "Ce matricule existe déjà.",
                    "danger"
                )

                return redirect(
                    url_for("eleves")
                )

            # ======================================
            # CRÉATION
            # ======================================

            eleve = Eleve(

                matricule=matricule_form,

                nom=nom,

                postnom=postnom,

                prenom=prenom,

                sexe=sexe,

                date_naissance=date_naissance,

                lieu_naissance=lieu_naissance,

                adresse=adresse,

                telephone=telephone,

                email=email,

                nom_parent=nom_parent,

                telephone_parent=telephone_parent,

                profession_parent=profession_parent,

                classe_id=int(classe_id)

            )

            db.session.add(eleve)

            db.session.commit()

            enregistrer_action(
                f"Ajout de l'élève "
                f"{eleve.nom} {eleve.postnom}"
            )

            flash(
                "Élève enregistré avec succès.",
                "success"
            )

            return redirect(
                url_for("eleves")
            )

        except Exception as e:

            db.session.rollback()

            flash(
                f"Erreur : {e}",
                "danger"
            )

    # ==========================================
    # RECHERCHE
    # ==========================================

    recherche = request.args.get(
        "recherche",
        ""
    ).strip()

    # ==========================================
    # CLASSE SÉLECTIONNÉE
    # ==========================================

    classe_id = request.args.get(
        "classe_id",
        type=int
    )

    # ==========================================
    # REQUÊTE DES ÉLÈVES
    # ==========================================

    query = Eleve.query

    # Recherche texte

    if recherche:

        recherche_like = f"%{recherche}%"

        query = query.filter(
            db.or_(
                Eleve.nom.like(recherche_like),
                Eleve.postnom.like(recherche_like),
                Eleve.prenom.like(recherche_like),
                Eleve.matricule.like(recherche_like)
            )
        )

    # Filtre par classe

    if classe_id:

        query = query.filter(
            Eleve.classe_id == classe_id
        )

    # Liste finale

    liste_eleves = query.order_by(
        Eleve.nom.asc(),
        Eleve.postnom.asc()
    ).all()

    # ==========================================
    # CLASSES
    # ==========================================

    classes = Classe.query.order_by(
        Classe.nom.asc()
    ).all()

    # ==========================================
    # NOMBRE D'ÉLÈVES PAR CLASSE
    # ==========================================

    nombres_par_classe = {}

    for classe in classes:

        nombres_par_classe[classe.id] = Eleve.query.filter_by(
            classe_id=classe.id
        ).count()

    # ==========================================
    # TOTAL ÉLÈVES
    # ==========================================

    total_eleves = Eleve.query.count()

    # ==========================================
    # RETOUR
    # ==========================================

    return render_template(

        "eleves.html",

        eleves=liste_eleves,

        classes=classes,

        matricule=matricule,

        total_eleves=total_eleves,

        nombres_par_classe=nombres_par_classe,

        classe_selectionnee=classe_id,

        recherche=recherche

    )


# ==================================================
# MODIFIER UN ELEVE
# ==================================================

@app.route("/modifier_eleve/<int:id>", methods=["GET", "POST"])
@login_required
def modifier_eleve(id):

    eleve = Eleve.query.get_or_404(id)

    if request.method == "POST":

        eleve.nom = request.form.get("nom", "").strip()
        eleve.postnom = request.form.get("postnom", "").strip()
        eleve.prenom = request.form.get("prenom", "").strip()
        eleve.sexe = request.form.get("sexe", "").strip()
        eleve.telephone = request.form.get("telephone", "").strip()
        eleve.email = request.form.get("email", "").strip()
        eleve.adresse = request.form.get("adresse", "").strip()
        eleve.nom_parent = request.form.get("nom_parent", "").strip()
        eleve.telephone_parent = request.form.get("telephone_parent", "").strip()
        eleve.profession_parent = request.form.get("profession_parent", "").strip()

        classe_id = request.form.get("classe_id")
        if classe_id:
            eleve.classe_id = int(classe_id)

        annee_id = request.form.get("annee_id")
        eleve.annee_id = int(annee_id) if annee_id else None

        db.session.commit()

        # ==========================================
        # ENREGISTRER DANS L'HISTORIQUE
        # ==========================================

        enregistrer_action(
            f"Modification de l'élève : {eleve.matricule} - {eleve.nom} {eleve.postnom} {eleve.prenom}"
        )

        flash(
            "Élève modifié avec succès.",
            "success"
        )

        return redirect(url_for("eleves"))

    classes = Classe.query.order_by(
        Classe.nom.asc()
    ).all()

    annees = AnneeScolaire.query.order_by(
        AnneeScolaire.id.desc()
    ).all()

    return render_template(
        "modifier_eleve.html",
        eleve=eleve,
        classes=classes,
        annees=annees
    )




# ==================================================
# FICHE ELEVE
# ==================================================

@app.route("/fiche_eleve/<int:id>")
@login_required
def fiche_eleve(id):

    eleve = Eleve.query.get_or_404(id)

    return render_template(
        "fiche_eleve.html",
        eleve=eleve
    )

# ==================================================
# SUPPRIMER UN ELEVE
# ==================================================

@app.route("/supprimer_eleve/<int:id>")
@login_required
def supprimer_eleve(id):

    eleve = Eleve.query.get_or_404(id)

    try:

        db.session.delete(eleve)

        db.session.commit()

        enregistrer_action(
            f"Suppression de l'élève {eleve.nom} {eleve.postnom}"
        )

        flash(
            "Élève supprimé avec succès.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        flash(
            f"Erreur : {e}",
            "danger"
        )

    return redirect(url_for("eleves"))




# ==================================================
# REÇU DE PAIEMENT
# ==================================================

@app.route("/recu/<int:id>")
@login_required
def recu(id):

    paiement = Paiement.query.get_or_404(id)

    return render_template(
        "recu.html",
        paiement=paiement
    )

# ==================================================
# REÇU PDF
# ==================================================

@app.route("/recu_pdf/<int:id>")
@login_required
def recu_pdf(id):

    paiement = Paiement.query.get_or_404(id)

    return render_template(
        "recu.html",
        paiement=paiement
    )


# ==================================================
# CLASSES
# ==================================================

@app.route("/classes", methods=["GET", "POST"])
@login_required
def classes():

    # ==============================
    # AJOUT
    # ==============================

    if request.method == "POST":

        try:

            nom = request.form.get("nom", "").strip()

            if nom == "":

                flash(
                    "Le nom de la classe est obligatoire.",
                    "danger"
                )

                return redirect(url_for("classes"))

            existe = Classe.query.filter_by(
                nom=nom
            ).first()

            if existe:

                flash(
                    "Cette classe existe déjà.",
                    "warning"
                )

                return redirect(url_for("classes"))

            classe = Classe(

                nom=nom,

                niveau=request.form.get("niveau"),

                titulaire=request.form.get("titulaire"),

            )

            db.session.add(classe)

            db.session.commit()

            enregistrer_action(
                f"Ajout classe {nom}"
            )

            flash(
                "Classe enregistrée avec succès.",
                "success"
            )

            return redirect(url_for("classes"))

        except Exception as e:

            db.session.rollback()

            flash(
                f"Erreur : {e}",
                "danger"
            )

    # ==============================
    # RECHERCHE
    # ==============================

    recherche = request.args.get(
        "recherche",
        ""
    ).strip()

    query = Classe.query

    if recherche:

        query = query.filter(

            Classe.nom.contains(recherche)

            |

            Classe.niveau.contains(recherche)

            |

            Classe.titulaire.contains(recherche)

        )

    liste = query.order_by(
        Classe.nom.asc()
    ).all()

    total_classes = Classe.query.count()

    return render_template(

        "classes.html",

        classes=liste,

        total_classes=total_classes

    )

@app.route("/modifier_classe/<int:id>", methods=["GET", "POST"])
@login_required
def modifier_classe(id):

    classe = Classe.query.get_or_404(id)

    if request.method == "POST":

        classe.nom = request.form.get("nom")

        classe.niveau = request.form.get("niveau")

        classe.titulaire = request.form.get("titulaire")

        classe.capacite = request.form.get("capacite")

        db.session.commit()

        enregistrer_action(
            f"Modification classe {classe.nom}"
        )

        flash(
            "Classe modifiée.",
            "success"
        )

        return redirect(url_for("classes"))

    return render_template(

        "modifier_classe.html",

        classe=classe

    )


@app.route("/supprimer_classe/<int:id>")
@login_required
@admin_required
def supprimer_classe(id):

    classe = Classe.query.get_or_404(id)

    if classe.eleves:

        flash(
            "Impossible de supprimer cette classe car elle contient des élèves.",
            "danger"
        )

        return redirect(url_for("classes"))

    enregistrer_action(
        f"Suppression classe {classe.nom}"
    )

    db.session.delete(classe)

    db.session.commit()

    flash(
        "Classe supprimée.",
        "success"
    )

    return redirect(url_for("classes"))


# ==================================================
# PAIEMENTS
# ==================================================

@app.route("/paiements", methods=["GET", "POST"])
@login_required
def paiements():

    # =====================================
    # AJOUT D'UN PAIEMENT
    # =====================================

    if request.method == "POST":

        try:

            eleve_id = request.form.get("eleve_id")
            motif_id = request.form.get("motif_id")
            montant = request.form.get("montant")

            devise = request.form.get("devise", "USD")
            mode_paiement = request.form.get("mode_paiement", "Espèces")
            reference = request.form.get("reference", "").strip()
            observation = request.form.get("observation", "").strip()

            # Vérification des champs

            if not eleve_id or not motif_id or not montant:

                flash(
                    "Veuillez remplir tous les champs obligatoires.",
                    "danger"
                )

                return redirect(url_for("paiements"))

            eleve_id = int(eleve_id)
            motif_id = int(motif_id)
            montant = float(montant)

            eleve = Eleve.query.get_or_404(eleve_id)
            motif = MotifPaiement.query.get_or_404(motif_id)

            # =====================================
            # Utilisateur connecté
            # =====================================

            utilisateur_id = session.get("user_id")

            if utilisateur_id is None:

                utilisateur = Utilisateur.query.filter_by(
                    username=session.get("user")
                ).first()

                if utilisateur:

                    utilisateur_id = utilisateur.id
                    session["user_id"] = utilisateur.id

                else:

                    flash(
                        "Session expirée.",
                        "danger"
                    )

                    return redirect(url_for("login"))

            # =====================================
            # Génération automatique du reçu
            # =====================================

            annee = datetime.now().year

            dernier = Paiement.query.filter(
                Paiement.numero_recu.like(f"REC-{annee}-%")
            ).order_by(Paiement.id.desc()).first()

            if dernier:

                try:

                    dernier_numero = int(
                        dernier.numero_recu.split("-")[-1]
                    )

                except Exception:

                    dernier_numero = 0

            else:

                dernier_numero = 0

            numero_recu = f"REC-{annee}-{dernier_numero + 1:06d}"

            # Vérification qu'il n'existe pas déjà

            while Paiement.query.filter_by(
                numero_recu=numero_recu
            ).first():

                dernier_numero += 1

                numero_recu = (
                    f"REC-{annee}-{dernier_numero + 1:06d}"
                )

            # =====================================
            # Création du paiement
            # =====================================

            paiement = Paiement(

                numero_recu=numero_recu,

                eleve_id=eleve.id,

                motif_id=motif.id,

                utilisateur_id=utilisateur_id,

                montant=montant,

                devise=devise,

                mode_paiement=mode_paiement,

                reference=reference,

                observation=observation

            )

            db.session.add(paiement)

            db.session.commit()

            enregistrer_action(
                f"Paiement {numero_recu}"
            )

            flash(
                "Paiement enregistré avec succès.",
                "success"
            )

            return redirect(url_for("paiements"))

        except Exception as e:

            db.session.rollback()

            flash(str(e), "danger")

    # =====================================
    # RECHERCHE
    # =====================================

    recherche = request.args.get(
        "recherche",
        ""
    ).strip()

    query = Paiement.query.join(Eleve).join(MotifPaiement)

    if recherche:

        query = query.filter(

            (Eleve.nom.contains(recherche))
            |
            (Eleve.postnom.contains(recherche))
            |
            (Eleve.prenom.contains(recherche))
            |
            (Eleve.matricule.contains(recherche))
            |
            (Paiement.numero_recu.contains(recherche))
            |
            (MotifPaiement.nom.contains(recherche))

        )

    liste = query.order_by(
        Paiement.date_paiement.desc()
    ).all()

    eleves = Eleve.query.order_by(
        Eleve.nom.asc()
    ).all()

    motifs = MotifPaiement.query.order_by(
        MotifPaiement.nom.asc()
    ).all()

    total_paiements = Paiement.query.count()

    montant_total = db.session.query(
        db.func.sum(Paiement.montant)
    ).scalar() or 0

    montant_jour = db.session.query(
        db.func.sum(Paiement.montant)
    ).filter(
        db.func.date(Paiement.date_paiement)
        == datetime.utcnow().date()
    ).scalar() or 0

    return render_template(

        "paiements.html",

        paiements=liste,

        eleves=eleves,

        motifs=motifs,

        total_paiements=total_paiements,

        montant_total=montant_total,

        montant_jour=montant_jour

    )

# ==================================================
# MOTIFS DE PAIEMENT
# ==================================================

@app.route("/motifs", methods=["GET", "POST"])
@login_required
@admin_required
def motifs():

    # ==============================
    # AJOUT
    # ==============================

    if request.method == "POST":

        try:

            nom = request.form.get(
                "nom",
                ""
            ).strip()

            if nom == "":

                flash(
                    "Le nom du motif est obligatoire.",
                    "danger"
                )

                return redirect(
                    url_for("motifs")
                )

            existe = MotifPaiement.query.filter_by(
                nom=nom
            ).first()

            if existe:

                flash(
                    "Ce motif existe déjà.",
                    "warning"
                )

                return redirect(
                    url_for("motifs")
                )

            motif = MotifPaiement(

                nom=nom

            )

            db.session.add(motif)

            db.session.commit()

            enregistrer_action(
                f"Ajout du motif {nom}"
            )

            flash(
                "Motif ajouté avec succès.",
                "success"
            )

            return redirect(
                url_for("motifs")
            )

        except Exception as e:

            db.session.rollback()

            flash(
                str(e),
                "danger"
            )

    # ==============================
    # RECHERCHE
    # ==============================

    recherche = request.args.get(
        "recherche",
        ""
    ).strip()

    query = MotifPaiement.query

    if recherche:

        query = query.filter(

            MotifPaiement.nom.contains(
                recherche
            )

        )

    liste = query.order_by(
        MotifPaiement.nom.asc()
    ).all()

    return render_template(

        "motifs.html",

        motifs=liste,

        total_motifs=len(liste)

    )

@app.route("/modifier_motif/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def modifier_motif(id):

    motif = MotifPaiement.query.get_or_404(id)

    if request.method == "POST":

        motif.nom = request.form.get(
            "nom"
        )

        db.session.commit()

        enregistrer_action(
            f"Modification du motif {motif.nom}"
        )

        flash(
            "Motif modifié.",
            "success"
        )

        return redirect(
            url_for("motifs")
        )

    return render_template(

        "modifier_motif.html",

        motif=motif

    )

@app.route("/supprimer_motif/<int:id>")
@login_required
@admin_required
def supprimer_motif(id):

    motif = MotifPaiement.query.get_or_404(id)

    if motif.paiements:

        flash(
            "Impossible de supprimer ce motif car il est utilisé.",
            "danger"
        )

        return redirect(
            url_for("motifs")
        )

    enregistrer_action(
        f"Suppression du motif {motif.nom}"
    )

    db.session.delete(motif)

    db.session.commit()

    flash(
        "Motif supprimé.",
        "success"
    )

    return redirect(
        url_for("motifs")
    )


# ==================================================
# MODIFIER UN PAIEMENT
# ==================================================

@app.route("/modifier_paiement/<int:id>", methods=["GET", "POST"])
@login_required
def modifier_paiement(id):

    paiement = Paiement.query.get_or_404(id)

    eleves = Eleve.query.order_by(Eleve.nom.asc()).all()

    motifs = MotifPaiement.query.order_by(MotifPaiement.nom.asc()).all()

    if request.method == "POST":

        try:

            paiement.eleve_id = int(request.form.get("eleve_id"))

            paiement.motif_id = int(request.form.get("motif_id"))

            paiement.montant = float(request.form.get("montant"))

            paiement.devise = request.form.get("devise")

            paiement.mode_paiement = request.form.get("mode_paiement")

            paiement.reference = request.form.get("reference")

            paiement.observation = request.form.get("observation")

            db.session.commit()

            enregistrer_action(
                f"Modification du paiement {paiement.numero_recu}"
            )

            flash(
                "Paiement modifié avec succès.",
                "success"
            )

            return redirect(url_for("paiements"))

        except Exception as e:

            db.session.rollback()

            flash(
                f"Erreur : {e}",
                "danger"
            )

    return render_template(

        "modifier_paiement.html",

        paiement=paiement,

        eleves=eleves,

        motifs=motifs

    )


# ==================================================
# DETAIL D'UN PAIEMENT
# ==================================================

@app.route("/detail_paiement/<int:id>")
@login_required
def detail_paiement(id):

    paiement = Paiement.query.get_or_404(id)

    return render_template(
        "detail_paiement.html",
        paiement=paiement
    )


# ==================================================
# SUPPRIMER UN PAIEMENT
# ==================================================

@app.route("/supprimer_paiement/<int:id>")
@login_required
@admin_required
def supprimer_paiement(id):

    paiement = Paiement.query.get_or_404(id)

    enregistrer_action(
        f"Suppression du paiement {paiement.numero_recu}"
    )

    db.session.delete(paiement)

    db.session.commit()

    flash(
        "Paiement supprimé avec succès.",
        "success"
    )

    return redirect(url_for("paiements"))





#========================================================
# UTILISATEURS
#========================================================
@app.route("/utilisateurs", methods=["GET", "POST"])
@login_required
@admin_required
def utilisateurs():

    # ==========================
    # AJOUT D'UN UTILISATEUR
    # ==========================

    if request.method == "POST":

        try:

            username = request.form.get("username", "").strip()

            if Utilisateur.query.filter_by(username=username).first():

                flash(
                    "Ce nom d'utilisateur existe déjà.",
                    "danger"
                )

                return redirect(url_for("utilisateurs"))

            utilisateur = Utilisateur(

                nom=request.form.get("nom", "").strip(),

                postnom=request.form.get("postnom", "").strip(),

                prenom=request.form.get("prenom", "").strip(),

                username=username,

                password=generate_password_hash(

                    request.form.get("password")

                ),

                telephone=request.form.get("telephone"),

                email=request.form.get("email"),

                role_id=int(request.form.get("role_id")),

                actif=True

            )

            db.session.add(utilisateur)

            db.session.commit()

            enregistrer_action(

                f"Création utilisateur {username}"

            )

            flash(

                "Utilisateur créé avec succès.",

                "success"

            )

            return redirect(

                url_for("utilisateurs")

            )

        except Exception as e:

            db.session.rollback()

            flash(str(e), "danger")

    # ==========================
    # RECHERCHE
    # ==========================

    recherche = request.args.get(

        "recherche",

        ""

    ).strip()

    query = Utilisateur.query.join(Role)

    if recherche:

        query = query.filter(

            (Utilisateur.nom.contains(recherche))

            |

            (Utilisateur.postnom.contains(recherche))

            |

            (Utilisateur.prenom.contains(recherche))

            |

            (Utilisateur.username.contains(recherche))

            |

            (Role.nom.contains(recherche))

        )

    liste = query.order_by(

        Utilisateur.nom.asc()

    ).all()

    roles = Role.query.order_by(

        Role.nom.asc()

    ).all()

    return render_template(

        "utilisateurs.html",

        utilisateurs=liste,

        roles=roles

    )

@app.route("/modifier_utilisateur/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def modifier_utilisateur(id):

    utilisateur = Utilisateur.query.get_or_404(id)

    if request.method == "POST":

        utilisateur.nom = request.form.get("nom")

        utilisateur.postnom = request.form.get("postnom")

        utilisateur.prenom = request.form.get("prenom")

        utilisateur.telephone = request.form.get("telephone")

        utilisateur.email = request.form.get("email")

        utilisateur.role_id = int(

            request.form.get("role_id")

        )

        if request.form.get("password"):

            utilisateur.password = generate_password_hash(

                request.form.get("password")

            )

        db.session.commit()

        enregistrer_action(

            f"Modification utilisateur {utilisateur.username}"

        )

        flash(

            "Utilisateur modifié.",

            "success"

        )

        return redirect(

            url_for("utilisateurs")

        )

    roles = Role.query.order_by(

        Role.nom.asc()

    ).all()

    return render_template(

        "modifier_utilisateur.html",

        utilisateur=utilisateur,

        roles=roles

    )

@app.route("/supprimer_utilisateur/<int:id>")
@login_required
@admin_required
def supprimer_utilisateur(id):

    utilisateur = Utilisateur.query.get_or_404(id)

    if utilisateur.id == session.get("user_id"):

        flash(

            "Impossible de supprimer le compte connecté.",

            "danger"

        )

        return redirect(

            url_for("utilisateurs")

        )

    enregistrer_action(

        f"Suppression utilisateur {utilisateur.username}"

    )

    db.session.delete(utilisateur)

    db.session.commit()

    flash(

        "Utilisateur supprimé.",

        "success"

    )

    return redirect(

        url_for("utilisateurs")
    )




# ==================================================
# PARAMÈTRES
# ==================================================

@app.route("/parametres", methods=["GET", "POST"])
@login_required
@admin_required
def parametres():

    # ==============================================
    # RÉCUPÉRATION DES PARAMÈTRES
    # ==============================================

    param = Parametre.query.first()

    # Si aucun paramètre n'existe encore,
    # on crée un enregistrement valide.

    if param is None:

        param = Parametre(
            nom_ecole="Complexe Scolaire La Suisse",
            devise="USD"
        )

        db.session.add(param)

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            flash(
                "Impossible de créer les paramètres de l'école.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )


    # ==============================================
    # ENREGISTREMENT
    # ==============================================

    if request.method == "POST":

        try:

            # --------------------------------------
            # NOM DE L'ÉCOLE
            # --------------------------------------

            nom_ecole = request.form.get(
                "nom_ecole",
                ""
            ).strip()


            if not nom_ecole:

                flash(
                    "Le nom de l'école est obligatoire.",
                    "danger"
                )

                return render_template(
                    "parametres.html",
                    param=param
                )


            # --------------------------------------
            # AUTRES INFORMATIONS
            # --------------------------------------

            adresse = request.form.get(
                "adresse",
                ""
            ).strip()


            telephone = request.form.get(
                "telephone",
                ""
            ).strip()


            email = request.form.get(
                "email",
                ""
            ).strip()


            site_web = request.form.get(
                "site_web",
                ""
            ).strip()


            devise = request.form.get(
                "devise",
                "USD"
            ).strip()


            # --------------------------------------
            # MISE À JOUR
            # --------------------------------------

            param.nom_ecole = nom_ecole

            param.adresse = adresse

            param.telephone = telephone

            param.email = email

            param.site_web = site_web

            param.devise = devise or "USD"


            # ======================================
            # LOGO
            # ======================================

            fichier = request.files.get("logo")


            if fichier and fichier.filename:

                from werkzeug.utils import secure_filename

                nom_fichier = secure_filename(
                    fichier.filename
                )


                # Vérification de l'extension

                extensions_autorisees = {
                    "png",
                    "jpg",
                    "jpeg",
                    "webp"
                }


                extension = (
                    nom_fichier
                    .rsplit(".", 1)[-1]
                    .lower()
                    if "." in nom_fichier
                    else ""
                )


                if extension not in extensions_autorisees:

                    flash(
                        "Format de logo non autorisé. "
                        "Utilisez PNG, JPG, JPEG ou WEBP.",
                        "danger"
                    )

                    return render_template(
                        "parametres.html",
                        param=param
                    )


                # ----------------------------------
                # DOSSIER UPLOADS
                # ----------------------------------

                os.makedirs(
                    app.config["UPLOAD_FOLDER"],
                    exist_ok=True
                )


                chemin_logo = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    nom_fichier
                )


                fichier.save(
                    chemin_logo
                )


                param.logo = nom_fichier


            # ======================================
            # SAUVEGARDE
            # ======================================

            db.session.commit()


            # ======================================
            # HISTORIQUE
            # ======================================

            enregistrer_action(
                "Modification des paramètres de l'école"
            )


            flash(
                "Paramètres enregistrés avec succès.",
                "success"
            )


            return redirect(
                url_for("parametres")
            )


        except Exception as e:

            db.session.rollback()


            flash(
                f"Erreur lors de l'enregistrement : {e}",
                "danger"
            )


    # ==============================================
    # AFFICHAGE
    # ==============================================

    return render_template(
        "parametres.html",
        param=param
    )


# ==================================================
# SAUVEGARDE DE LA BASE DE DONNÉES
# ==================================================

@app.route("/backup", methods=["GET", "POST"])
@login_required
@admin_required
def backup():

    if request.method == "POST":

        try:
            # Nom du fichier
            nom = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

            # Dossier de sauvegarde
            os.makedirs(
                app.config["BACKUP_FOLDER"],
                exist_ok=True
            )

            chemin = os.path.join(
                app.config["BACKUP_FOLDER"],
                nom
            )

            # Connexion SQLAlchemy
            connexion = db.engine.connect()

            # Récupérer les tables MySQL
            result = connexion.execute(
                text("SHOW TABLES")
            )

            tables = [
                ligne[0]
                for ligne in result
            ]

            with open(
                chemin,
                "w",
                encoding="utf-8"
            ) as fichier:

                fichier.write(
                    "-- ========================================\n"
                )

                fichier.write(
                    "-- SAUVEGARDE SCHOOLPAY PRO\n"
                )

                fichier.write(
                    f"-- Date : {datetime.now()}\n"
                )

                fichier.write(
                    "-- ========================================\n\n"
                )

                # --------------------------------------
                # SAUVEGARDE DE CHAQUE TABLE
                # --------------------------------------

                for table in tables:

                    fichier.write(
                        f"\n-- ========================================\n"
                        f"-- TABLE : {table}\n"
                        f"-- ========================================\n\n"
                    )

                    # Structure de la table
                    structure = connexion.execute(
                        text(f"SHOW CREATE TABLE `{table}`")
                    ).fetchone()

                    if structure:

                        create_table = structure[1]

                        fichier.write(
                            f"DROP TABLE IF EXISTS `{table}`;\n"
                        )

                        fichier.write(
                            create_table + ";\n\n"
                        )

                    # Récupérer les données
                    donnees = connexion.execute(
                        text(f"SELECT * FROM `{table}`")
                    )

                    colonnes = list(
                        donnees.keys()
                    )

                    for ligne in donnees:

                        valeurs = []

                        for valeur in ligne:

                            if valeur is None:

                                valeurs.append("NULL")

                            elif isinstance(
                                valeur,
                                (int, float)
                            ):

                                valeurs.append(
                                    str(valeur)
                                )

                            elif isinstance(
                                valeur,
                                bytes
                            ):

                                valeurs.append(
                                    "X'" +
                                    valeur.hex() +
                                    "'"
                                )

                            else:

                                texte = str(
                                    valeur
                                )

                                texte = texte.replace(
                                    "\\",
                                    "\\\\"
                                )

                                texte = texte.replace(
                                    "'",
                                    "''"
                                )

                                texte = texte.replace(
                                    "\n",
                                    "\\n"
                                )

                                texte = texte.replace(
                                    "\r",
                                    "\\r"
                                )

                                valeurs.append(
                                    "'" +
                                    texte +
                                    "'"
                                )

                        colonnes_sql = ", ".join(
                            f"`{colonne}`"
                            for colonne in colonnes
                        )

                        valeurs_sql = ", ".join(
                            valeurs
                        )

                        fichier.write(
                            f"INSERT INTO `{table}` "
                            f"({colonnes_sql}) "
                            f"VALUES ({valeurs_sql});\n"
                        )

                    fichier.write("\n")

            connexion.close()

            # --------------------------------------
            # TAILLE DU FICHIER
            # --------------------------------------

            taille = round(
                os.path.getsize(chemin) / 1024,
                2
            )

            # --------------------------------------
            # ENREGISTRER LA SAUVEGARDE
            # --------------------------------------

            sauvegarde = Sauvegarde(

                nom_fichier=nom,

                taille=f"{taille} Ko",

                utilisateur=session["user"]

            )

            db.session.add(
                sauvegarde
            )

            db.session.commit()

            enregistrer_action(
                "Création d'une sauvegarde"
            )

            flash(
                "Sauvegarde de la base de données créée avec succès.",
                "success"
            )

        except Exception as e:

            db.session.rollback()

            flash(
                f"Erreur lors de la sauvegarde : {str(e)}",
                "danger"
            )

        return redirect(
            url_for("backup")
        )

    # --------------------------------------
    # LISTE DES SAUVEGARDES
    # --------------------------------------

    sauvegardes = Sauvegarde.query.order_by(
        Sauvegarde.date_sauvegarde.desc()
    ).all()

    return render_template(
        "backup.html",
        sauvegardes=sauvegardes
    )




@app.route("/telecharger_backup/<path:nom>")
@login_required
@admin_required
def telecharger_backup(nom):

    chemin = os.path.join(
        app.config["BACKUP_FOLDER"],
        nom
    )

    if not os.path.isfile(chemin):
        flash(
            "La sauvegarde demandée n'existe pas.",
            "danger"
        )
        return redirect(url_for("backup"))

    return send_file(
        chemin,
        as_attachment=True,
        download_name=nom
    )


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")


# ==================================================
# A PROPOS
# ==================================================

@app.route("/apropos")
@login_required
def apropos():

    parametre = Parametre.query.first()

    return render_template(
        "apropos.html",
        parametre=parametre
    )



# ==================================================
# RAPPORT DES PAIEMENTS
# ==================================================

@app.route("/rapport_paiements")
@login_required
def rapport_paiements():

    paiements = Paiement.query.order_by(
        Paiement.date_paiement.desc()
    ).all()

    montant_total = db.session.query(
        db.func.sum(Paiement.montant)
    ).scalar() or 0

    return render_template(
        "rapport_paiements.html",
        paiements=paiements,
        montant_total=montant_total
    )

# ==================================================
# EXPORT EXCEL DES PAIEMENTS
# ==================================================

@app.route("/export_excel")
@login_required
def export_excel():

    try:
        paiements = Paiement.query.order_by(
            Paiement.date_paiement.desc()
        ).all()

        wb = Workbook()
        ws = wb.active
        ws.title = "Paiements"

        # En-têtes
        ws.append([
            "N° Reçu",
            "Élève",
            "Matricule",
            "Motif",
            "Montant",
            "Devise",
            "Mode de paiement",
            "Référence",
            "Date"
        ])

        # Données
        for paiement in paiements:

            eleve = paiement.eleve
            motif = paiement.motif

            nom_eleve = ""

            if eleve:
                nom_eleve = (
                    f"{eleve.nom} "
                    f"{eleve.postnom} "
                    f"{eleve.prenom}"
                ).strip()

            ws.append([
                paiement.numero_recu,
                nom_eleve,
                eleve.matricule if eleve else "",
                motif.nom if motif else "",
                paiement.montant,
                paiement.devise,
                paiement.mode_paiement,
                paiement.reference,
                paiement.date_paiement
            ])

        # Ajustement automatique des colonnes
        for colonne in ws.columns:

            longueur = 0
            lettre = colonne[0].column_letter

            for cellule in colonne:

                if cellule.value is not None:

                    longueur = max(
                        longueur,
                        len(str(cellule.value))
                    )

            ws.column_dimensions[lettre].width = (
                min(longueur + 2, 40)
            )

        # Dossier temporaire
        fichier = os.path.join(
            app.config["BACKUP_FOLDER"],
            "rapport_paiements.xlsx"
        )

        wb.save(fichier)

        enregistrer_action(
            "Export Excel des paiements"
        )

        return send_file(
            fichier,
            as_attachment=True,
            download_name="rapport_paiements.xlsx",
            mimetype=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

    except Exception as e:

        db.session.rollback()

        print(
            "ERREUR EXPORT EXCEL :",
            e
        )

        flash(
            f"Erreur lors de l'export Excel : {e}",
            "danger"
        )

        return redirect(
            url_for("rapport_paiements")
        )


# ==================================================
# IMPRIMER LES ELEVES
# ==================================================

@app.route("/imprimer_eleves")
@login_required
def imprimer_eleves():

    eleves = Eleve.query.order_by(
        Eleve.nom.asc()
    ).all()

    return render_template(
        "imprimer_eleves.html",
        eleves=eleves
    )


# ==========================================================
# CARTE D'IDENTIFICATION DE L'ÉLÈVE
# ==========================================================

@app.route("/carte_eleve/<int:id>")
@login_required
def carte_eleve(id):

    try:

        # --------------------------------------------------
        # 1. RÉCUPÉRER L'ÉLÈVE
        # --------------------------------------------------

        eleve = Eleve.query.get_or_404(id)


        # --------------------------------------------------
        # 2. RÉCUPÉRER LA CARTE EXISTANTE
        # --------------------------------------------------

        carte = CarteEleve.query.filter_by(
            eleve_id=eleve.id
        ).first()


        # --------------------------------------------------
        # 3. CRÉER LA CARTE SI ELLE N'EXISTE PAS
        # --------------------------------------------------

        if carte is None:

            annee = datetime.now().year


            derniere_carte = (
                CarteEleve.query
                .order_by(
                    CarteEleve.id.desc()
                )
                .first()
            )


            if derniere_carte:

                try:

                    dernier_numero = int(
                        derniere_carte.numero_carte
                        .split("-")[-1]
                    )

                except (ValueError, AttributeError):

                    dernier_numero = 0

            else:

                dernier_numero = 0


            numero = dernier_numero + 1


            numero_carte = (
                f"CAR-{annee}-{numero:06d}"
            )


            # ------------------------------------------------
            # ÉVITER UN DOUBLON
            # ------------------------------------------------

            while CarteEleve.query.filter_by(
                numero_carte=numero_carte
            ).first():

                numero += 1

                numero_carte = (
                    f"CAR-{annee}-{numero:06d}"
                )


            carte = CarteEleve(

                eleve_id=eleve.id,

                numero_carte=numero_carte

            )


            db.session.add(carte)

            db.session.flush()


        # --------------------------------------------------
        # 4. GÉNÉRER LE QR CODE
        # --------------------------------------------------

        if not carte.qr_code:

            resultat_qr = generer_qr_code(
                eleve,
                carte
            )

            if not resultat_qr:

                db.session.rollback()

                flash(
                    "Impossible de générer le QR code.",
                    "danger"
                )

                return redirect(
                    url_for("eleves")
                )


        # --------------------------------------------------
        # 5. ENREGISTRER
        # --------------------------------------------------

        db.session.commit()


        # --------------------------------------------------
        # 6. PARAMÈTRES DE L'ÉCOLE
        # --------------------------------------------------

        param = Parametre.query.first()


        # --------------------------------------------------
        # 7. AFFICHER LA CARTE
        # --------------------------------------------------

        return render_template(

            "carte_eleve.html",

            eleve=eleve,

            carte=carte,

            param=param

        )


    except Exception as e:

        db.session.rollback()

        print(
            "ERREUR CARTE ÉLÈVE :",
            e
        )

        flash(
            f"Erreur lors de la génération de la carte : {e}",
            "danger"
        )

        return redirect(
            url_for("eleves")
        )


    
# ==========================================================
# GÉNÉRER LE QR CODE D'UNE CARTE ÉLÈVE
# ==========================================================

def generer_qr_code(eleve, carte):

    try:

        # Dossier :
        # static/uploads/qr_codes/

        dossier_qr = os.path.join(
            UPLOAD_FOLDER,
            "qr_codes"
        )

        os.makedirs(
            dossier_qr,
            exist_ok=True
        )


        # Données contenues dans le QR

        donnees = (
            "SCHOOLPAY PRO\n"
            f"Matricule : {eleve.matricule}\n"
            f"Nom : {eleve.nom} {eleve.postnom} {eleve.prenom}\n"
            f"Classe : {eleve.classe.nom if eleve.classe else '-'}"
        )


        # Création du QR

        qr = qrcode.QRCode(

            version=1,

            error_correction=qrcode.constants.ERROR_CORRECT_M,

            box_size=8,

            border=4

        )

        qr.add_data(donnees)

        qr.make(
            fit=True
        )


        image = qr.make_image(
            fill_color="black",
            back_color="white"
        )


        # Nom du fichier

        nom_fichier = (
            f"qr_{eleve.matricule}.png"
        )


        chemin = os.path.join(
            dossier_qr,
            nom_fichier
        )


        # Enregistrer l'image

        image.save(
            chemin
        )


        # Chemin enregistré dans MySQL

        carte.qr_code = (
            f"qr_codes/{nom_fichier}"
        )


        return True


    except Exception as e:

        print(
            "ERREUR QR CODE :",
            e
        )

        return False


# ==================================================
# GESTION DES ERREURS
# ==================================================

@app.errorhandler(404)
def page_introuvable(error):

    return """
    <h1>404 - Page introuvable</h1>
    <p>La page demandée n'existe pas.</p>
    <a href="/dashboard">Retour au tableau de bord</a>
    """, 404


@app.errorhandler(500)
def erreur_serveur(error):

    try:
        db.session.rollback()
    except Exception:
        pass

    return """
    <h1>500 - Erreur serveur</h1>
    <p>Une erreur interne est survenue.</p>
    <a href="/dashboard">Retour au tableau de bord</a>
    """, 500


# ==================================================
# PARAMETRES GLOBAUX
# ==================================================

@app.context_processor
def inject_param():

    param = Parametre.query.first()

    return dict(param=param)


# ==================================================
# INITIALISATION
# ==================================================

with app.app_context():

    db.create_all()

    creer_roles()

    creer_motifs()

    creer_admin()

    if Parametre.query.count() == 0:

        db.session.add(

            Parametre(

                nom_ecole="SchoolPay Pro",

                devise="USD"

            )

        )

        db.session.commit()

    print("Base SchoolPay Pro recréée.")


# ==================================================
# HISTORIQUE
# ==================================================

@app.route("/historique")
@login_required
@admin_required
def historique():

    historiques = Historique.query.order_by(
        Historique.date_action.desc()
    ).all()

    return render_template(
        "historique.html",
        historiques=historiques
    )


# ==========================================================
# CARTES SCOLAIRES
# ==========================================================

@app.route("/cartes")
@login_required
def cartes():

    # Récupérer tous les élèves
    eleves = Eleve.query.order_by(
        Eleve.nom.asc(),
        Eleve.postnom.asc(),
        Eleve.prenom.asc()
    ).all()

    # Paramètres de l'école
    param = Parametre.query.first()

    return render_template(
        "cartes.html",
        eleves=eleves,
        param=param
    )





# ==========================================================
# CRÉATION DES TABLES
# ==========================================================

with app.app_context():

    db.create_all()

    creer_roles()

    creer_motifs()

    # seulement si cette fonction existe
    # creer_admin()


# ==========================================================
# LANCEMENT
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )