"""
Poll Detail View.
Shows poll question, voting options, and results with percentage bars.
"""
import flet as ft
from ui.components import app_bar, PrimaryButton, section_title
import theme
from core.db import SessionLocal
from core.auth import get_current_user
from core.logic import vote_poll, get_poll_results, get_member_vote
from core.models import Poll, GroupMember

def poll_detail_view(page: ft.Page, group_id: int, poll_id: int):
    """
    Renders the poll detail with voting and results.
    
    Args:
        page: Flet page object
        group_id: ID of the group
        poll_id: ID of the poll
        
    Returns:
        ft.View: Poll detail view
    """
    db = SessionLocal()
    user = get_current_user(db)
    
    if not user:
        db.close()
        page.go("/login")
        return ft.View("/login", [])
    
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    
    if not poll:
        db.close()
        return ft.View("/404", [ft.Text("Poll not found")])
    
    # Find current user's member ID
    current_member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user.id
    ).first()
    
    # Check if user already voted
    existing_vote = get_member_vote(db, poll_id, current_member.id) if current_member else None
    
    # Selected option (radio group)
    selected_option = ft.Ref[ft.RadioGroup]()
    error_text = ft.Text("", color=theme.ERROR_COLOR)
    
    # Content containers
    voting_section = ft.Container()
    results_section = ft.Container()
    
    def load_voting_interface():
        """Loads the voting interface with radio buttons."""
        voting_section.content = ft.Column([
            section_title(poll.question),
            ft.Container(height=10),
            ft.RadioGroup(
                ref=selected_option,
                content=ft.Column([
                    ft.Radio(
                        value=str(option.id),
                        label=option.text,
                        label_style=ft.TextStyle(color=theme.TEXT_PRIMARY, size=14),
                        active_color=theme.PRIMARY_COLOR
                    ) for option in poll.options
                ])
            ),
            ft.Container(height=20),
            error_text,
            PrimaryButton("Submit Vote", on_vote, width=200) if not existing_vote else ft.Container()
        ])
        page.update()
    
    def load_results():
        """Loads and displays poll results with percentage bars."""
        results = get_poll_results(db, poll_id)
        
        results_section.content = ft.Column([
            ft.Divider(color=theme.DIVIDER_COLOR),
            section_title("Results"),
            ft.Text(
                f"{results['total_votes']} {'vote' if results['total_votes'] == 1 else 'votes'}",
                color=theme.TEXT_SECONDARY,
                size=12
            ),
            ft.Container(height=10),
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(
                                result['text'],
                                size=14,
                                color=theme.TEXT_PRIMARY,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.Text(
                                f"{result['percentage']:.1f}%",
                                size=14,
                                color=theme.PRIMARY_COLOR,
                                weight=ft.FontWeight.BOLD
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=4),
                        ft.Stack([
                            # Background bar
                            ft.Container(
                                width=300,
                                height=8,
                                bgcolor="#E2E8F0",
                                border_radius=4
                            ),
                            # Filled bar
                            ft.Container(
                                width=300 * (result['percentage'] / 100),
                                height=8,
                                bgcolor=theme.PRIMARY_COLOR,
                                border_radius=4
                            )
                        ]),
                        ft.Text(
                            f"{result['votes']} {'vote' if result['votes'] == 1 else 'votes'}",
                            size=11,
                            color=theme.TEXT_SECONDARY
                        )
                    ], spacing=4),
                    padding=ft.padding.only(bottom=12)
                ) for result in results['options']
            ], spacing=8)
        ])
        page.update()
    
    def on_vote(e):
        """Handles vote submission."""
        if not selected_option.current or not selected_option.current.value:
            error_text.value = "Please select an option"
            page.update()
            return
        
        if not current_member:
            error_text.value = "You are not a member of this group"
            page.update()
            return
        
        option_id = int(selected_option.current.value)
        
        action_db = SessionLocal()
        try:
            vote_poll(action_db, poll_id, option_id, current_member.id)
            page.snack_bar = ft.SnackBar(ft.Text("Vote recorded successfully!"))
            page.snack_bar.open = True
            page.update()
            # Reload the page to show updated results
            import time
            time.sleep(0.5)
            page.go(f"/groups/{group_id}")
        except Exception as ex:
            error_text.value = f"Error: {str(ex)}"
            page.update()
        finally:
            action_db.close()
    
    # Load initial content
    if not existing_vote:
        load_voting_interface()
    
    load_results()
    
    # Show message if already voted
    if existing_vote:
        voted_option = next((opt for opt in poll.options if opt.id == existing_vote.option_id), None)
        info_text = ft.Container(
            content=ft.Column([
                ft.Text(
                    f"✓ You voted for: {voted_option.text if voted_option else 'Unknown'}",
                    color=theme.PRIMARY_COLOR,
                    weight=ft.FontWeight.W_500
                ),
                ft.Text(
                    "You can change your vote by selecting a different option and voting again.",
                    size=12,
                    color=theme.TEXT_SECONDARY
                )
            ], spacing=4),
            padding=12,
            bgcolor="#E0F7F7",
            border_radius=8,
            margin=ft.margin.only(bottom=10)
        )
        # Still show voting interface so they can change vote
        load_voting_interface()
    else:
        info_text = ft.Container()
    
    db.close()
    
    return ft.View(
        f"/groups/{group_id}/polls/{poll_id}",
        [
            app_bar("Poll", page, show_back=True),
            ft.Container(
                content=ft.Column([
                    info_text,
                    voting_section,
                    results_section
                ], scroll=ft.ScrollMode.AUTO),
                padding=theme.PADDING,
                expand=True
            )
        ],
        bgcolor=theme.PRIMARY_BG
    )
