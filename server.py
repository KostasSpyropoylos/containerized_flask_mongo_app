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
            session["username"] = str(doctor["first_name"] + " " + doctor["last_name"])
            session["accessLevel"] = "doctor"
            session["userID"] = str(doctor["_id"])
            return redirect(url_for("home"))

        if patient:
            session["username"] = str(
                patient["first_name"] + " " + patient["last_name"]
            )
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


# Admin
@app.route("/admin_panel", methods=["GET", "POST"])
def admin_panel():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    doctors = list(getDoctors())
    if request.method == "POST":
        if "delete" in request.form:
            row_id = request.form["remove_row"]

            status = removeDoctorByUsername(str(row_id))

            return redirect(url_for("admin_panel"))
        
        # new_password = request.form["password"]
        # # Update the password for the logged-in user
        # if username and new_password:
        #     doctor_collection.update_one(
        #         {"username": username},
        #         {"$set": {"password": new_password}},
        #         upsert=True,
        #     )
        #     flash("Password updated Successfully!", "success")
        # else:
        #     flash("Password is required!", "danger")

    return render_template("admin_panel.html", username=username, len=len(doctors),doctors = doctors)

    # Redirect to login if not logged in


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

    id = session["userID"]

    appointment = {}
    appointment_data = {}
    doctor = {}
    # check it there are appointments for the user
    appointments = appointment_collection.find({"patient_id": id})
    lst = list(appointments)

    # Get the data and the status code
    response, status = getAllSpecializations()

    if status == 200:
        specializations = response.json
    else:
        specializations = []

    if request.method == "POST":
        if "book" in request.form:
            date = request.form["date"]
            specialization = request.form["specialization"]
            reason_of_visit = request.form["reason_of_visit"]
            time = request.form["time"]

            doctor = doctor_collection.find_one(
                {"specialization": specialization.lower()}
            )
            if doctor:
                status, apps = getAvailableDate(date, time, doctor["_id"])
                if status == 200:
                    # Insert the appointment data into the MongoDB collection
                    result = appointment_collection.insert_one(
                        {
                            "appointment_date": date,
                            "appointment_time": time,
                            "reason_of_visit": reason_of_visit,
                            "patient_id": str(session["userID"]),
                            "patient_name": session["username"],
                            "doctor_id": doctor["_id"],
                            "doctor_last_name": str(doctor["last_name"]),
                            "specialization": str(doctor["specialization"]),
                        }
                    )
                    return redirect(url_for("book_appointment"))
                else:
                    return jsonify({"message": "Appointment slot not available"}), 409

        elif "show_details" in request.form:
            row_id = request.form["row_id"]

            appointment_data = getAppointmentById(str(row_id))

            if appointment_data:
                doc_id = appointment_data["doctor_id"]
                doctor = getDoctorById(doc_id)
                appointment_data = jsonify(appointment_data)
                return redirect(url_for("book_appointment"))

        elif "cancel" in request.form:
            row_id = request.form["remove_row"]

            status = removeAppointmentById(str(row_id))

            return redirect(url_for("book_appointment"))

    return render_template(
        "appointments.html",
        username=session.get("username"),
        len=len(lst),
        lst=lst,
        appointment=appointment_data,
        doctor=jsonify(doctor),
        accessLevel=session.get("accessLevel"),
        specialization=specializations,
    )


def getAvailableDate(date, time, doc_id):
    available_apps = appointment_collection.find_one(
        {
            "$and": [
                {"appointment_time": time},
                {"appointment_date": date},
                {"doctor_id": doc_id},
            ]
        }
    )

    # if exists get status 400 and the appointment
    if available_apps:
        # available_apps["_id"] = str(available_apps["_id"])
        return 400, jsonify({"message": "Appointment slot not available"})

    # return ok and available appointments
    return 200, jsonify(available_apps)


# Helper methods
@app.route("/doctors/all", methods=["GET"])
def getDoctors():

    doctors = doctor_collection.find()
    # Convert the documents to a list of dictionaries
    doctor_list = []
    for doc in doctors:
        doc["_id"] = str(doc["_id"])  # Convert ObjectId to string
        doctor_list.append(doc)

    return doctor_list


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


@app.route("/doctor/<id>", methods=["GET"])
def getDoctorById(id):

    # Ανάκτηση των ραντεβού με το συγκεκριμένο doctor_id
    doctor = doctor_collection.find_one({"_id": ObjectId(id)})

    doctor["_id"] = str(doctor["_id"])  # Μετατροπή του ObjectId σε string
    if doctor:
        return doctor
    else:
        return jsonify({"message": "No doctor found with provided id"})

@app.route("/doctor/<username>", methods=["DELETE"])
def removeDoctorByUsername(username):
    doctor_collection.delete_one({"username": str(username)})
    if doctor_collection.find_one({"username": str(username)}):
        return ({"message": "didn't delete"}),500
    else:
        return ({"message": "deleted"}),200

# Returns list of doctors with certain specialization
@app.route("/doctors/<specialization>", methods=["GET"])
def getDoctorBySpecialization(specialization):
    doctors = doctor_collection.find_one({"specialization": specialization.lower()})
    doctors["_id"] = str(doctors["_id"])

    if doctors:
        return jsonify(doctors), 200
    else:
        return (
            jsonify({"message": "No doctor found with provided specialization"}),
            404,
        )


def removeAppointmentById(id):
    appointment_collection.delete_one({"_id": ObjectId(id)})
    if appointment_collection.find_one({"_id": ObjectId(id)}):
        return 500
    else:
        return 200


@app.route("/appointment/<id>", methods=["GET"])
def getAppointmentById(id):
    appointment = appointment_collection.find_one({"_id": ObjectId(id)})
    if appointment:
        appointment["_id"] = str(appointment["_id"])
        appointment["doctor_id"] = str(appointment["doctor_id"])
        return appointment
    else:
        return jsonify({"message": f"No appointment found with id `{id}`"})


@app.route("/appointments/all", methods=["GET"])
def getAppointments():

    reservation = appointment_collection.find()
    # Convert the documents to a list of dictionaries
    appointment_list = []
    for res in reservation:
        res["_id"] = str(res["_id"])
        res["doctor_id"] = str(res["doctor_id"])  # Convert ObjectId to string
        appointment_list.append(res)

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
