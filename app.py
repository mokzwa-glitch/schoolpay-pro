from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    flash
)

from database.models import (
    db,
    Utilisateur,
    Classe,
    Eleve,
    Paiement,
    Parametre,
    Historique
)

from config import Config
from database.models import (
    db,
    Utilisateur,
    Classe,
    Eleve,
    Paiement,
    Parametre
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from openpyxl import Workbook

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

import os
import subprocess
from datetime import datetime

from functools import wraps
from flask import session, flash, redirect, url_for

# =====================================
# CONFIGURATION
# =====================================

app = Flask(__name__)
app.config.from_object(Config)

app.secret_key = app.config["SECRET_KEY"]
app.config.from_object(Config)
print("DATABASE :", app.config["SQLALCHEMY_DATABASE_URI"])

db.init_app(app)

with app.app_context():
    db.create_all()


def enregistrer_action(action):

    historique = Historique(
        utilisateur=session.get("user"),
        action=action
    )

    db.session.add(historique)
    db.session.commit()



# =====================================
# ACCUEIL
# =====================================

@app.route("/")
def accueil():
    return redirect(url_for("login"))

# =====================================
# LOGIN
# =====================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # Si l'utilisateur est déjà connecté
    if "user" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        print("=" * 50)
        print("Tentative de connexion")
        print("Nom d'utilisateur :", username)

        utilisateur = Utilisateur.query.filter_by(
            username=username
        ).first()

        if utilisateur:
            print("Utilisateur trouvé :", utilisateur.username)
            print("Rôle :", utilisateur.role)
            print("Hash enregistré :", utilisateur.password)

            if check_password_hash(utilisateur.password, password):

                print("Mot de passe correct.")

                # Création de la session
                session["user"] = utilisateur.username
                session["role"] = utilisateur.role

                # Historique (optionnel)
                # enregistrer_action("Connexion au système")

                flash(
                    f"Bienvenue {utilisateur.username} ({utilisateur.role})",
                    "success"
                )

                return redirect(url_for("dashboard"))

            else:
                print("Mot de passe incorrect.")

        else:
            print("Utilisateur introuvable.")

        flash(
            "Nom d'utilisateur ou mot de passe incorrect.",
            "danger"
        )

    return render_template("login.html")

# =====================================
# DASHBOARD
# =====================================

@app.route("/dashboard")
def dashboard():

    # Vérifier si l'utilisateur est connecté
    if "user" not in session:
        return redirect(url_for("login"))

    # Statistiques
    total_eleves = Eleve.query.count()
    total_classes = Classe.query.count()
    total_paiements = Paiement.query.count()

    # Montant total des paiements
    montant_total = db.session.query(
        db.func.sum(Paiement.montant)
    ).scalar()

    if montant_total is None:
        montant_total = 0

    # Les 5 derniers paiements
    derniers_paiements = Paiement.query.order_by(
        Paiement.id.desc()
    ).limit(5).all()

    return render_template(
        "dashboard.html",
        total_eleves=total_eleves,
        total_classes=total_classes,
        total_paiements=total_paiements,
        montant_total=montant_total,
        derniers_paiements=derniers_paiements,
        utilisateur=session.get("user"),
        role=session.get("role")
    )
# =====================================
# DECONNEXION
# =====================================

@app.route("/logout")
def logout():

    if "user" in session:

        # Historique (à activer plus tard)
        # enregistrer_action("Déconnexion")

        session.clear()

        flash(
            "Vous avez été déconnecté avec succès.",
            "success"
        )

    return redirect(url_for("login"))

# =====================================
# GESTION DES ELEVES
# =====================================

@app.route("/eleves", methods=["GET", "POST"])
def eleves():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        matricule = request.form["matricule"].strip()
        nom = request.form["nom"].strip()
        postnom = request.form["postnom"].strip()
        prenom = request.form["prenom"].strip()
        sexe = request.form["sexe"]
        classe_id = request.form["classe_id"]

        # Vérifier les champs obligatoires
        if not matricule or not nom or not postnom or not prenom:
            flash("Tous les champs sont obligatoires.", "warning")
            return redirect(url_for("eleves"))

        # Vérifier le matricule
        existe = Eleve.query.filter_by(
            matricule=matricule
        ).first()

        if existe:
            flash("Ce matricule existe déjà.", "danger")
            return redirect(url_for("eleves"))

        eleve = Eleve(
            matricule=matricule,
            nom=nom,
            postnom=postnom,
            prenom=prenom,
            sexe=sexe,
            classe_id=classe_id
        )

        db.session.add(eleve)
        db.session.commit()

        flash("Élève ajouté avec succès.", "success")

        return redirect(url_for("eleves"))

    # Recherche
    recherche = request.args.get("recherche", "").strip()

    if recherche:
        liste = Eleve.query.filter(
            (Eleve.matricule.contains(recherche)) |
            (Eleve.nom.contains(recherche)) |
            (Eleve.postnom.contains(recherche)) |
            (Eleve.prenom.contains(recherche))
        ).order_by(Eleve.nom.asc()).all()
    else:
        liste = Eleve.query.order_by(
            Eleve.nom.asc()
        ).all()

    liste_classes = Classe.query.order_by(
        Classe.nom.asc()
    ).all()

    return render_template(
        "eleves.html",
        eleves=liste,
        classes=liste_classes
    )


# =====================================
# MODIFIER ELEVE
# =====================================

@app.route("/modifier_eleve/<int:id>", methods=["GET", "POST"])
def modifier_eleve(id):

    if "user" not in session:
        return redirect(url_for("login"))

    eleve = Eleve.query.get_or_404(id)

    if request.method == "POST":

        matricule = request.form["matricule"].strip()
        nom = request.form["nom"].strip()
        postnom = request.form["postnom"].strip()
        prenom = request.form["prenom"].strip()
        sexe = request.form["sexe"]
        classe_id = request.form["classe_id"]

        if not matricule or not nom or not postnom or not prenom:
            flash("Tous les champs sont obligatoires.", "warning")
            return redirect(url_for("modifier_eleve", id=id))

        existe = Eleve.query.filter(
            Eleve.matricule == matricule,
            Eleve.id != id
        ).first()

        if existe:
            flash("Ce matricule est déjà utilisé.", "danger")
            return redirect(url_for("modifier_eleve", id=id))

        eleve.matricule = matricule
        eleve.nom = nom
        eleve.postnom = postnom
        eleve.prenom = prenom
        eleve.sexe = sexe
        eleve.classe_id = classe_id

        db.session.commit()

        flash("Élève modifié avec succès.", "success")

        return redirect(url_for("eleves"))

    classes = Classe.query.order_by(
        Classe.nom.asc()
    ).all()

    return render_template(
        "modifier_eleve.html",
        eleve=eleve,
        classes=classes
    )


# =====================================
# SUPPRIMER ELEVE
# =====================================

@app.route("/supprimer_eleve/<int:id>")
def supprimer_eleve(id):

    if "user" not in session:
        return redirect(url_for("login"))

    eleve = Eleve.query.get_or_404(id)

    # Vérifier si l'élève possède des paiements
    paiement = Paiement.query.filter_by(
        eleve_id=id
    ).first()

    if paiement:
        flash(
            "Impossible de supprimer cet élève car il possède déjà des paiements.",
            "warning"
        )
        return redirect(url_for("eleves"))

    db.session.delete(eleve)
    db.session.commit()

    flash("Élève supprimé avec succès.", "success")

    return redirect(url_for("eleves"))


# =====================================
# IMPRESSION DES ELEVES
# =====================================

@app.route("/imprimer_eleves")
def imprimer_eleves():

    if "user" not in session:
        return redirect(url_for("login"))

    eleves = Eleve.query.order_by(
        Eleve.nom.asc()
).all()

    dossier = "static/rapports"
    os.makedirs(dossier, exist_ok=True)

    chemin_pdf = os.path.join(dossier, "liste_eleves.pdf")

    doc = SimpleDocTemplate(chemin_pdf)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph("<b>SCHOOLPAY PRO</b>", styles["Title"])
    )

    elements.append(
        Paragraph(
    f"Liste des élèves ({len(eleves)})",
    styles["Heading2"]
)
    )

    elements.append(Spacer(1, 20))

    data = [[
        "N°",
        "Matricule",
        "Nom",
        "Postnom",
        "Prénom",
        "Sexe",
        "Classe"
    ]]

    for i, e in enumerate(eleves, start=1):

        data.append([
            str(i),
            e.matricule,
            e.nom,
            e.postnom,
            e.prenom,
            e.sexe,
            e.classe.nom if e.classe else "-"
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,-1), colors.beige),
    ]))

    elements.append(table)

    doc.build(elements)

    return send_file(
        chemin_pdf,
        as_attachment=False
    )

