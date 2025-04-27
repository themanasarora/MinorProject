#import dependencies
from flask import Flask, render_template,request, url_for, redirect,session,flash,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import openai

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
    
    
class Adoption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=False)
    
    # Denormalized pet info
    pet_name = db.Column(db.String(100), nullable=False)
    pet_breed = db.Column(db.String(100), nullable=False)
    pet_image_url = db.Column(db.Text, nullable=True)

    adopter_name = db.Column(db.String(100), nullable=False)
    adopter_email = db.Column(db.String(120), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    pet = db.relationship('Pet', backref=db.backref('adoptions', lazy=True))



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
    pets = Pet.query.all()
    return render_template("adopt.html", pets=pets)


@app.route('/adopt/<int:pet_id>', methods=['GET', 'POST'])
def adopt_pet(pet_id):
    pet = Pet.query.get_or_404(pet_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        reason = request.form['reason']

        new_adoption = Adoption(
        pet_id=pet.id,
        pet_name=pet.name,
        pet_breed=pet.breed,
        pet_image_url=pet.image_url,
        adopter_name=name,
        adopter_email=email,
        contact_number=contact,
        reason=reason
    )


        db.session.add(new_adoption)
        db.session.commit()
        flash(f"Adoption request for {pet.name} submitted successfully!", "success")
        return redirect(url_for('adopt'))

    return render_template('adopt_pet.html', pet=pet)




@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/pet/<int:pet_id>")
def pet_info(pet_id):
    pet = Pet.query.get_or_404(pet_id)
    return render_template("petinfo.html", pet=pet)


@app.route("/add-more-sample-pets")
def add_more_sample_pets():
    more_pets = [
        Pet(name="Luna", breed="Husky", age="2 Yrs", location="Bangalore", image_url="https://place-puppy.com/310x310"),
        Pet(name="Max", breed="Beagle", age="4 Yrs", location="Pune", image_url="https://place-puppy.com/311x311"),
        Pet(name="Chloe", breed="Pomeranian", age="3 Yrs", location="Chennai", image_url="https://place-puppy.com/312x312"),
        Pet(name="Milo", breed="German Shepherd", age="2 Yrs 6 Mos", location="Mumbai", image_url="https://place-puppy.com/313x313"),
        Pet(name="Loki", breed="Siberian Husky", age="5 Yrs", location="Delhi", image_url="https://place-puppy.com/314x314"),
        Pet(name="Zoe", breed="Shih Tzu", age="1 Yr 4 Mos", location="Hyderabad", image_url="https://place-puppy.com/315x315"),
        Pet(name="Leo", breed="Labrador", age="3 Yrs", location="Ahmedabad", image_url="https://place-puppy.com/316x316"),
        Pet(name="Nala", breed="Dalmatian", age="2 Yrs", location="Kolkata", image_url="https://place-puppy.com/317x317"),
        Pet(name="Bailey", breed="Boxer", age="1 Yr", location="Lucknow", image_url="https://place-puppy.com/318x318"),
        Pet(name="Rocky", breed="Doberman", age="3 Yrs 8 Mos", location="Nagpur", image_url="https://place-puppy.com/319x319"),
        Pet(name="Coco", breed="French Bulldog", age="2 Yrs", location="Patna", image_url="https://place-puppy.com/320x320"),
        Pet(name="Buddy", breed="Cocker Spaniel", age="4 Yrs", location="Bhopal", image_url="https://place-puppy.com/321x321"),
        Pet(name="Daisy", breed="Pug", age="2 Yrs 2 Mos", location="Indore", image_url="https://place-puppy.com/322x322"),
        Pet(name="Oscar", breed="Great Dane", age="5 Yrs", location="Jaipur", image_url="https://place-puppy.com/323x323"),
        Pet(name="Mochi", breed="Rottweiler", age="3 Yrs 1 Mo", location="Surat", image_url="https://place-puppy.com/324x324"),
        Pet(name="Simba", breed="Golden Retriever", age="2 Yrs 5 Mos", location="Noida", image_url="https://place-puppy.com/325x325"),
        Pet(name="Lilly", breed="Maltese", age="2 Yrs", location="Thane", image_url="https://place-puppy.com/326x326"),
        Pet(name="Bruno", breed="Chow Chow", age="1 Yr 9 Mos", location="Kanpur", image_url="https://place-puppy.com/327x327"),
        Pet(name="Teddy", breed="Pekingese", age="2 Yrs 6 Mos", location="Guwahati", image_url="https://place-puppy.com/328x328"),
        Pet(name="Ginger", breed="Chihuahua", age="3 Yrs", location="Chandigarh", image_url="https://place-puppy.com/329x329"),
    ]
    db.session.add_all(more_pets)
    db.session.commit()
    return "20 new sample pets added!"





# Set your OpenAI API key
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']

    # Call HuggingFace free chatbot model
    api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"

    headers = {
        "Authorization": "Bearer YOUR_HUGGINGFACE_TOKEN"  # optional if you have a free token
    }

    payload = {
        "inputs": {
            "text": user_message
        }
    }

    response = requests.post(api_url, json=payload, headers=headers)

    if response.status_code == 200:
        bot_response = response.json()['generated_text']
    else:
        bot_response = "Sorry, I couldn't process that right now. Please try again later."

    return jsonify({'response': bot_response})



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
