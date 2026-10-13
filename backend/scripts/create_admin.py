
import getpass

from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.user import User


def main():
    db = SessionLocal()

    try:
        username = input("Enter Admin username: ").strip()

        if len(username) < 3 or len(username) > 50:
            print("Username must contain 3–50 characters.")
            return

        existing_user = (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

        if existing_user:
            print("That username already exists. Choose another username.")
            return

        password = getpass.getpass("Enter Admin password (minimum 12 characters): ")

        if len(password) < 12 or len(password) > 128:
            print("Password must contain 12–128 characters.")
            return

        confirm_password = getpass.getpass("Confirm Admin password: ")

        if password != confirm_password:
            print("Passwords do not match.")
            return

        admin = User(
            username=username,
            password_hash=hash_password(password),
            role="ADMIN",
            is_active=True,
        )

        db.add(admin)
        db.commit()

        print(f"Admin account '{username}' created successfully.")

    except IntegrityError:
        db.rollback()
        print("Could not create Admin. The username may already exist.")

    except Exception as error:
        db.rollback()
        print(f"Admin creation failed: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