# =====================================
# GESTION DES CLASSES
# =====================================

@app.route("/classes", methods=["GET", "POST"])
def classes():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        nom = request.form["nom"].strip()

        if not nom:
            flash("Le nom de la classe est obligatoire.", "warning")
            return redirect(url_for("classes"))

        existe = Classe.query.filter_by(
            nom=nom
        ).first()

        if existe:
            flash("Cette classe existe déjà.", "danger")
            return redirect(url_for("classes"))

        classe = Classe(nom=nom)

        db.session.add(classe)
        db.session.commit()

        flash("Classe ajoutée avec succès.", "success")

        return redirect(url_for("classes"))

    recherche = request.args.get("recherche", "").strip()

    if recherche:
        liste = Classe.query.filter(
            Classe.nom.contains(recherche)
        ).order_by(Classe.nom.asc()).all()
    else:
        liste = Classe.query.order_by(
            Classe.nom.asc()
        ).all()

    return render_template(
        "classes.html",
        classes=liste
    )

# =====================================
# MODIFIER CLASSE
# =====================================

@app.route("/modifier_classe/<int:id>", methods=["GET", "POST"])
def modifier_classe(id):

    if "user" not in session:
        return redirect(url_for("login"))

    classe = Classe.query.get_or_404(id)

    if request.method == "POST":

        nom = request.form["nom"].strip()

        if not nom:
            flash("Le nom de la classe est obligatoire.", "warning")
            return redirect(url_for("modifier_classe", id=id))

        existe = Classe.query.filter(
            Classe.nom == nom,
            Classe.id != id
        ).first()

        if existe:
            flash("Cette classe existe déjà.", "danger")
            return redirect(url_for("modifier_classe", id=id))

        classe.nom = nom

        db.session.commit()

        flash("Classe modifiée avec succès.", "success")

        return redirect(url_for("classes"))

    return render_template(
        "modifier_classe.html",
        classe=classe
    )

