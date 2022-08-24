from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user


#don't forget that flask_sqlalchemy and flask_login need to be installed through the terminal commands


app = Flask(__name__)


app.config['SECRET_KEY'] = 'Zr4u7w!z%C*F-JaNdRgUkXp2s5v8y/A?'
# create database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout_log.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# initializes database
db = SQLAlchemy(app)


login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# creating the tables
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    first_name = db.Column(db.String(1000))
    last_name = db.Column(db.String(1000))


class Exercises(db.Model):
    exercise_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    date = db.Column(db.Integer, nullable=False)
    workout = db.Column(db.String(250))
    exercise = db.Column(db.String(250))
    sets =  db.Column(db.Integer)
    reps = db.Column(db.Integer)
    weight = db.Column(db.Float)


class Routines(db.Model):
    routine_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    workout = db.Column(db.String(250), nullable=False)
    routine_name = db.Column(db.String(250))



db.create_all()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/create-account', methods=["GET", "POST"])
def create_account():
    if request.method == "POST":

        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        #checks to see if there is already an account with this email
        if User.query.filter_by(email=request.form.get('email')).first():
            #User already exists
            flash("There is already an account associated with that email, please use a different email or log in instead!")
            return redirect(url_for('create_account'))

        if password1 != password2:
            flash("The entered passwords do not match.")
            return redirect(url_for('create_account'))
        else:
            hashed_salted_password = generate_password_hash(
                request.form.get('password'),
                method='pbkdf2:sha256',
                salt_length=8
            )

            new_user = User(
                email=request.form.get('email'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                password=hashed_salted_password
            )

            db.session.add(new_user)
            db.session.commit()

            #login the new user
            login_user(new_user, remember=True)

            return redirect(url_for('home'))

    return render_template('create_account.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        #remember to NOT include a comma after the next line, otherwise it creates a one element tuple rather than a string
        entered_email = request.form.get('email')
        entered_password = request.form.get('password')

        #Looking for the user by their email
        user = User.query.filter_by(email=entered_email).first()

        #if email not found
        if not user:
            flash("The email you entered is not associated with an account, please try again.")
            return redirect(url_for('login'))
        #if email was found but password wasn't correct
        elif not check_password_hash(user.password, entered_password):
            flash('Incorrect password, please try again.')
            return redirect(url_for('login'))
        #email is found + entered password is correct
        else:
            login_user(user, remember=True)
            # user_routines = db.session.query(Exercises.workout.distinct()).filter(Exercises.user_id == current_user.id).all()
            # print(user_routines)
            return redirect(url_for('workout_choice'))


    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))





@app.route('/dashboard')
@login_required
def dashboard():
    # full_workout_log = db.session.query(Exercises.workout.distinct()).all()
    # print(full_workout_log)
    return render_template("dashboard.html")



@app.route('/choose-a-workout')
@login_required
def workout_choice():
    full_user_workout_log = db.session.query(Exercises.workout.distinct()).filter(Exercises.user_id == current_user.id).all()
    user_routine_names = []
    for i in full_user_workout_log:
        user_routine_names.append(i[0])
    return render_template("workout.html", workout_list=user_routine_names)


@app.route('/enter-your-stats', methods=['GET', 'POST'])
@login_required
def add_to_workout():
    if request.form.get("button", False) == "Record a Workout":
        workout_list_box_result = request.form.get('Workout_ListBox')
        print(workout_list_box_result)
        workout_date = request.form.get('workout_date')
        exercise_list = []
        exercise_tuples = db.session.query(Exercises.exercise.distinct()).filter(Exercises.user_id == current_user.id, Exercises.workout == workout_list_box_result).all()
        for i in exercise_tuples:
            exercise_list.append(i[0])
        print(exercise_list)
        number_of_exercises = len(exercise_list)
        # feed the list of exercises into the entry.html, and render them on the new page (form)
        return render_template('entry.html', exercises_in_selected_workout=exercise_list,
                               workout_name=workout_list_box_result, workout_date=workout_date,
                               number_of_exercises=number_of_exercises)
    if request.form.get("button", False) == "Edit Routine":
        workout_list_box_result = request.form.get('Workout_ListBox')
        db.session.query(Routines).filter(Routines.user_id == current_user.id).delete()
        # db.session.query(Routines).delete()
        db.session.commit()
        exercise_list = []
        full_user_workout_log = db.session.query(Exercises.exercise.distinct()).filter(Exercises.user_id == current_user.id, Exercises.workout == workout_list_box_result).all()
        for i in full_user_workout_log:
            exercise_list.append(i[0])
        for exercise in exercise_list:
            new_routine = Routines(
                user_id=current_user.id,
                workout=exercise,
                routine_name=workout_list_box_result
            )
            db.session.add(new_routine)
            db.session.commit()
        print(exercise_list)
        print(f"edit button responded correctly to try and edit {workout_list_box_result}")
        return render_template('edit_routine.html', exercise_list=exercise_list, routine_name=workout_list_box_result)
    if request.form.get("button", False) == "Delete Routine":
        workout_list_box_result = request.form.get('Workout_ListBox')
        for row in db.session.query(Exercises):
            if row.workout == workout_list_box_result and row.user_id == current_user.id:
                db.session.delete(row)
        db.session.commit()
        # full_workout_log = db.session.query(Exercises.workout.distinct()).all()
        # workout_day_names = []
        # for i in full_workout_log:
        #     workout_day_names.append(i[0])
        # return render_template("workout.html", workout_list=workout_day_names)
        return redirect(url_for('workout_choice'))
    else:
        # full_workout_log = db.session.query(Exercises.workout.distinct()).all()
        # workout_day_names = []
        # for i in full_workout_log:
        #     workout_day_names.append(i[0])
        # return render_template("workout.html", workout_list=workout_day_names)
        return redirect(url_for('workout_choice'))


