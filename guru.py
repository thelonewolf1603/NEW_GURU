from flask import Flask, render_template, request, redirect, url_for, flash
from flask_socketio import SocketIO, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from datetime import datetime

app = Flask(__name__, static_url_path='', static_folder='static')
app.secret_key = 'many random bytes'
app.static_folder = 'static'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:\\Users\\neeladri\\guru\\sqlite\\database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

socketio = SocketIO(app)


class Mentor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll = db.Column(db.String(20), nullable=False)
    dept = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    

class Mentee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Mentee %r>' % self.name

class Feed(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    desc = db.Column(db.String(200), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    
@app.route('/')
def index():
    return render_template("index.html")

    



           
@app.route('/home',methods=["GET", "POST"])
def home():
    return render_template("index.html")    

@app.route('/dashboard_mentor/<roll>')
def dashboard_mentor(roll):
    mn = Mentor.query.all()
    posts = Feed.query.all()
        
    mentor = Mentor.query.filter_by(roll=roll).first()

    return render_template('dashboard.html',user = mentor, mentors=mn, feed=posts)

@app.route('/dashboard_mentee/<roll>')
def dashboard_mentee(roll):
    mn = Mentor.query.all()
    posts = Feed.query.all()
        
    mentee = Mentee.query.filter_by(roll=roll).first()

    return render_template('dashboard.html',user = mentee, mentors=mn, feed=posts)


@app.route('/savepost', methods=["GET","POST"])
def savepost():
    if request.method == "POST":
        desc = request.form['desc']
        content = request.form['postcontent']
        name = request.form['rolle']
        date = datetime.now()
        flag = 0
        men1 =Mentor.query.filter_by(roll=name).first()
        men2 = Mentee.query.filter_by(roll=name).first()
        if men1 != None:
            new_post = Feed(name = men1.name, desc = desc, content = content, date = date.strftime("%x"))
            flag=1
        else :
            new_post = Feed(name = men2.name, desc = desc, content = content, date = date.strftime("%x"))
            flag=2
        db.session.add(new_post)
        db.session.commit()
        if flag==1 :
            return redirect(url_for('dashboard_mentor',roll=name))
        else :
            return redirect(url_for('dashboard_mentee',roll=name))

    return redirect(url_for('home'))


@app.route('/mentor_register', methods=["GET", "POST"])
def mentor_register():
    if request.method == "POST":
        new_mentor = Mentor(name=request.form['name'], roll=request.form['roll'], dept= request.form['dept'], year=request.form['year'], password=request.form['password'])
        db.session.add(new_mentor)
        db.session.commit()
        flash('successfuly registered')
        return redirect('login')


    return render_template('index.html')


@app.route('/mentee_register', methods=["GET", "POST"])
def mentee_register():
    if request.method == "POST":
        new_mentee = Mentee(name=request.form['name'], roll=request.form['roll'], year=request.form['year'], password=request.form['password'])
        db.session.add(new_mentee)
        db.session.commit()
        
        return render_template('login.html')


    return render_template('index.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    
    return render_template('login.html')



@app.route('/mentor_auth', methods=["GET", "POST"])
def mentor_auth():
    if request.method == "POST":
        roll = request.form['roll']
        password = request.form['password']
        mn = Mentor.query.all()
        posts = Feed.query.all()
        
        mentor = Mentor.query.filter_by(roll=roll).first()

        if mentor == None :
            
            return '<h1>no valid user</h>'

        elif mentor.password != password :
            
            return redirect(url_for('login'))

        else:

            return redirect(url_for('dashboard_mentor',roll=mentor.roll))

    return '<h1>no valid user</h>'
      

@app.route('/mentee_auth', methods=["GET", "POST"])
def mentee_auth():
    if request.method == "POST":
        roll = request.form['roll']
        password = request.form['password']
        mn = Mentee.query.all()
        posts = Feed.query.all()
        
        mentee = Mentee.query.filter_by(roll=roll).first()

        if mentee == None :
            
            return '<h1>no valid user</h>'

        elif mentee.password != password :
            
            return redirect(url_for('login'))

        else:

            return redirect(url_for('dashboard_mentee',roll=mentee.roll))

    return '<h1>no valid user</h>'

@app.route('/chat')
def chat():
    username = request.args.get('username')
    room = request.args.get('room')

    if username and room:
        return render_template('dashboard.html', username=username, room=room)
    else:
        return redirect(url_for('home'))


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))
    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])


if __name__ == '__main__':
    socketio.run(app, debug=True)

