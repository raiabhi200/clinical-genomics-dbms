from flask import Flask, render_template, request, redirect, url_for
from database.db_connection import get_db_connection

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/patients", methods=["GET", "POST"])
def patients():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if request.method == "POST":
        patient_code = request.form["patient_code"]
        age = request.form["age"]
        sex = request.form["sex"]
        diagnosis_id = request.form["diagnosis_id"]
        registration_date = request.form["registration_date"]

        cursor.execute(
            "INSERT INTO patients (patient_code, age, sex, diagnosis_id, registration_date) VALUES (%s, %s, %s, %s, %s)",
            (patient_code, age, sex, diagnosis_id, registration_date)
        )

        db.commit()

        cursor.close()
        db.close()

        return redirect(url_for("patients"))

    cursor.execute("SELECT diagnosis_id, disease_name FROM diagnoses ORDER BY disease_name")
    diagnoses = cursor.fetchall()

    cursor.execute("SELECT p.patient_id, p.patient_code, p.age, p.sex, d.disease_name, p.registration_date FROM patients p JOIN diagnoses d ON p.diagnosis_id = d.diagnosis_id ORDER BY p.patient_id")
    patients = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template("patients.html", diagnoses=diagnoses, patients=patients)


if __name__ == "__main__":
    app.run(debug=True)