# =====================================
# SUPPRIMER CLASSE
# =====================================

@app.route("/supprimer_classe/<int:id>")
def supprimer_classe(id):

    if "user" not in session:
        return redirect(url_for("login"))

    classe = Classe.query.get_or_404(id)

    nb_eleves = Eleve.query.filter_by(
        classe_id=id
    ).count()

    if nb_eleves > 0:

        flash(
            f"Impossible de supprimer cette classe. Elle contient encore {nb_eleves} élève(s).",
            "warning"
        )

        return redirect(url_for("classes"))

    db.session.delete(classe)
    db.session.commit()

    flash("Classe supprimée avec succès.", "success")

    return redirect(url_for("classes"))



# =====================================
# GESTION DES PAIEMENTS
# =====================================

@app.route("/paiements", methods=["GET", "POST"])
def paiements():

    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        eleve_id = request.form["eleve_id"]
        motif = request.form["motif"].strip()

        try:
            montant = float(request.form["montant"])
        except ValueError:
            flash("Montant invalide.", "danger")
            return redirect(url_for("paiements"))

        if montant <= 0:
            flash("Le montant doit être supérieur à zéro.", "warning")
            return redirect(url_for("paiements"))

        paiement = Paiement(
            eleve_id=eleve_id,
            montant=montant,
            motif=motif
        )

        db.session.add(paiement)
        db.session.commit()

        flash("Paiement enregistré avec succès.", "success")

        return redirect(url_for("paiements"))

    recherche = request.args.get("recherche", "").strip()

    if recherche:
        liste_paiements = Paiement.query.join(Eleve).filter(
            (Eleve.matricule.contains(recherche)) |
            (Eleve.nom.contains(recherche)) |
            (Eleve.postnom.contains(recherche)) |
            (Eleve.prenom.contains(recherche)) |
            (Paiement.motif.contains(recherche))
        ).order_by(Paiement.id.desc()).all()
    else:
        liste_paiements = Paiement.query.order_by(
            Paiement.id.desc()
        ).all()

    liste_eleves = Eleve.query.order_by(
        Eleve.nom.asc()
    ).all()

    total_paiements = Paiement.query.count()

    montant_total = db.session.query(
        db.func.sum(Paiement.montant)
    ).scalar()

    if montant_total is None:
        montant_total = 0

    return render_template(
        "paiements.html",
        paiements=liste_paiements,
        eleves=liste_eleves,
        total_paiements=total_paiements,
        montant_total=montant_total
    )



# =====================================
# SUPPRIMER PAIEMENT
# =====================================

@app.route("/supprimer_paiement/<int:id>")
def supprimer_paiement(id):

    if "user" not in session:
        return redirect(url_for("login"))

    paiement = Paiement.query.get_or_404(id)

    db.session.delete(paiement)
    db.session.commit()

    flash(
        "Paiement supprimé avec succès.",
        "success"
    )

    return redirect(url_for("paiements"))



# =====================================
# MODIFIER PAIEMENT
# =====================================

