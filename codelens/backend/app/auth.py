from flask import Blueprint, request, session
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from models import User
from database import db


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/auth",
)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return {
            "error": "Request data is required."
        }, 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return {
            "error": "Name, email and password are required."
        }, 400

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:
        return {
            "error": "An account with this email already exists."
        }, 409

    password_hash = generate_password_hash(
        password
    )

    user = User(
        name=name,
        email=email,
        password_hash=password_hash,
    )

    db.session.add(user)
    db.session.commit()

    return {
        "message": "Registration successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return {
            "error": "Request data is required."
        }, 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return {
            "error": "Email and password are required."
        }, 400

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:
        return {
            "error": "Invalid email or password."
        }, 401

    if not check_password_hash(
        user.password_hash,
        password,
    ):
        return {
            "error": "Invalid email or password."
        }, 401

    # Store the logged-in user's ID in the session
    session["user_id"] = user.id

    return {
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        },
    }, 200

@auth_bp.route("/me", methods=["GET"])
def current_user():
    user_id = session.get("user_id")

    if not user_id:
        return {
            "error": "Not authenticated."
        }, 401

    user = User.query.get(user_id)

    if not user:
        session.clear()

        return {
            "error": "User not found."
        }, 401

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
        }
    }, 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return {
        "message": "Logout successful."
    }, 200