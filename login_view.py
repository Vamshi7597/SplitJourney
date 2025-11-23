"""
Login View.
Handles user authentication and navigation to signup or groups.
"""
import flet as ft
from ui.components import PrimaryButton, InputField
import theme
from core.db import SessionLocal
from core.auth import authenticate_user
import core.auth

def login_view(page: ft.Page):
    """
    Renders the login screen with email and password inputs.
    
    Args:
        page (ft.Page): The Flet page object for navigation and updates
        
    Returns:
        ft.View: The login view with input fields and navigation buttons
        
    Behavior:
        - Authenticates user credentials against the database
        - Sets current user session on successful login
        - Navigates to /groups on success
        - Displays error message on failure
        - Provides link to signup page
    """
    email_input = InputField("Email")
    password_input = InputField("Password", password=True)
    error_text = ft.Text("", color=theme.ERROR_COLOR)

    def on_login_click(e):
        if not email_input.value or not password_input.value:
            error_text.value = "Please fill in all fields"
            page.update()
            return

        db = SessionLocal()
        user = authenticate_user(db, email_input.value, password_input.value)
        db.close()

        if user:
            core.auth.CURRENT_USER_ID = user.id
            page.client_storage.set("user_id", user.id)
            page.go("/groups")
        else:
            error_text.value = "Invalid email or password"
            page.update()

    def on_signup_click(e):
        page.go("/signup")

    return ft.View(
        "/login",
        [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Container(height=40),  # Top spacing
                        ft.Image(
                            src="assets/logo.png",
                            width=120,
                            height=120,
                            fit=ft.ImageFit.CONTAIN
                        ),
                        ft.Text(
                            "SplitJourney",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=theme.TEXT_PRIMARY
                        ),
                        ft.Text(
                            "Split expenses with ease",
                            size=16,
                            color=theme.TEXT_SECONDARY
                        ),
                        ft.Container(height=40),  # Spacing
                        email_input,
                        password_input,
                        error_text,
                        ft.Container(height=20),
                        PrimaryButton("Login", on_login_click, width=240),
                        ft.Container(height=10),
                        ft.TextButton(
                            "Create an Account",
                            on_click=on_signup_click,
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
        bgcolor=theme.PRIMARY_BG,  # Pure white
        padding=0
    )
