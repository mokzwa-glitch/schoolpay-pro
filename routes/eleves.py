# ==================================================
# GESTION DES ELEVES
# ==================================================

@app.route("/eleves", methods=["GET", "POST"])
@login_required
def eleves():

    if request.method == "POST":

        dernier = Eleve.query.order_by(Eleve.id.desc()).first()

        if dernier:
            numero = dernier.id + 1
        else:
            numero = 1

        matricule = f"ELV-{datetime.now().year}-{numero:05d}"

        nouvel_eleve = Eleve(
            matricule=matricule,
            nom=request.form["nom"],
            postnom=request.form["postnom"],
            prenom=request.form["prenom"],
            sexe=request.form["sexe"]
)

        # ==========================================
        # Création de l'élève
        # ==========================================

        nouvel_eleve = Eleve(

            matricule=matricule,

            nom=request.form.get("nom", "").strip(),

            postnom=request.form.get("postnom", "").strip(),

            prenom=request.form.get("prenom", "").strip(),

            sexe=request.form.get("sexe", "").strip()

        )

        db.session.add(nouvel_eleve)

        db.session.commit()

        # ==========================================
        # Historique
        # ==========================================

        enregistrer_action(
            f"Ajout de l'élève {nouvel_eleve.nom} {nouvel_eleve.postnom} ({matricule})"
        )

        flash(
            "Élève ajouté avec succès.",
            "success"
        )

        return redirect(url_for("eleves"))

    liste_eleves = Eleve.query.order_by(Eleve.id.desc()).all()

    return render_template(
        "eleves.html",
        eleves=liste_eleves
    )