from datetime import datetime
import logging
from bson import ObjectId
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from pymongo import MongoClient

# Flask App Initialization
app = Flask(__name__)
app.secret_key = "a_random_key"  # Needed to use sessions

# MongoDB Client Initialization
client = MongoClient("localhost", 27017)  # Adjust the host and port if necessary
db = client["HospitalDB"]  # Database name
patient_collection = db["patients"]
doctor_collection = db["doctors"]
appointment_collection = db["reservations"]
# professors_collection = db["professors"]

""" Routes """


# Home Route to Home Template
@app.route("/")
def home():
    if "username" in session:
        username = session["username"]
        accessLevel = session["accessLevel"]
        return render_template("home.html", username=username, accessLevel=accessLevel)

    # Redirect to login if not logged in
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    # if "username" in session:
    #     username = session["username"]
    #     return render_template("home.html", username=username)
    error = None
    if request.method == "POST":
        firstName = request.form["firstName"]
        lastName = request.form["lastName"]
        email = request.form["email"]
        amka = request.form["amka"]
        birthDay = request.form["birthDay"]
        username = request.form["username"]
        password = request.form["password"]

        patient = {
            "first_name": firstName,
            "last_name": lastName,
            "email": email,
            "amka": amka,
            "date_of_birth": birthDay,
            "username": username,
            "password": password,
        }
        res, status = getPatientsByEmailAndUsername(email, username)
        if status == 200:

            flash("Patient already exists!", "success")
        elif status == 404:
            patient_collection.insert_one(patient)
            flash("Patient registered!", "success")
    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        username = session["username"]
        return render_template("home.html", username=username)
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["username"] = username
            session["accessLevel"] = "admin"
            return redirect(url_for("home"))

        # Fetch the doctor with the given username
        doctor = doctor_collection.find_one(
            {"$and": [{"username": username}, {"password": password}]}
        )

        patient = patient_collection.find_one(
            {"$and": [{"username": username}, {"password": password}]}
        )
        doctor_found = False

        if doctor:
            session["username"] = username
            session["accessLevel"] = "doctor"
            session["userID"] = str(doctor["_id"])
            return redirect(url_for("home"))

        if patient:
            session["username"] = username
            session["accessLevel"] = "patient"
            session["userID"] = str(patient["_id"])
            return redirect(url_for("home"))

        error = "Invalid Credentials"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    # Remove the username from the session if it's there
    session.pop("username", None)
    return redirect(url_for("login"))


# Doctor routing
@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    if request.method == "POST":
        new_password = request.form["password"]
        # Update the password for the logged-in user
        if username and new_password:
            doctor_collection.update_one(
                {"username": username},
                {"$set": {"password": new_password}},
                upsert=True,
            )
            flash("Password updated Successfully!", "success")
        else:
            flash("Password is required!", "danger")

    return render_template("change_password.html", username=username)

    # Redirect to login if not logged in


@app.route("/change_cost", methods=["GET", "POST"])
def change_cost():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    if request.method == "POST":
        pricing = request.form["pricing"]

        # Update the appointment_cost for the logged-in user
        if pricing and username:
            doctor_collection.update_one(
                {"username": username},
                {"$set": {"appointment_cost": int(pricing)}},
                upsert=True,
            )
            flash("Price Updated Successfully!", "success")
        else:
            flash("Price is required!", "danger")

    return render_template("change_cost.html", username=username)


@app.route("/show_appointments", methods=["GET", "POST"])
def appointments():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    id = session["userID"]

    # Update the appointment_cost for the logged-in user
    appointments = appointment_collection.find({"doctor_id": id})
    lst = list(appointments)
    return render_template(
        "appointments.html", username=username, len=len(lst), lst=lst
    )


# Patient routing
@app.route("/book_appointment", methods=["GET", "POST"])
def book_appointment():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    id = session["userID"]
    accessLevel = session["accessLevel"]

    # check it there are appointments for the user
    appointments = appointment_collection.find({"patient_id": id})
    lst = list(appointments)
    
    # Get the data and the status code
    response,status = getAllSpecializations()
    if(status == 200):
        specializations = response.json
    else:
        specializations = []
    if request.method == "POST":
        date = request.form["date"]
        specialization = request.form["specialization"]
        reason_of_visit = request.form["reason_of_visit"]
        time = request.form["time"]
        
        

     
    return render_template(
        "appointments.html",
        username=username,
        len=len(lst),
        lst=lst,
        accessLevel=accessLevel,
        specialization=specializations,
    )


