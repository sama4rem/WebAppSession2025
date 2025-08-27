import json
import os
from datetime import datetime

# Use the project directory on Render (writable)
DATA_PATH = os.path.join(os.getcwd(), "data.json")

def load_data():
    """Load data from JSON or create an empty one if missing"""
    if not os.path.exists(DATA_PATH):  # Ensure the file exists
        print("📁 data.json not found, creating a new one...")
        save_data({"students": [], "sessions": [], "selected_sessions": {}})

    try:
        with open(DATA_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️ data.json was corrupted, resetting it.")
        save_data({"students": [], "sessions": [], "selected_sessions": {}})
        return {"students": [], "sessions": [], "selected_sessions": {}}

def save_data(data):
    """Save data to JSON file in a writable directory"""
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)


def add_student(name, new_id):
    data = load_data()

    # Créer un nouvel élève avec l'ID unique
    new_student = {
        "id": new_id,
        "name": name,
        "phone_number": "",
    }
    
    # Ajouter l'élève à la liste
    data["students"].append(new_student)
    
    # Sauvegarder les données mises à jour dans le fichier
    save_data(data)



def add_session(remark, student_id):
    """Ajouter une session avec une remarque pour un élève donné"""
    data = load_data()
    session_id = len(data["sessions"]) + 1
    date = datetime.now().strftime("%d.%m.%Y")
    data["sessions"].append({"id": session_id, "student_id": student_id, "remark": remark, "date": date})
    save_data(data)

def remove_session(session_id):
    """Supprimer une session par son ID"""
    data = load_data()
    data["sessions"] = [s for s in data["sessions"] if s["id"] != session_id]
    save_data(data)

def remove_student(student_id):
    """Supprime un élève et toutes ses remarques."""
    data = load_data()
    data["students"] = [s for s in data["students"] if s["id"] != student_id]
    data["sessions"] = [s for s in data["sessions"] if s["student_id"] != student_id]
    save_data(data)

def save_selected_sessions(student_id, selected_sessions):
    data = load_data()
    data["selected_sessions"][str(student_id)] = selected_sessions
    save_data(data)


