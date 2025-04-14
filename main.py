#import dependencies
from flask import Flask, render_template,request, url_for, redirect,session,flash,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

app= Flask(__name__)
app.secret_key="secretkey"

#SQlAlchemy configure
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
db = SQLAlchemy(app)

#database model
class User(db.Model):
    id=db.Column(db.Integer, primary_key =True)
    username=db.Column(db.String(25), unique=True, nullable=False)
    password_hash=db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash=generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.Text, nullable=False)


#routing
@app.route('/')
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("home.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # Check if fields are empty
        if not username or not password:
            flash("Please fill out both fields.", "error")
            return redirect(url_for('login'))

        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        print(f"Login Attempt: {username}, Exists: {bool(user)}")
        if user:
            print("Password Match:", user.check_password(password))


        # Validate password
        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash("Incorrect username or password", "error")
            return redirect(url_for('login'))

    return render_template("login.html")




    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user:
            return render_template("register.html", error="User already registered")

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))

    return render_template("register.html")


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html', username=session['username'])


# @app.route("/logout")
# def logout():
#     session.pop('username', None)
#     return redirect(url_for('home'))

@app.route("/get-started")
def start():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route("/api/pets")
def get_pets():
    pets = Pet.query.all()
    pet_list = [
        {
            "id": pet.id,
            "name": pet.name,
            "breed": pet.breed,
            "age": pet.age,
            "location": pet.location,
            "image_url": pet.image_url
        }
        for pet in pets
    ]
    return jsonify(pet_list)


@app.route('/add-pet', methods=['POST'])
def add_pet():
    name = request.form['name']
    breed = request.form['breed']
    age = request.form['age']
    location = request.form['location']
    image_url = request.form['image_url']

    new_pet = Pet(
        name=name,
        breed=breed,
        age=age,
        location=location,
        image_url=image_url
    )

    db.session.add(new_pet)
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route("/add-sample-pets")
def add_sample_pets():
    sample_pets = [
        Pet(name="Rico", breed="Labrador Retriever", age="3 Yrs 10 Mos", location="Beverly Hills, CA", image_url="https://place-puppy.com/300x300"),
        Pet(name="Oreo", breed="Münsterländer", age="3 Yrs 6 Mos", location="West Hollywood, CA", image_url="https://place-puppy.com/301x301"),
        Pet(name="Cooper", breed="Springer Spaniel", age="2 Yrs", location="Los Angeles, CA", image_url="https://place-puppy.com/302x302"),
    ]
    db.session.add_all(sample_pets)
    db.session.commit()
    return "Sample pets added!"




@app.route("/adopt")
def adopt():
    return render_template("adopt.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))




if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
