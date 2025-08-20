from app import create_app, db
from app.models.user import User

# Emails/phones to delete
targets = [
    {'email': 'adviktripathy@gmail.com'},
    {'phone_number': '9625250966'},
    {'email': 'divyabaj@gmail.com'}
]

app = create_app()
with app.app_context():
    deleted = 0
    for target in targets:
        q = User.query
        if 'email' in target:
            q = q.filter_by(email=target['email'])
        if 'phone_number' in target:
            q = q.filter_by(phone_number=target['phone_number'])
        users = q.all()
        for user in users:
            db.session.delete(user)
            deleted += 1
    db.session.commit()
    print(f"Deleted {deleted} test users.")
