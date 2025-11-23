"""
Polls Tab Component for Group Detail View.
Displays list of polls with create and view functionality.
"""
import flet as ft
import theme
from core.db import SessionLocal
from core.logic import get_polls

def polls_tab(page: ft.Page, group_id: int):
    """
    Creates the polls tab content for a group.
    
    Args:
        page: Flet page object
        group_id: ID of the group
        
    Returns:
        ft.Container: Polls tab with poll list
    """
    db = SessionLocal()
    
    polls_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)
    
    def load_polls():
        """Loads and displays all polls for the group."""
        polls_list.controls.clear()
        polls = get_polls(db, group_id)
        
        if not polls:
            polls_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon("poll", size=64, color=theme.TEXT_SECONDARY),
                        ft.Text(
                            "No polls yet",
                            size=18,
                            color=theme.TEXT_PRIMARY,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(
                            "Create a poll to get group opinions",
                            color=theme.TEXT_SECONDARY,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
                    alignment=ft.alignment.center,
                    padding=40
                )
            )
        else:
            for poll in polls:
                # Format date
                date_str = poll.created_at.strftime("%b %d, %Y")
                
                polls_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    poll.question,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme.TEXT_PRIMARY,
                                    size=16
                                ),
                                ft.Text(
                                    f"Created by {poll.creator.member_name} • {date_str}",
                                    size=12,
                                    color=theme.TEXT_SECONDARY
                                ),
                                ft.Container(height=8),
                                ft.ElevatedButton(
                                    "View Poll",
                                    on_click=lambda _, p_id=poll.id: page.go(f"/groups/{group_id}/polls/{p_id}"),
                                    bgcolor=theme.PRIMARY_COLOR,
                                    color=theme.TEXT_ON_DARK,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=8)
                                    )
                                )
                            ], spacing=6),
                            padding=16
                        ),
                        color=theme.CARD_BG,
                        elevation=2
                    )
                )
        
        page.update()
    
    load_polls()
    db.close()
    
    return ft.Container(
        content=polls_list,
        padding=theme.PADDING,
        expand=True
    )

def create_poll_fab(page: ft.Page, group_id: int):
    """
    Creates a floating action button for creating polls.
    
    Args:
        page: Flet page object
        group_id: ID of the group
        
    Returns:
        ft.FloatingActionButton: FAB for poll creation
    """
    return ft.FloatingActionButton(
        icon="add",
        bgcolor=theme.PRIMARY_COLOR,
        foreground_color=theme.TEXT_ON_DARK,
        on_click=lambda _: page.go(f"/groups/{group_id}/polls/new")
    )
