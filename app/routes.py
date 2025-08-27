<<<<<<< HEAD
# -*- coding: utf-8 -*-
import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from .models import db, Student, Session, ProgrammeSelection  # Import des modèles
from datetime import datetime
import psycopg2 # Nouvelle importation

app_routes = Blueprint('app_routes', __name__)

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)

# --- NOUVEL ENDPOINT POUR LE PING DE LA BASE DE DONNÉES ---
@app_routes.route('/ping')
def ping_database():
    """Endpoint pour vérifier la connexion à la base de données."""
    try:
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if not DATABASE_URL:
            # Gérer le cas où la variable d'environnement n'est pas définie
            return jsonify({"error": "DATABASE_URL non définie"}), 500
        
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.close()
        conn.close()
        return jsonify({"message": "Database ping successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- ROUTES EXISTANTES ---

@app_routes.route('/')
def home():
    return redirect(url_for('app_routes.students'))

# --- MODIFIÉ POUR L'ARCHIVAGE ---
@app_routes.route('/students', methods=['GET', 'POST'])
def students():
    if request.method == 'POST':
        name = request.form.get('name', "").strip()
        if not name:
            flash("Le nom de l'élève est obligatoire.", "error")
            return redirect(url_for('app_routes.students'))

        new_student = Student(name=name)
        try:
            db.session.add(new_student)
            db.session.commit()
            flash("Élève ajouté avec succès.", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'ajout de l'élève : {str(e)}", "error")

        return redirect(url_for('app_routes.students'))

    # ✅ MODIFICATION : Ne montrer que les élèves non-archivés
    students = Student.query.filter_by(is_archived=False).order_by(Student.name).all()

    for student in students:
        student.unrecorded_count = Session.query.filter_by(student_id=student.id, selected=False).count()
        student.recorded_count = Session.query.filter_by(student_id=student.id, selected=True).count()
    students = Student.query.filter_by(is_archived=False).order_by(Student.created_at.asc()).all()    
    return render_template('students.html', students=students)


# --- NOUVELLE LOGIQUE D'ARCHIVAGE CI-DESSOUS ---

@app_routes.route('/archived_students')
def archived_students():
    """Affiche la liste des élèves archivés."""
    archived = Student.query.filter_by(is_archived=True).order_by(Student.name).all()
    return render_template('archived_students.html', archived_students=archived)


@app_routes.route('/archive_student/<int:student_id>', methods=['POST'])
def archive_student(student_id):
    """Marque un élève comme archivé."""
    student = db.session.get(Student, student_id)
    if student:
        try:
            student.is_archived = True
            db.session.commit()
            flash(f"L'élève '{student.name}' a été archivé.", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'archivage : {str(e)}", "error")
    else:
        flash("Élève introuvable.", "error")
    return redirect(url_for('app_routes.remarks', student_id=student_id))


@app_routes.route('/unarchive_student/<int:student_id>', methods=['POST'])
def unarchive_student(student_id):
    """Restaure un élève depuis les archives."""
    student = db.session.get(Student, student_id)
    if student:
        try:
            student.is_archived = False
            db.session.commit()
            flash(f"L'élève '{student.name}' a été restauré.", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de la restauration : {str(e)}", "error")
    else:
        flash("Élève introuvable.", "error")
    return redirect(url_for('app_routes.archived_students'))


# --- LE RESTE DE VOS ROUTES NE CHANGE PAS ---

@app_routes.route('/remarks/<int:student_id>', methods=['GET', 'POST'])
def remarks(student_id):
    # J'utilise db.session.get qui est la méthode moderne pour récupérer par clé primaire
    student = db.session.get(Student, student_id) 

    if not student:
        logging.error(f"Élève ID {student_id} introuvable.")
        flash("Élève introuvable.", "error")
        return redirect(url_for('app_routes.students'))

    if request.method == 'POST':
        remark = request.form.get('remark', "").strip()
        if remark:
            new_session = Session(student_id=student.id, remark=remark, selected=False)
            try:
                db.session.add(new_session)
                db.session.commit()
                flash("Séance ajoutée avec succès.", "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Erreur lors de l'ajout de la séance : {str(e)}", "error")
        else:
            flash("La remarque ne peut pas être vide.", "error")
        return redirect(url_for('app_routes.remarks', student_id=student.id))

    student_sessions = Session.query.filter_by(student_id=student_id).order_by(Session.selected.asc(), Session.id.desc()).all()

    for session in student_sessions:
        if isinstance(session.date, str):
            try:
                session.date = datetime.strptime(session.date, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                session.date = datetime.now().date() # Fallback
    
    selected_sessions = {s.id for s in student_sessions if s.selected}
    unrecorded_count = sum(1 for s in student_sessions if not s.selected)
    recorded_count = len(student_sessions) - unrecorded_count
    return render_template(
        "remarks.html",
        student_id=student.id,
        student_name=student.name,
        student_school=student.school_name or "",
        student_birth_date=student.birth_date or "",
        student_phone_number=student.phone_number or "",
        sessions=student_sessions,
        selected_sessions=selected_sessions,
        unrecorded_count=unrecorded_count,
        recorded_count=recorded_count,
    )


@app_routes.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if student:
        try:
            # La configuration 'cascade' dans le modèle s'occupe de supprimer les sessions et sélections
            db.session.delete(student)
            db.session.commit()
            flash("Élève et données associées supprimés définitivement.", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de la suppression de l'élève : {str(e)}", "error")

    return redirect(url_for('app_routes.students'))


@app_routes.route('/programme_maths/<int:student_id>')
def programme_maths(student_id):
    programme = {
        "1. Limites et Continuité": ["Continuité en un point- continuité à droite - continuité à gauche", "Continuité sur un intervalle", "Image d’un intervalle", "Théorème des valeurs intermédiaires (T.V.I) et dichotomie", "Fonction réciproque", "Racine N-ième"],
        "2. Dérivabilité et Étude des Fonctions": ["Dérivabilité en un point", "Interprétation géométrique du nombre dérivé", "Dérivabilité sur un intervalle", "Calcul de la dérivée", "Dérivée et variations", "Extremums d’une fonction", "Concavité et dérivée seconde", "Les branches infinies", "Axe de symétrie - Centre de symétrie- Fonction paire – impaire", "Position relative d’une courbe et d’une droite"],
        "3. Fonctions Primitives": ["Les primitives", "Intégrale", "Intégration par parties", "Application – Aire et Volume"],
        "4. Fonction Logarithme": ["Définition et propriétés (Df et Equation/Inéquation)", "Limites usuelles", "La dérivée", "Logarithmes de base a"],
        "5. Fonction Exponentielle": ["Définition et propriétés (Df et Equation/Inéquation)", "Limites usuelles", "La dérivée", "Exponentielle de base a"],
        "6. Suites Numériques": ["Monotonie d’une suite numérique", "Suite majorée – Suite minorée – Suite bornée (Récurrence)", "Suite arithmétique", "Suite géométrique", "Limite d’une suite numérique (Convergence)"],
        "7. Nombres Complexes": ["Notion et propriétés", "Représentation géométrique", "Equations du second degré", "Forme trigonométrique", "Interprétation géométrique (Alignement, type du triangle, points circulaires)", "Notation exponentielle", "Transformations (Translation-Homothétie-Rotation)"],
        "8. Géométrie dans l’espace": ["Produit scalaire et propriétés", "Equation d’une droite et distance", "Equation cartésienne d’une sphère", "Produit vectoriel", "Positions relatives d’une droite et d’une sphère"],
        "9. Équations Différentielles": ["Equation Différentielle Linéaire du 1er ordre", "Equation Différentielle Linéaire du 2nd ordre"],
        "10. Probabilités et Statistiques": ["Introduction Cardinal - principe fondamental de dénombrement - Types de tirages", "Probabilité d’un événement - Probabilité conditionnelle", "Variables aléatoires - Loi Binomiale"]
    }

    selected_chapters = {selection.chapter_name for selection in ProgrammeSelection.query.filter_by(student_id=student_id).all()}

    return render_template('programme.html', programme=programme, student_id=student_id, selected_chapters=selected_chapters)


@app_routes.route('/save_programme_selections', methods=['POST'])
def save_programme_selections():
    if not request.is_json:
        return jsonify({"error": "Le Content-Type doit être application/json"}), 415

    data = request.get_json()
    student_id = data.get('student_id')
    selected_chapters = data.get('selections', [])

    if not student_id:
        return jsonify({"error": "L'ID de l'élève est requis"}), 400

    try:
        ProgrammeSelection.query.filter_by(student_id=student_id).delete()
        if selected_chapters:
            for chapter in selected_chapters:
                new_selection = ProgrammeSelection(student_id=student_id, chapter_name=chapter)
                db.session.add(new_selection)
        db.session.commit()
        return jsonify({"message": "Sélections enregistrées avec succès!"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Erreur lors de la sauvegarde : {str(e)}"}), 500


@app_routes.route('/edit_remark/<int:student_id>/<int:session_id>', methods=['POST'])
def edit_remark(student_id, session_id):
    session_to_edit = db.session.get(Session, session_id)
    if session_to_edit:
        new_remark = request.form.get('remark', "").strip()
        if new_remark:
            try:
                session_to_edit.remark = new_remark
                db.session.commit()
                flash("La remarque a été mise à jour avec succès.", "success")
            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Erreur lors de la modification de la remarque : {str(e)}", "error")
        else:
            flash("La remarque ne peut pas être vide.", "error")
    else:
        flash("Séance introuvable.", "error")
    return redirect(url_for('app_routes.remarks', student_id=student_id))
=======
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file

import json
from .utils import load_data, add_student, add_session, remove_session, remove_student, save_data

app_routes = Blueprint('app_routes', __name__)


@app_routes.route('/students', methods=['GET', 'POST'])
def students():
    if request.method == 'POST':
        name = request.form['name']

        # Charger les données actuelles
        data = load_data()

        # Trouver le plus grand ID existant parmi les étudiants
        existing_ids = [student['id'] for student in data.get("students", [])]
        new_id = max(existing_ids) + 1 if existing_ids else 1  # ID suivant disponible

        # Ajouter un nouvel étudiant avec un ID unique
        add_student(name, new_id)

        return redirect(url_for('app_routes.students'))

    data = load_data()
    students = data["students"]
    return render_template('students.html', students=students)



@app_routes.route('/remarks/<int:student_id>', methods=['GET', 'POST'])
def remarks(student_id):
    data = load_data()

    if request.method == 'POST':
        remark = request.form.get('remark', "")
        add_session(remark, student_id)
        flash("Séance ajoutée avec ou sans remarque.", "success")
        return redirect(url_for('app_routes.remarks', student_id=student_id))

    # Trouver l'élève correspondant
    student = next((s for s in data["students"] if s["id"] == student_id), None)
    if student is None:
        flash("Élève introuvable.", "error")
        return redirect(url_for('app_routes.students'))

    # Filtrer les séances de cet élève
    student_sessions = [session for session in data["sessions"] if session["student_id"] == student_id]

    # Récupérer les sessions sélectionnées depuis Flask session
    selected_sessions = set(session.get(f'selected_sessions_{student_id}', []))  # Utilisation correcte de session

    # Compter les séances non cochées (celles qui ne sont pas dans selected_sessions)
    unrecorded_count = sum(1 for s in student_sessions if s["id"] not in selected_sessions)

    return render_template(
        "remarks.html",
        student_id=student_id,
        student_name=student["name"],
        student_school=student.get("school_name", ""),
        student_birth_date=student.get("birth_date", ""),
        student_phone_number=student.get("phone_number", ""),
        sessions=student_sessions,
        selected_sessions=selected_sessions,
        unrecorded_count=unrecorded_count,  # Nombre de séances non cochées
    )



>>>>>>> 113f45e4c4adce49a832eacd2d33dc61e112a042


@app_routes.route('/update_info/<int:student_id>', methods=['POST'])
def update_info(student_id):
<<<<<<< HEAD
    student = db.session.get(Student, student_id)
    if not student:
        flash("Élève introuvable.", "error")
        return redirect(url_for('app_routes.students'))

    student.school_name = request.form.get('school_name', '').strip()
    student.birth_date = request.form.get('birth_date', '').strip()
    student.phone_number = request.form.get('phone_number', '').strip()

    try:
        db.session.commit()
        flash("Informations mises à jour avec succès.", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur lors de la mise à jour : {str(e)}", "error")
    return redirect(url_for('app_routes.remarks', student_id=student_id))


@app_routes.route('/delete_remark/<int:student_id>/<int:session_id>', methods=['POST'])
def delete_remark(student_id, session_id):
    session_to_delete = db.session.get(Session, session_id)
    if session_to_delete:
        try:
            db.session.delete(session_to_delete)
            db.session.commit()
            flash("Séance supprimée avec succès.", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de la suppression : {str(e)}", "error")
    else:
        flash("Séance introuvable.", "error")
=======
    data = load_data()

    # Mettre à jour les informations de l'élève
    for student in data["students"]:
        if student["id"] == student_id:
            student["school_name"] = request.form['school_name']
            student["birth_date"] = request.form['birth_date']
            student["phone_number"] = request.form['phone_number']  # Ajout
            break

    save_data(data)
    flash("Les informations de l'élève ont été mises à jour avec succès.", "success")
>>>>>>> 113f45e4c4adce49a832eacd2d33dc61e112a042
    return redirect(url_for('app_routes.remarks', student_id=student_id))


@app_routes.route('/save_selection/<int:student_id>', methods=['POST'])
def save_selection(student_id):
<<<<<<< HEAD
    selected_sessions = request.form.getlist('selected_sessions')
    try:
        Session.query.filter(Session.student_id == student_id).update({"selected": False})
        if selected_sessions:
            Session.query.filter(Session.id.in_(selected_sessions)).update({"selected": True}, synchronize_session=False)
        db.session.commit()
        return jsonify({"message": "Sélection mise à jour avec succès"}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
=======
    try:
        selected_sessions = request.form.getlist('selected_sessions')
        selected_sessions = list(map(int, selected_sessions))
        
        session[f'selected_sessions_{student_id}'] = selected_sessions
        session.modified = True  # Assure la sauvegarde dans Flask
        
        flash("Les sélections ont été sauvegardées avec succès !", "success")
        return '', 200
    except Exception as e:
        print(f"Erreur lors de la sauvegarde : {e}")
        return "Une erreur s'est produite lors de la sauvegarde.", 500



@app_routes.route('/delete_remark/<int:student_id>/<int:session_id>', methods=['POST'])
def delete_remark(student_id, session_id):
    remove_session(session_id)
    flash("Remarque supprimée avec succès.", "success")
    return redirect(url_for('app_routes.remarks', student_id=student_id))


from flask import jsonify

@app_routes.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    # Charger les données depuis le fichier JSON
    data = load_data()

    # Supprimer l'élève correspondant
    data["students"] = [student for student in data.get("students", []) if student["id"] != student_id]

    # Supprimer les remarques associées à l'élève
    data["sessions"] = [session for session in data.get("sessions", []) if session["student_id"] != student_id]

    # Supprimer les sauvegardes de sélection associées à l'élève
    session.pop(f'selected_sessions_{student_id}', None)

    # Ne pas réassigner les IDs des élèves, mais conserver les anciens IDs
    # Supprimer uniquement l'élève, sans affecter les autres IDs
    save_data(data)

    # Rediriger vers la page des étudiants
    flash("Élève et données associées supprimés avec succès.", "success")
    return redirect(url_for('app_routes.students'))

@app_routes.route('/edit_remark/<int:student_id>/<int:session_id>', methods=['POST'])
def edit_remark(student_id, session_id):
    data = load_data()

    # Trouver la session et la modifier
    session_to_edit = next((s for s in data["sessions"] if s["id"] == session_id and s["student_id"] == student_id), None)

    if session_to_edit:
        # Mettre à jour la remarque
        new_remark = request.form.get('remark')  # Utiliser get() pour éviter les KeyError
        if new_remark:
            session_to_edit["remark"] = new_remark
            save_data(data)
            flash("La remarque a été mise à jour avec succès.", "success")
        else:
            flash("La remarque ne peut pas être vide.", "error")

    # Rediriger vers la page des remarques de l'élève
    return redirect(url_for('app_routes.remarks', student_id=student_id))


@app_routes.route('/download_db')
def download_db():
    # Get the correct absolute path to data.json
    db_path = os.path.join(os.path.dirname(__file__), "data.json")
    
    # Ensure the file exists before sending
    if not os.path.exists(db_path):
        return "Database file not found", 404

    # Send the file for download
    return send_file(db_path, as_attachment=True)







>>>>>>> 113f45e4c4adce49a832eacd2d33dc61e112a042
