"""
Chat Tab Component for Group Detail View.
Displays group chat messages with send functionality.
"""
import flet as ft
import theme
from core.db import SessionLocal
from core.logic import add_message, get_messages
from core.auth import get_current_user
from datetime import datetime

def chat_tab(page: ft.Page, group_id: int):
    """
    Creates the chat tab content for a group.
    
    Args:
        page: Flet page object
        group_id: ID of the group
        
    Returns:
        ft.Container: Chat tab with messages and input
    """
    db = SessionLocal()
    user = get_current_user(db)
    
    if not user:
        db.close()
        return ft.Container(content=ft.Text("Please login"))
    
    # Find current user's member ID in this group
    from core.models import GroupMember
    current_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user.id
    ).first()
    
    # Message list container
    message_list = ft.Column(
        spacing=10,
        scroll=ft.ScrollMode.AUTO,
        auto_scroll=True,
        expand=True
    )
    
    # Input field
    message_input = ft.TextField(
        hint_text="Type your message...",
        border_radius=theme.BORDER_RADIUS,
        border_color=theme.DIVIDER_COLOR,
        focused_border_color=theme.FOCUS_RING,
        bgcolor=theme.INPUT_BG,
        filled=True,
        multiline=False,
        expand=True,
        on_submit=lambda _: send_message()
    )
    
    def load_messages():
        """Loads and displays all messages for the group."""
        message_list.controls.clear()
        messages = get_messages(db, group_id)
        
        if not messages:
            message_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No messages yet. Start the conversation!",
                        color=theme.TEXT_SECONDARY,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    padding=40
                )
            )
        else:
            for msg in messages:
                # Format timestamp
                time_str = msg.created_at.strftime("%I:%M %p")
                date_str = msg.created_at.strftime("%b %d")
                
                message_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(
                                        msg.sender.member_name,
                                        weight=ft.FontWeight.BOLD,
                                        color=theme.PRIMARY_COLOR,
                                        size=14
                                    ),
                                    ft.Text(
                                        f"{date_str} • {time_str}",
                                        size=11,
                                        color=theme.TEXT_SECONDARY
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(
                                    msg.text,
                                    color=theme.TEXT_PRIMARY,
                                    size=14
                                )
                            ], spacing=4),
                            padding=12
                        ),
                        color=theme.CARD_BG,
                        elevation=1
                    )
                )
        
        page.update()
    
    def send_message():
        """Sends a new message."""
        if not message_input.value or not message_input.value.strip():
            return
        
        if not current_member:
            page.snack_bar = ft.SnackBar(ft.Text("You are not a member of this group"))
            page.snack_bar.open = True
            page.update()
            return
        
        action_db = SessionLocal()
        try:
            add_message(action_db, group_id, current_member.id, message_input.value.strip())
            message_input.value = ""
            load_messages()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"))
            page.snack_bar.open = True
        finally:
            action_db.close()
        
        page.update()
    
    # Load initial messages
    load_messages()
    db.close()
    
    # Send button
    send_button = ft.IconButton(
        icon="send",
        icon_color=theme.PRIMARY_COLOR,
        tooltip="Send",
        on_click=lambda _: send_message()
    )
    
    # Input bar at bottom
    input_bar = ft.Container(
        content=ft.Row([
            message_input,
            send_button
        ], spacing=10),
        bgcolor=theme.CARD_BG,
        padding=10,
        border=ft.border.only(top=ft.border.BorderSide(1, theme.DIVIDER_COLOR))
    )
    
    return ft.Container(
        content=ft.Column([
            message_list,
            input_bar
        ], spacing=0),
        padding=0,
        expand=True
    )