# Helper methods
@app.route("/doctors/all", methods=["GET"])
def getDoctors():

    doctors = doctor_collection.find()
    # Convert the documents to a list of dictionaries
    doctor_list = []
    for doc in doctors:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        doctor_list.append(doc)

    return jsonify(doctor_list)


@app.route("/specializations", methods=["GET"])
def getAllSpecializations():
    # Ανάκτηση των ραντεβού με το συγκεκριμένο doctor_id
    doctors = doctor_collection.find()

    # Μετατροπή των εγγράφων σε λίστα από λεξικά
    specialization_list = []
    for doc in doctors:
        specialization_list.append(doc["specialization"])

    if len(specialization_list) > 0:
        # Get unique specialization values and turn in to json object
        specialization_list = list(set(specialization_list))
        return jsonify(specialization_list), 200
    else:
        return (
            jsonify({"message": "No doctor found with provided specialization"}),
            404,
        )


# Returns list of doctors with certain specialization
@app.route("/doctors/<specialization>", methods=["GET"])
def getDoctorsBySpecialization(specialization):

    # Ανάκτηση των ραντεβού με το συγκεκριμένο doctor_id
    doctors = doctor_collection.find({"specialization": specialization.lower()})

    # Μετατροπή των εγγράφων σε λίστα από λεξικά
    doctor_list = []
    for doc in doctors:
        doc["_id"] = str(doc["_id"])  # Μετατροπή του ObjectId σε string
        # Μετατροπή του ObjectId σε string αν υπάρχει και αυτό ως ObjectId
        doctor_list.append(doc)
    if len(doctor_list) > 0:
        return jsonify(doctor_list), 200
    else:
        return (
            jsonify({"message": "No doctor found with provided specialization"}),
            404,
        )


@app.route("/appointments/<id>", methods=["GET"])
def getAppointmentsById(id):
    try:
        # Ανάκτηση των ραντεβού με το συγκεκριμένο doctor_id
        appointments = appointment_collection.find({"doctor_id": id})

        # Μετατροπή των εγγράφων σε λίστα από λεξικά
        appointment_list = []
        for doc in appointments:
            doc["_id"] = str(doc["_id"])  # Μετατροπή του ObjectId σε string
            doc["doctor_id"] = str(
                doc["doctor_id"]
            )  # Μετατροπή του ObjectId σε string αν υπάρχει και αυτό ως ObjectId
            appointment_list.append(doc)

        return jsonify(appointment_list), 200

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 400


@app.route("/appointments/all", methods=["GET"])
def getAppointments():

    reservation = appointment_collection.find()
    # Convert the documents to a list of dictionaries
    appointment_list = []
    for doc in reservation:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        appointment_list.append(doc)

    return jsonify(appointment_list)


@app.route("/patients/all", methods=["GET"])
def getPatients():

    patients = patient_collection.find()
    # Convert the documents to a list of dictionaries
    patient_list = []
    for patient in patients:
        patient["_id"] = str(patient["_id"])  # Convert ObjectId to string
        patient_list.append(patient)

    return jsonify(patient_list)


@app.route("/getPatientByEmailAndUsername/", methods=["GET"])
def getPatientsByEmailAndUsername(email, username):

    patient = patient_collection.find_one(
        {"$or": [{"email": email}, {"username": username}]}
    )
    doctor = doctor_collection.find_one(
        {"$or": [{"email": email}, {"username": username}]}
    )

    if patient or doctor:
        patient["_id"] = str(patient["_id"])  # Convert ObjectId to string
        return jsonify(patient), 200
    else:
        return (
            jsonify({"message": "No patient found with provided email or username"}),
            404,
        )


# Run the Flask App
if __name__ == "__main__":
    app.run(debug=True, host="localhost", port=5000)