@app.route('/enter-your-stats', methods=['GET', 'POST'])
@login_required
def print_test(action):
    print()



@app.route("/", methods=['GET', 'POST'])
@login_required
def completed_exercises():
    # look into how to either stay on the same page (w/ the other fields STILL filled out), or use 1 submit button to
    # submit all the exercise forms at once. Because right now if someone fills out/submits one, it clears the others
    if request.method == "POST":
        exercises_in_workout_length = int(request.form["Number_of_Exercises"])
        for i in range(1, int(exercises_in_workout_length) + 1):
            if request.form[f"Weight{i}"] == '':
                weight_provided = None
                new_workout = Exercises(
                    user_id=current_user.id,
                    date=request.form["workout_date"],
                    workout=request.form[f"Workout{i}"],
                    exercise=request.form[f"Exercise{i}"],
                    sets=request.form[f"Sets{i}"],
                    reps=request.form[f"Reps{i}"],
                    weight=weight_provided
                )
                db.session.add(new_workout)
                db.session.commit()
            else:
                new_workout = Exercises(
                    user_id=current_user.id,
                    date=request.form["workout_date"],
                    workout=request.form[f"Workout{i}"],
                    exercise=request.form[f"Exercise{i}"],
                    sets=request.form[f"Sets{i}"],
                    reps=request.form[f"Reps{i}"],
                    weight=request.form[f"Weight{i}"]
                )
                db.session.add(new_workout)
                db.session.commit()
        return redirect(url_for('home'))
    else:
        pass


# @app.route("/test/<string:exercise_list>", methods=['GET', 'POST'])
# def test_func(exercise_list):
#     print(exercise_list)
#     return redirect(url_for('home'))


# @app.route("/new-routine", methods=['GET', 'POST'])
# def new_routine():
#     if request.method == "POST":
#         exercise_list = request.form.get('Exercise_List')
#         # exercise_list = request.form["Exercise_List"]
#         print(type(exercise_list))
#         exercise_to_add = request.form["Exercise_Name"]
#         print(exercise_list)
#         # print(exercise_to_add)
#         # exercise_list.append(exercise_to_add)
#         return render_template('add_workout.html', exercise_list=exercise_list)
#     else:
#         exercise_list = []
#         print(type(exercise_list))
#         return render_template('add_workout.html', exercise_list=exercise_list)

@app.route("/new-routine", methods=['GET', 'POST'])
@login_required
def new_routine():
    if request.method == "POST":
        new_routine = Routines(
            user_id=current_user.id,
            workout=request.form["Exercise_Name"]
        )
        db.session.add(new_routine)
        db.session.commit()
        exercise_list = []
        exercise_tuples = db.session.query(Routines.workout.distinct()).filter(Routines.user_id == current_user.id).all()
        for i in exercise_tuples:
            exercise_list.append(i[0])
        return render_template('add_workout.html', exercise_list=exercise_list)
    else:
        db.session.query(Routines).filter(Routines.user_id == current_user.id).delete()
        db.session.commit()
        return render_template('add_workout.html')