@app.route("/modifier_paiement/<int:id>", methods=["GET", "POST"])
def modifier_paiement(id):

    if "user" not in session:
        return redirect(url_for("login"))

    paiement = Paiement.query.get_or_404(id)

    if request.method == "POST":

        try:
            montant = float(request.form["montant"])
        except ValueError:
            flash("Montant invalide.", "danger")
            return redirect(url_for("modifier_paiement", id=id))

        if montant <= 0:
            flash("Le montant doit être supérieur à zéro.", "warning")
            return redirect(url_for("modifier_paiement", id=id))

        paiement.eleve_id = int(request.form["eleve_id"])
        paiement.montant = montant
        paiement.motif = request.form["motif"].strip()

        db.session.commit()

        flash("Paiement modifié avec succès.", "success")

        return redirect(url_for("paiements"))

    eleves = Eleve.query.order_by(
        Eleve.nom.asc()
    ).all()

    return render_template(
        "modifier_paiement.html",
        paiement=paiement,
        eleves=eleves
    )


# =====================================
# RECU PDF
# =====================================

@app.route("/recu/<int:id>")
def recu(id):

    if "user" not in session:
        return redirect(url_for("login"))

    paiement = Paiement.query.get_or_404(id)

    dossier = "static/recus"
    os.makedirs(dossier, exist_ok=True)

    fichier = os.path.join(dossier, f"recu_{id}.pdf")

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(fichier)

    elements = []

    elements.append(Paragraph("<b>SCHOOLPAY PRO</b>", styles["Title"]))
    elements.append(Paragraph("Reçu de paiement", styles["Heading2"]))
    elements.append(Spacer(1, 15))

    data = [
        ["Élève", f"{paiement.eleve.nom} {paiement.eleve.postnom}"],
        ["Montant", f"{paiement.montant} $"],
        ["Motif", paiement.motif],
        ["Date", paiement.date_paiement.strftime("%d/%m/%Y")]
    ]

    table = Table(data, colWidths=[5 * cm, 10 * cm])

    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (0,-1), colors.lightgrey),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8)
    ]))

    elements.append(table)

    doc.build(elements)

    return send_file(fichier, as_attachment=True)


# =====================================
# EXPORT EXCEL
# =====================================

@app.route("/export_excel")
def export_excel():

    if "user" not in session:
        return redirect(url_for("login"))

    wb = Workbook()
    ws = wb.active
    ws.title = "Paiements"

    ws.append([
        "ID",
        "Matricule",
        "Nom",
        "Postnom",
        "Montant",
        "Motif",
        "Date"
    ])

    for p in Paiement.query.all():

        ws.append([
            p.id,
            p.eleve.matricule,
            p.eleve.nom,
            p.eleve.postnom,
            p.montant,
            p.motif,
            p.date_paiement.strftime("%d/%m/%Y")
        ])

    dossier = "static/export"
    os.makedirs(dossier, exist_ok=True)

    fichier = os.path.join(dossier, "paiements.xlsx")

    wb.save(fichier)

    return send_file(fichier, as_attachment=True)


# =====================================
# RAPPORT PDF
# =====================================

@app.route("/rapport_paiements")
def rapport_paiements():

    if "user" not in session:
        return redirect(url_for("login"))

    dossier = "static/rapports"
    os.makedirs(dossier, exist_ok=True)

    fichier = os.path.join(dossier, "rapport_paiements.pdf")

    doc = SimpleDocTemplate(fichier)

    data = [["ID", "Élève", "Montant", "Motif", "Date"]]

    for p in Paiement.query.all():

        data.append([
            p.id,
            f"{p.eleve.nom} {p.eleve.postnom}",
            f"{p.montant} $",
            p.motif,
            p.date_paiement.strftime("%d/%m/%Y")
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.blue),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("ALIGN",(0,0),(-1,-1),"CENTER")
    ]))

    doc.build([table])

    return send_file(fichier, as_attachment=True)

# =====================================
# GESTION DES UTILISATEURS
# =====================================

@app.route("/utilisateurs", methods=["GET", "POST"])
def utilisateurs():

    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Administrateur":
        flash("Accès refusé.", "danger")
        return redirect(url_for("dashboard"))

    # Ajout d'un utilisateur
    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]
        role = request.form["role"]

        if not username or not password:
            flash("Tous les champs sont obligatoires.", "warning")
            return redirect(url_for("utilisateurs"))

        existe = Utilisateur.query.filter_by(
            username=username
        ).first()

        if existe:
            flash("Ce nom d'utilisateur existe déjà.", "danger")
            return redirect(url_for("utilisateurs"))

        utilisateur = Utilisateur(
            username=username,
            password=generate_password_hash(password),
            role=role
        )

        db.session.add(utilisateur)
        db.session.commit()

        flash("Utilisateur ajouté avec succès.", "success")
        return redirect(url_for("utilisateurs"))

    # Recherche
    recherche = request.args.get("recherche", "").strip()

    if recherche:
        liste = Utilisateur.query.filter(
            Utilisateur.username.contains(recherche)
        ).all()
    else:
        liste = Utilisateur.query.order_by(
            Utilisateur.username.asc()
        ).all()

    return render_template(
        "utilisateurs.html",
        utilisateurs=liste
    )


