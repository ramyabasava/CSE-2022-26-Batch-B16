import os
import numpy as np
import pandas as pd
import torch
from PIL import Image
import torchvision.transforms.functional as TF

from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import db, User, Scan
import CNN

app = Flask(__name__)

app.config['SECRET_KEY'] = 'agriscan-master-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agriscan.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- AI MODEL ---------------- #

disease_info = pd.read_csv('disease_info.csv', encoding='cp1252')
supplement_info = pd.read_csv('supplement_info.csv', encoding='cp1252')

model = CNN.CNN(39)
model.load_state_dict(torch.load("plant_disease_model_1_latest.pt", map_location=torch.device('cpu')))
model.eval()

import torch.nn.functional as F

def prediction(image_path):

    image = Image.open(image_path)
    image = image.resize((224,224))

    input_data = TF.to_tensor(image)
    input_data = input_data.view((-1,3,224,224))

    output = model(input_data)

    # Apply Softmax
    probs = F.softmax(output, dim=1)

    probs = probs.detach().numpy()

    index = np.argmax(probs)

    confidence = float(np.max(probs) * 100)

    return index, confidence

# ---------------- ROUTES ---------------- #

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['GET','POST'])
def register():

    if request.method == 'POST':

        user = User(
            full_name=request.form['full_name'],
            email=request.form['email'],
            password=generate_password_hash(request.form['password']),
            phone=request.form['phone'],
            location=request.form['location'],
            role='user'
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET','POST'])
def login():

    if request.method == 'POST':

        user = User.query.filter_by(email=request.form['email']).first()

        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route("/dashboard")
@login_required
def dashboard():

    total = Scan.query.filter_by(user_id=current_user.id).count()

    healthy = Scan.query.filter(
        Scan.user_id == current_user.id,
        Scan.disease_name.ilike("%healthy%")
    ).count()

    diseased = total - healthy

    # 🔹 Get last scan
    last_scan = Scan.query.filter_by(user_id=current_user.id)\
                          .order_by(Scan.id.desc())\
                          .first()

    return render_template(
        "dashboard.html",
        total=total,
        healthy=healthy,
        diseased=diseased,
        last_scan=last_scan
    )

@app.route('/admin-login', methods=['GET','POST'])
def admin_login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.role == 'admin' and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))

    return render_template('admin_login.html')

@app.route('/admin/dashboard')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():

    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    user_count = User.query.count()
    total_scans = Scan.query.count()

    # latest 20 scans for table
    reports = Scan.query.order_by(Scan.date_scanned.desc()).limit(20).all()

    return render_template(
        "admin_dashboard.html",
        user_count=user_count,
        total_scans=total_scans,
        reports=reports
    )
@app.route('/upload', methods=['GET','POST'])
@login_required
def upload():

    if request.method == 'POST':

        file = request.files['file']

        filename = secure_filename(file.filename)

        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        file.save(path)

        pred, conf = prediction(path)

        disease = disease_info['disease_name'][pred]
        desc = disease_info['description'][pred]
        prevent = disease_info['Possible Steps'][pred]
        sup_img = supplement_info['supplement image'][pred]
        supplement = supplement_info['supplement name'][pred]
        supplement_link = supplement_info['buy link'][pred]

        scan = Scan(
            disease_name=disease,
            description=desc,
            prevention=prevent,
            supplement_name=supplement,
            supplement_image=sup_img,
            supplement_link=supplement_link,
            confidence=conf,
            image_file=filename,
            owner=current_user
        )

        db.session.add(scan)
        db.session.commit()

        return redirect(url_for('result', id=scan.id))

    return render_template('upload.html')

@app.route('/admin/users')
@login_required
def admin_users():

    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    users = User.query.order_by(User.id.desc()).all()

    return render_template("admin_users.html", users=users)

@app.route('/admin/reports')
@login_required
def admin_reports():

    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))

    scans = Scan.query.order_by(Scan.date_scanned.desc()).all()

    return render_template("reports.html", scans=scans)
@app.route('/result/<int:id>')
@login_required
def result(id):

    scan = Scan.query.get_or_404(id)

    return render_template('result.html', scan=scan)


@app.route('/history')
@login_required
def history():

    scans = Scan.query.filter_by(user_id=current_user.id).order_by(Scan.date_scanned.desc()).all()

    return render_template('history.html', scans=scans)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


if __name__ == '__main__':

    with app.app_context():
        db.create_all()

        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)