# admin.py
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    
    # 1. Clean up any old attempts
    existing_admin = User.query.filter_by(email='admin@agriscan.com').first()
    if existing_admin:
        db.session.delete(existing_admin)
        db.session.commit()
    
    # 2. Create the clean Admin account
    hashed_pw = generate_password_hash('admin123')
    new_admin = User(
        full_name="System Administrator",
        email="admin@agriscan.com",
        password=hashed_pw,
        role="admin",  # EXACTLY 'admin'
        location="Headquarters",
        phone="000-000-0000"
    )
    db.session.add(new_admin)
    db.session.commit()
    print("SUCCESS: Admin 'admin@agriscan.com' created with password 'admin123'")