# =====================================
# SUPPRIMER UTILISATEUR
# =====================================

@app.route("/supprimer_utilisateur/<int:id>")
def supprimer_utilisateur(id):

    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Administrateur":
        flash("Accès refusé.", "danger")
        return redirect(url_for("dashboard"))

    utilisateur = Utilisateur.query.get_or_404(id)

    if utilisateur.username == session.get("user"):
        flash(
            "Vous ne pouvez pas supprimer votre propre compte.",
            "warning"
        )
        return redirect(url_for("utilisateurs"))

    db.session.delete(utilisateur)
    db.session.commit()

    flash("Utilisateur supprimé avec succès.", "success")

    return redirect(url_for("utilisateurs"))


# =====================================
# MODIFIER UTILISATEUR
# =====================================

@app.route("/modifier_utilisateur/<int:id>", methods=["GET", "POST"])
def modifier_utilisateur(id):

    if "user" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Administrateur":
        flash("Accès refusé.", "danger")
        return redirect(url_for("dashboard"))

    utilisateur = Utilisateur.query.get_or_404(id)

    if request.method == "POST":

        username = request.form["username"].strip()
        role = request.form["role"]
        password = request.form["password"].strip()

        autre = Utilisateur.query.filter(
            Utilisateur.username == username,
            Utilisateur.id != id
        ).first()

        if autre:
            flash("Ce nom d'utilisateur est déjà utilisé.", "danger")
            return redirect(url_for("modifier_utilisateur", id=id))

        utilisateur.username = username
        utilisateur.role = role

        if password:
            utilisateur.password = generate_password_hash(password)

        db.session.commit()

        flash("Utilisateur modifié avec succès.", "success")
        return redirect(url_for("utilisateurs"))

    return render_template(
        "modifier_utilisateur.html",
        utilisateur=utilisateur
    )


# =====================================
# SAUVEGARDE MYSQL
# =====================================

@app.route("/backup")
def backup():

    if "user" not in session:
        return redirect(url_for("login"))

    dossier = "backup"
    os.makedirs(dossier, exist_ok=True)

    date = datetime.now().strftime("%Y%m%d_%H%M%S")

    fichier = os.path.join(
        dossier,
        f"schoolpay_{date}.sql"
    )

    commande = [
        "C:\\xampp\\mysql\\bin\\mysqldump.exe",
        "-u",
        "root",
        "schoolpay"
    ]

    with open(fichier, "w", encoding="utf-8") as sortie:

        subprocess.run(
            commande,
            stdout=sortie
        )

    return send_file(
        fichier,
        as_attachment=True
    )


# =====================================
# PARAMETRES
# =====================================

@app.route("/parametres", methods=["GET", "POST"])
def parametres():

    if "user" not in session:
        return redirect(url_for("login"))

    param = Parametre.query.first()

    if param is None:

        param = Parametre()

        db.session.add(param)
        db.session.commit()

    if request.method == "POST":

        param.nom_ecole = request.form["nom_ecole"]
        param.adresse = request.form["adresse"]
        param.telephone = request.form["telephone"]
        param.email = request.form["email"]
        param.devise = request.form["devise"]

        db.session.commit()

        flash("Paramètres enregistrés.", "success")

        return redirect(url_for("parametres"))

    return render_template(
        "parametres.html",
        param=param
    )


# =====================================
# A PROPOS
# =====================================

@app.route("/apropos")
def apropos():

    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("apropos.html")


# =====================================
# LANCEMENT DE L'APPLICATION
# =====================================

@app.route("/sauvegarde")
def sauvegarde():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("sauvegarde.html")

# =====================================
# VERIFICATION DU ROLE ADMINISTRATEUR
# =====================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):

        if "user" not in session:
            flash("Veuillez vous connecter.", "warning")
            return redirect(url_for("login"))

        if session.get("role") != "Administrateur":
            flash("Accès refusé. Réservé à l'administrateur.", "danger")
            return redirect(url_for("dashboard"))

        return f(*args, **kwargs)

    return decorated_function




print(app.url_map)

if __name__ == "__main__":

    app.run(
        debug=True
    )

    
