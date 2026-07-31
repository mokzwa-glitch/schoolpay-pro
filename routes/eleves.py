@app.route("/eleves", methods=["GET", "POST"])
def eleves():

    if request.method == "POST":

        nouvel_eleve = Eleve(
            matricule=request.form["matricule"],
            nom=request.form["nom"],
            postnom=request.form["postnom"],
            prenom=request.form["prenom"],
            sexe=request.form["sexe"]
        )

        db.session.add(nouvel_eleve)
        db.session.commit()

        return redirect(url_for("eleves"))

    liste_eleves = Eleve.query.all()

    return render_template(
        "eleves.html",
        eleves=liste_eleves
    )