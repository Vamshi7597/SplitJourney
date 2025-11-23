"""
Signup View.
Handles new user registration with validation.
"""
import flet as ft
import re
from ui.components import PrimaryButton, InputField
import theme
from core.db import SessionLocal
from core.auth import create_user

def is_valid_email(email):
    """
    Validates email format using regex.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if email format is valid, False otherwise
    """
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def signup_view(page: ft.Page):
    """
    Renders the signup screen with name, email, and password inputs.
    
    Args:
        page (ft.Page): The Flet page object for navigation and updates
        
    Returns:
        ft.View: The signup view with input fields and validation
        
    Behavior:
        - Validates all input fields are filled
        - Validates email format
        - Ensures password is at least 6 characters
        - Confirms password match
        - Creates new user account in database
        - Handles duplicate email errors
        - Navigates to login on success
    """
    """
    Renders the signup screen.
    """
    name_input = InputField("Full Name")
    email_input = InputField("Email")
    password_input = InputField("Password", password=True)
    confirm_password_input = InputField("Confirm Password", password=True)
    error_text = ft.Text("", color=theme.ERROR_COLOR)

    def on_signup_click(e):
        if not name_input.value or not email_input.value or not password_input.value:
            error_text.value = "Please fill in all fields"
            page.update()
            return
        
        if not is_valid_email(email_input.value):
            error_text.value = "Please enter a valid email address"
            page.update()
            return

        if len(password_input.value) < 6:
            error_text.value = "Password must be at least 6 characters"
            page.update()
            return

        if password_input.value != confirm_password_input.value:
            error_text.value = "Passwords do not match"
            page.update()
            return

        db = SessionLocal()
        try:
            user = create_user(db, name_input.value, email_input.value, password_input.value)
            db.close()

            if user:
                page.snack_bar = ft.SnackBar(ft.Text("Account created! Please login."))
                page.snack_bar.open = True
                page.go("/login")
            else:
                error_text.value = "Email already exists"
                page.update()
        except Exception as ex:
            db.close()
            error_text.value = f"An error occurred: {str(ex)}"
            page.update()
            print(ex) # Log to console for debugging


    def on_login_link(e):
        page.go("/login")

    return ft.View(
        "/signup",
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(height=20),
                        ft.Text("Create Account", size=28, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                        ft.Text("Join SplitJourney", size=14, color=theme.TEXT_SECONDARY),
                        ft.Container(height=30),
                        name_input,
                        email_input,
                        password_input,
                        confirm_password_input,
                        error_text,
                        ft.Container(height=20),
                        PrimaryButton("Sign Up", on_signup_click, width=240),
                        ft.Container(height=10),
                        ft.TextButton(
                            "Already have an account? Login",
                            on_click=on_login_link,
                            style=ft.ButtonStyle(color=theme.PRIMARY_COLOR)
                        )
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=40,
                alignment=ft.alignment.center,
                expand=True
            )
        ],
        bgcolor=theme.PRIMARY_BG  # Pure white
    )
