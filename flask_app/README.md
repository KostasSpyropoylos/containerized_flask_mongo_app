# Project Title
 ### Hospital App

## Περιεχόμενα

1. [Επιπλέον Παραδοχές που Επιλέξατε](#Επιπλέον-Παραδοχές-που-Επιλέξατε)
2. [Τεχνολογίες που Χρησιμοποιήθηκαν](#Τεχνολογίες-που-Χρησιμοποιήθηκαν)
3. [Περιγραφή των Αρχείων](#Περιγραφή-των-Αρχείων)
4. [Τρόπος Εκτέλεσης Συστήματος](#Τρόπος-Εκτέλεσης-Συστήματος)
5. [Τρόπος Χρήσης του Συστήματος](#Τρόπος-Χρήσης-του-Συστήματος)
6. [Αναφορές που χρησιμοποιήσατε](#Αναφορές-που-χρησιμοποιήσατε)

## Επιπλέον Παραδοχές που Επιλέξατε

- Interpollation: Έγινε χρήση σε διάφορα σημεία του κώδικα για αλλαγή περιεχομένου αναλόγως του ρόλου του χρήστη
- Μοναδικότητα Ειδικεύσεων: Οι ειδικεύσεις των ιατρών είναι μοναδικές και αποθηκεύονται με πεζούς χαρακτήρες

## Τεχνολογίες που Χρησιμοποιήθηκαν

- **Docker**: Για την εικονικοποίηση του περιβάλλοντος ανάπτυξης και παραγωγής
- **MongoDB**: Για τη βάση δεδομένων NoSQL
- **Flask**: Για την υλοποίηση του backend
- **HTML**: Για την υλοποίηση του frontend
- **Bootstrap**: Για το styling

## Περιγραφή των Αρχείων


- `docker-compose.yml`: Περιέχει τον ορισμό των υπηρεσιών για την Docker εφαρμογή
- `flask_app/`: Περιέχει τον κώδικα της εφαρμογής
    - `Dockerfile`: Περιέχει τις οδηγίες για την κατασκευή της εικόνας Docker
    - `server.py`: Το κύριο αρχείο εκκίνησης του backend
    - `templates`: Περιέχει τα html αρχεία για τα views
    - `requirements.txt`: Περιέχει όλα τα dependencies του project
- `data/`: Αποθήκευση των δεδομένων locally της MongoDB για αποφυγή απώλειας δεδομένων
- `mongo/`: Περιέχει τις συλλογές στις οποίες βασίστηκε η υλοποίηση του API

## Τρόπος Εκτέλεσης Συστήματος

1. Κλώνος του αποθετηρίου:
   ```sh
   git clone git@github.com:KostasSpyropoylos/dockerized-flask-mongodb-app.git
   ```
2. Εκκίνηση των υπηρεσιών μέσω Docker Compose:
   ```sh
   docker-compose up -d
   ```
3. Change Directory
    ```sh
    cd mongo
    ```
4. Αντιγραφή αρχείων JSON στο container του Docker
    ```sh
    docker cp doctors.json hospitaldb:/doctors.json && 
    docker cp patients.json hospitaldb:/patients.json && 
    docker cp reservations.json hospitaldb:/reservations.json
    ```
5. Εισαγωγή αρχείων JSON στις συλλογές της MongoDB
    ```sh
    docker exec -it hospitaldb mongoimport --db HospitalDB --collection doctors --file doctors.json --jsonArray && 
    docker exec -it hospitaldb mongoimport --db HospitalDB --collection patients --file patients.json --jsonArray && 
    docker exec -it hospitaldb mongoimport --db HospitalDB --collection reservations --file reservations.json --jsonArray
    ```


## Τρόπος Χρήσης του Συστήματος
1. Πρόσβαση στο frontend:
    - Ανοίξτε ένα πρόγραμμα περιήγησης και πηγαίνετε στη διεύθυνση `http://localhost:5000`
2. Χρήση του backend API:
    - Αποστολή αιτημάτων στο `http://localhost:5000/`
        - π.χ. `http://localhost:5000/doctors/all`
        - π.χ. `http://localhost:5000/patients/all`
        - π.χ. `http://localhost:5000/appointments/all`


## Αναφορές που χρησιμοποιήσατε
- [Flask Documentation](https://flask.palletsprojects.com/en/2.0.x/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Stack Overflow](https://stackoverflow.com/)
- [Python Official Documentation](https://docs.python.org/3/)
- Χρήση κώδικα από τα μαθήματα του εργαστηρίου 
- Αρκετό google


