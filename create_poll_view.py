"""
Create Poll View.
Allows creating a new poll with question and multiple options.
"""
import flet as ft
from ui.components import app_bar, PrimaryButton, InputField, section_title
import theme
from core.db import SessionLocal
from core.auth import get_current_user
from core.logic import create_poll

def create_poll_view(page: ft.Page, group_id: int):
    """
    Renders the form to create a new poll.
    
    Args:
        page: Flet page object
        group_id: ID of the group
        
    Returns:
        ft.View: Create poll view
    """
    db = SessionLocal()
    user = get_current_user(db)
    
    if not user:
        db.close()
        page.go("/login")
        return ft.View("/login", [])
    
    # Find current user's member ID in this group
    from core.models import GroupMember
    current_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user.id
    ).first()
    
    db.close()
    
    # Form inputs
    question_input = InputField("Poll Question")
    
    # Option inputs (start with 2)
    option_inputs = [
        InputField("Option 1"),
        InputField("Option 2")
    ]
    
    options_container = ft.Column(spacing=10)
    
    error_text = ft.Text("", color=theme.ERROR_COLOR)
    
    def update_options_display():
        """Updates the displayed option inputs."""
        options_container.controls.clear()
        for i, option_input in enumerate(option_inputs):
            options_container.controls.append(
                ft.Row([
                    option_input,
                    ft.IconButton(
                        icon="delete",
                        icon_color=theme.ERROR_COLOR,
                        tooltip="Remove",
                        visible=len(option_inputs) > 2,
                        on_click=lambda _, idx=i: remove_option(idx)
                    ) if len(option_inputs) > 2 else ft.Container(width=40)
                ])
            )
        page.update()
    
    def add_option(e):
        """Adds a new option field."""
        if len(option_inputs) < 10:  # Max 10 options
            option_inputs.append(InputField(f"Option {len(option_inputs) + 1}"))
            update_options_display()
        else:
            error_text.value = "Maximum 10 options allowed"
            page.update()
    
    def remove_option(idx):
        """Removes an option field."""
        if len(option_inputs) > 2:
            option_inputs.pop(idx)
            # Renumber remaining options
            for i, opt in enumerate(option_inputs):
                opt.label = f"Option {i + 1}"
            update_options_display()
    
    def on_create(e):
        """Creates the poll."""
        question = question_input.value
        
        if not question or not question.strip():
            error_text.value = "Please enter a poll question"
            page.update()
            return
        
        # Collect non-empty options
        options = []
        for opt in option_inputs:
            if opt.value and opt.value.strip():
                options.append(opt.value.strip())
        
        if len(options) < 2:
            error_text.value = "Please provide at least 2 options"
            page.update()
            return
        
        if not current_member:
            error_text.value = "You are not a member of this group"
            page.update()
            return
        
        action_db = SessionLocal()
        try:
            create_poll(action_db, group_id, question.strip(), options, current_member.id)
            page.go(f"/groups/{group_id}")
            page.snack_bar = ft.SnackBar(ft.Text("Poll created!"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            error_text.value = f"Error: {str(ex)}"
            page.update()
        finally:
            action_db.close()
    
    update_options_display()
    
    return ft.View(
        f"/groups/{group_id}/polls/new",
        [
            app_bar("Create Poll", page, show_back=True),
            ft.Container(
                content=ft.Column([
                    section_title("Poll Question"),
                    question_input,
                    ft.Container(height=20),
                    section_title("Options"),
                    options_container,
                    ft.TextButton(
                        "+ Add Option",
                        on_click=add_option,
                        style=ft.ButtonStyle(color=theme.PRIMARY_COLOR)
                    ),
                    error_text,
                    ft.Container(height=20),
                    PrimaryButton("Create Poll", on_create, width=240)
                ], scroll=ft.ScrollMode.AUTO),
                padding=theme.PADDING,
                expand=True
            )
        ],
        bgcolor=theme.PRIMARY_BG
    )