@app.route("/new_routine", methods=['GET', 'POST'])
@login_required
def submit_new_routine():
    new_routine_name = request.form["routine_name"]

    # Looking for exercises by their user_id
    user_exercise_present = Routines.query.filter_by(user_id=current_user.id).first()
    if not user_exercise_present:
        #if they didn't enter any exercises
        flash("Please add exercises to your new routine before submitting!")
        return redirect(url_for('new_routine'))


    if Exercises.query.filter_by(workout=new_routine_name).first():
        print("duplicate name")
        flash("You already have a routine with that name, try adding a different routine!")
        exercise_list = []
        exercise_tuples = db.session.query(Routines.workout.distinct()).filter(Routines.user_id == current_user.id).all()
        for i in exercise_tuples:
            exercise_list.append(i[0])
        return render_template('add_workout.html', exercise_list=exercise_list)

    else:
        for row in db.session.query(Routines).filter(Routines.user_id == current_user.id):
            row.routine_name = new_routine_name
            new_workout = Exercises(
                date=0,
                user_id=current_user.id,
                workout=row.routine_name,
                exercise=row.workout
            )
            db.session.add(new_workout)
        db.session.commit()
        return redirect(url_for('workout_choice'))


@app.route("/delete")
@login_required
def delete_during_creation():
    # right now the delete button works, but it redirects the user to another page
    # change it so that you can delete one, and it will reload the page and keep what the
    # user already had entered (maybe this can be done by -> when delete() is invoked,
    # it saves the other names and feeds them back into the add_workout.html to
    # "start" with those names already in there
    exercise_name = request.args.get('exercise_name')
    print(exercise_name)
    # exercise_to_delete = Routines.query.get(exercise_name)
    # db.session.delete(exercise_to_delete)

    db.session.query(Routines).filter(Routines.user_id == current_user.id, Routines.workout == exercise_name).delete()

    db.session.commit()
    exercise_list = []
    exercise_tuples = db.session.query(Routines.workout.distinct()).filter(Routines.user_id == current_user.id).all()
    for i in exercise_tuples:
        exercise_list.append(i[0])
    return render_template('add_workout.html', exercise_list=exercise_list)


# @app.route("/edit-routine")
# def edit_routine():
#     db.session.query(Routines).delete()
#     db.session.commit()
#     routine_to_edit = request.args.get('routine_to_edit')
#     exercise_list = []
#     exercise_tuples = db.session.query(Exercises.exercise.distinct()).filter(Exercises.workout == routine_to_edit).all()
#     for i in exercise_tuples:
#         exercise_list.append(i[0])
#     for exercise in exercise_list:
#         new_routine = Routines(
#             workout=exercise
#         )
#         db.session.add(new_routine)
#         db.session.commit()
#     return render_template('add_workout.html', exercise_list=exercise_list)

@app.route("/edit-routine")
@login_required
def delete_from_routine():
    exercise_name = request.args.get('exercise_name')
    print(exercise_name)
    routine_name = request.args.get('routine_name')
    print(routine_name)
    # exercise_to_delete = Routines.query.get(exercise_name)
    # print(exercise_to_delete)
    # db.session.delete(exercise_to_delete)

    db.session.query(Routines).filter(Routines.user_id == current_user.id, Routines.workout == exercise_name).delete()

    db.session.commit()
    exercise_list = []
    exercise_tuples = db.session.query(Routines.workout.distinct()).filter(Routines.user_id == current_user.id).all()
    for i in exercise_tuples:
        exercise_list.append(i[0])
    return render_template('edit_routine.html', exercise_list=exercise_list, routine_name=routine_name)


@app.route("/save", methods=['GET', 'POST'])
@login_required
def save_routine_edits():
    # get routine_name
    # get the remaining exercise names and put them in a "keep" list
    # iterate through the database and find the rows where the routine name in the db == this routine name
    # "change" the routine_name, even if it's the same
    # check to see if the exercise name in the db is included in the "keep" list, and if not, delete it from the db
    new_routine_name = request.form['new_routine_name']
    old_routine_name = request.form['old_routine_name']
    exercise_keep_list = []
    exercise_tuples = db.session.query(Routines.workout.distinct()).filter(Routines.user_id == current_user.id).all()
    for i in exercise_tuples:
        exercise_keep_list.append(i[0])
    print(f'new_routine_name is {new_routine_name}')
    print(f'old_routine_name is {old_routine_name}')
    print(exercise_keep_list)
    for row in db.session.query(Exercises):
        if row.workout == old_routine_name and row.user_id == current_user.id:
            row.workout = new_routine_name
            if row.exercise not in exercise_keep_list:
                db.session.delete(row)
            else:
                pass
        db.session.commit()
            # MAKE SURE THAT IT WORKS WITH A NEW NAME TOO, ALSO DELETING ZERO EXERCISES AND IT STILL WORKING, etc.
    return render_template('index.html')




if __name__ == "__main__":
    app.run(debug=True)
