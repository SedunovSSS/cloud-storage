from flask import Flask, render_template, request, redirect, make_response
from flask_sqlalchemy import SQLAlchemy
import os
import hashlib, datetime

HOST = '0.0.0.0'
PORT = 5000

DB_NAME = "sqlite:///database.db"
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_NAME
UPLOAD_FOLDER = './static/uploads'
db = SQLAlchemy(app)


class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    dateR = db.Column(db.DateTime, default=datetime.datetime.utcnow())

    def __repr__(self):
        return '<Users %r>' % self.id


class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(150), nullable=False)
    path = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    count = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Files %r>' % self.id


@app.route('/')
def main():
    name = request.cookies.get('user')
    if name is None:
        name = "Guest"
    return render_template("index.html", name=name)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        login = request.form['login']
        email = request.form['email']
        passw1 = request.form['passw1']
        passw2 = request.form['passw2']

        if passw1 == passw2:
            password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
            exists = db.session.query(Users.id).filter_by(login=login).first() is not None or db.session.query(Users.id).filter_by(email=email).first() is not None
            if not exists:
                user = Users(login=login, email=email, password=password)
            else:
                return redirect("/register")
            try:
                db.session.add(user)
                db.session.commit()
                resp = make_response(redirect("/"))
                resp.set_cookie('user', user.login)
                return resp
            except Exception as ex:
                print(ex)
                return redirect("/register")
    else:
        name = request.cookies.get('user')
        if name is None:
            name = "Guest"
        try:
            path = db.session.query(Users.path).filter_by(login=name).first()[0]
            return render_template("register.html", name=name, path=path)
        except:
            return render_template("register.html", name=name)


@app.route('/login', methods=['POST', "GET"])
def login():
    if request.method == "POST":
        email = request.form['email']
        passw1 = request.form['passw1']
        passw2 = request.form['passw2']
        if passw1 == passw2:
            password = hashlib.md5(passw1.encode("utf-8")).hexdigest()
            exists = db.session.query(Users.id).filter_by(email=email, password=password).first() is not None
            user = db.session.query(Users.login).filter_by(email=email, password=password).first()
            if exists:
                resp = make_response(redirect("/"))
                resp.set_cookie('user', user[0])
                return resp
            else:
                return redirect("/login")

        else:
            name = request.cookies.get('user')
            if name is None:
                name = "Guest"
            try:
                path = db.session.query(Users.path).filter_by(login=name).first()[0]
                return render_template("login.html", name=name, path=path)
            except:
                return render_template("login.html", name=name)
    else:
        name = request.cookies.get('user')
        if name is None:
            name = "Guest"
        try:
            path = db.session.query(Users.path).filter_by(login=name).first()[0]
            return render_template("login.html", name=name, path=path)
        except:
            return render_template("login.html", name=name)


@app.route("/upload", methods=['POST', 'GET'])
def upload():
    if request.method == "POST":
        name = request.cookies.get('user')
        if name is None:
            return redirect("/login")

        file = request.files['file[]']
        filename = file.filename
        n = os.path.splitext(filename)[0]
        path = f"static/uploads/{name}/{n}/{filename}"
        while os.path.exists(path):
            n = "1" + n
            path = f"static/uploads/{name}/{n}/{filename}"
        os.makedirs(f"static/uploads/{name}/{n}")
        file.save(path)
        size = os.path.getsize(path)
        if size < 1000:
            count = 1
        elif 1000 < size < 1000000:
            count = 1000
        elif 1000000 < size < 1000000000:
            count = 1000000
        else:
            count = 1000000000
        file = Files(author=name, path=path, size=size, name=filename, count=count)
        try:
            db.session.add(file)
            db.session.commit()
            return redirect("/myfiles")
        except Exception as ex:
            print(ex)
            return redirect("/upload")
    else:
        name = request.cookies.get('user')
        if name is None:
            return redirect("/login")
        return render_template("upload.html")


@app.route("/myfiles")
def myfiles():
    name = request.cookies.get('user')
    if name is None:
        return redirect("/login")
    else:
        files = Files.query.filter_by(author=name).all()
        files = list(files)
        if len(files) == 2:
            files[0], files[1] = files[1], files[0]
        elif len(files) > 2:
            files.reverse()
        return render_template("myfiles.html", files=files)


@app.route("/deletefile")
def delete():
    id = request.args.get('id')
    name = request.cookies.get('user')
    if name is None:
        return redirect("/login")
    file = Files.query.filter_by(id=id, author=name).first()
    path = file.path
    os.remove(path)
    path_split = path.split("/")
    os.rmdir(f"{path_split[0]}/{path_split[1]}/{path_split[2]}/{path_split[3]}")
    Files.query.filter_by(id=id, author=name).delete()
    db.session.commit()
    return redirect("/myfiles")


@app.route('/static/uploads/<string:name>/<string:dir>/<string:file>')
def redirection(name, dir, file):
    return redirect("/myfiles")


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
