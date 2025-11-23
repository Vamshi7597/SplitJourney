"""
Main entry point for SplitJourney.
Handles application initialization and routing.
"""
import flet as ft
import theme
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from core.db import init_db
from ui.login_view import login_view
from ui.signup_view import signup_view
from ui.groups_list_view import groups_list_view
from ui.group_detail_view import group_detail_view
from ui.add_expense_view import add_expense_view
from ui.edit_expense_view import edit_expense_view
from ui.create_poll_view import create_poll_view
from ui.poll_detail_view import poll_detail_view
from ui.member_management_view import member_management_view

def main(page: ft.Page):
    # Initialize Database
    init_db()

    # App Configuration
    page.title = "SplitJourney"
    page.theme_mode = "light"
    page.padding = 0
    page.bgcolor = theme.PRIMARY_BG
    
    # Custom fonts could be loaded here
    # page.fonts = {"Roboto": "fonts/Roboto-Regular.ttf"}

    def route_change(route):
        page.views.clear()
        
        # Routing Logic
        troute = ft.TemplateRoute(page.route)
        
        if troute.match("/login"):
            page.views.append(login_view(page))
        elif troute.match("/signup"):
            page.views.append(signup_view(page))
        elif troute.match("/groups"):
            page.views.append(groups_list_view(page))
        elif troute.match("/groups/:id"):
            page.views.append(group_detail_view(page, int(troute.id)))
        elif troute.match("/groups/:id/expenses/new"):
            page.views.append(add_expense_view(page, int(troute.id)))
        elif troute.match("/groups/:id/expenses/:expense_id/edit"):
            page.views.append(edit_expense_view(page, int(troute.id), int(troute.expense_id)))
        elif troute.match("/groups/:id/polls/new"):
            page.views.append(create_poll_view(page, int(troute.id)))
        elif troute.match("/groups/:id/polls/:poll_id"):
            page.views.append(poll_detail_view(page, int(troute.id), int(troute.poll_id)))
        elif troute.match("/groups/:id/members"):
            page.views.append(member_management_view(page, int(troute.id)))
        else:
            # Default to login
            page.go("/login")
            
        page.update()

    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Check for persistent login
    user_id = page.client_storage.get("user_id")
    if user_id:
        import core.auth
        core.auth.CURRENT_USER_ID = user_id
        page.go("/groups")
    else:
        page.go("/login")

import os

if __name__ == "__main__":
    # Get port from environment variable (Render sets this)
    port = int(os.getenv("PORT", 8000))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0", assets_dir="downloads")
