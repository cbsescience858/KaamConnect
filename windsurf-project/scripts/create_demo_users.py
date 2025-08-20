from app import create_app, db
from app.models.user import User

DEMO_USERS = [
    {"username": "Client EN", "email": "client_en@demo.local", "phone_number": "+91-9000000001", "user_type": "client", "preferred_language": "en"},
    {"username": "Client HI", "email": "client_hi@demo.local", "phone_number": "+91-9000000002", "user_type": "client", "preferred_language": "hi"},
    {"username": "Client TA", "email": "client_ta@demo.local", "phone_number": "+91-9000000003", "user_type": "client", "preferred_language": "ta"},
    {"username": "Client TE", "email": "client_te@demo.local", "phone_number": "+91-9000000004", "user_type": "client", "preferred_language": "te"},
    {"username": "Client KN", "email": "client_kn@demo.local", "phone_number": "+91-9000000005", "user_type": "client", "preferred_language": "kn"},
    {"username": "Client BN", "email": "client_bn@demo.local", "phone_number": "+91-9000000006", "user_type": "client", "preferred_language": "bn"},
    {"username": "Client MR", "email": "client_mr@demo.local", "phone_number": "+91-9000000007", "user_type": "client", "preferred_language": "mr"},
    {"username": "Client GU", "email": "client_gu@demo.local", "phone_number": "+91-9000000008", "user_type": "client", "preferred_language": "gu"},
    {"username": "Worker EN", "email": "worker_en@demo.local", "phone_number": "+91-9000000101", "user_type": "worker", "preferred_language": "en"},
    {"username": "Worker HI", "email": "worker_hi@demo.local", "phone_number": "+91-9000000102", "user_type": "worker", "preferred_language": "hi"},
    {"username": "Worker TA", "email": "worker_ta@demo.local", "phone_number": "+91-9000000103", "user_type": "worker", "preferred_language": "ta"},
    {"username": "Worker TE", "email": "worker_te@demo.local", "phone_number": "+91-9000000104", "user_type": "worker", "preferred_language": "te"},
    {"username": "Worker KN", "email": "worker_kn@demo.local", "phone_number": "+91-9000000105", "user_type": "worker", "preferred_language": "kn"},
    {"username": "Worker BN", "email": "worker_bn@demo.local", "phone_number": "+91-9000000106", "user_type": "worker", "preferred_language": "bn"},
    {"username": "Worker MR", "email": "worker_mr@demo.local", "phone_number": "+91-9000000107", "user_type": "worker", "preferred_language": "mr"},
    {"username": "Worker GU", "email": "worker_gu@demo.local", "phone_number": "+91-9000000108", "user_type": "worker", "preferred_language": "gu"},
]

DEFAULT_PASSWORD = "Passw0rd!"

app = create_app()


def upsert_user(payload: dict) -> User:
    user = User.query.filter(User.email == payload["email"]).first()
    if not user:
        user = User(
            username=payload["username"],
            email=payload["email"],
            phone_number=payload["phone_number"],
            user_type=payload["user_type"],
            preferred_language=payload["preferred_language"],
        )
        user.set_password(DEFAULT_PASSWORD)
        db.session.add(user)
        return user
    # Update any drifted fields and reset password for testing
    user.username = payload["username"]
    user.phone_number = payload["phone_number"]
    user.user_type = payload["user_type"]
    user.preferred_language = payload["preferred_language"]
    user.set_password(DEFAULT_PASSWORD)
    return user


with app.app_context():
    created, updated = 0, 0
    for demo in DEMO_USERS:
        existing = User.query.filter(User.email == demo["email"]).first()
        if existing:
            upsert_user(demo)
            updated += 1
        else:
            upsert_user(demo)
            created += 1
    db.session.commit()
    print(f"Demo users seeded. Created: {created}, Updated: {updated}. Default password: {DEFAULT_PASSWORD}")
