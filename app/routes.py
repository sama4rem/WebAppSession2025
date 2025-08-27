# -*- coding: utf-8 -*-

import os
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from .models import db, Student, Session, ProgrammeSelection  # Import des modèles
from datetime import datetime
import psycopg2  # Nouvelle importation

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
    return redirect(url_for('app_routes.remarks', student_id=student_id))


@app_routes.route('/update_info/<int:student_id>', methods=['POST'])
def update_info(student_id):
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


@app_routes.route('/save_selection/<int:student_id>', methods=['POST'])
def save_selection(student_id):
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