"""
Member Management View.
Allows viewing and managing group members.
"""
import flet as ft
from ui.components import app_bar, section_title, PrimaryButton, InputField
import theme
from core.db import SessionLocal
from core.models import Group, GroupMember, User
from core.auth import get_current_user

def member_management_view(page: ft.Page, group_id: int):
    """
    Renders the member management screen.
    
    Args:
        page: Flet page object
        group_id: ID of the group
        
    Returns:
        ft.View: Member management view
    """
    db = SessionLocal()
    user = get_current_user(db)
    
    if not user:
        db.close()
        page.go("/login")
        return ft.View("/login", [])
    
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        db.close()
        return ft.View("/404", [ft.Text("Group not found")])
    
    members_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    new_member_input = InputField("Member Name")
    error_text = ft.Text("", color=theme.ERROR_COLOR)
    
    def load_members():
        """Loads and displays all group members."""
        members_list.controls.clear()
        
        for member in group.members:
            # Check if this is the creator or if there are expenses
            has_expenses = any(e.payer_member_id == member.id for e in group.expenses)
            can_delete = len(group.members) > 1 and not has_expenses
            
            members_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Row([
                                ft.Icon("person", color=theme.PRIMARY_COLOR, size=20),
                                ft.Text(
                                    member.member_name,
                                    weight=ft.FontWeight.BOLD,
                                    color=theme.TEXT_PRIMARY,
                                    size=14
                                )
                            ], spacing=10),
                            ft.IconButton(
                                icon="delete",
                                icon_color=theme.ERROR_COLOR,
                                tooltip="Remove member",
                                visible=can_delete,
                                on_click=lambda _, m_id=member.id: delete_member(m_id)
                            ) if can_delete else ft.Container(width=40)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        padding=12
                    ),
                    color=theme.CARD_BG,
                    elevation=1
                )
            )
        
        page.update()
    
    def delete_member(member_id):
        """Deletes a member from the group."""
        action_db = SessionLocal()
        try:
            member = action_db.query(GroupMember).filter(GroupMember.id == member_id).first()
            if member:
                action_db.delete(member)
                action_db.commit()
                page.snack_bar = ft.SnackBar(ft.Text(f"{member.member_name} removed from group"))
                page.snack_bar.open = True
                # Reload members
                db_refresh = SessionLocal()
                group_refresh = db_refresh.query(Group).filter(Group.id == group_id).first()
                group.members[:] = group_refresh.members
                db_refresh.close()
                load_members()
        except Exception as ex:
            error_text.value = f"Error: {str(ex)}"
            page.update()
        finally:
            action_db.close()
    
    def add_member(e):
        """Adds a new member to the group."""
        member_name = new_member_input.value
        
        if not member_name or not member_name.strip():
            error_text.value = "Please enter a member name"
            page.update()
            return
        
        action_db = SessionLocal()
        try:
            new_member = GroupMember(
                group_id=group_id,
                member_name=member_name.strip()
            )
            action_db.add(new_member)
            action_db.commit()
            
            page.snack_bar = ft.SnackBar(ft.Text(f"{member_name} added to group"))
            page.snack_bar.open = True
            new_member_input.value = ""
            error_text.value = ""
            
            # Reload members
            db_refresh = SessionLocal()
            group_refresh = db_refresh.query(Group).filter(Group.id == group_id).first()
            group.members[:] = group_refresh.members
            db_refresh.close()
            load_members()
        except Exception as ex:
            error_text.value = f"Error: {str(ex)}"
            page.update()
        finally:
            action_db.close()
    
    load_members()
    db.close()
    
    return ft.View(
        f"/groups/{group_id}/members",
        [
            app_bar(f"{group.name} - Members", page, show_back=True),
            ft.Container(
                content=ft.Column([
                    section_title("Group Members"),
                    members_list,
                    ft.Divider(color=theme.DIVIDER_COLOR),
                    section_title("Add Member"),
                    ft.Row([
                        new_member_input,
                        ft.IconButton(
                            icon="add",
                            icon_color=theme.PRIMARY_COLOR,
                            tooltip="Add",
                            on_click=add_member
                        )
                    ]),
                    error_text,
                    ft.Container(height=10),
                    ft.Text(
                        "Note: Members with expenses cannot be removed.",
                        size=11,
                        color=theme.TEXT_SECONDARY,
                        italic=True
                    )
                ], scroll=ft.ScrollMode.AUTO),
                padding=theme.PADDING,
                expand=True
            )
        ],
        bgcolor=theme.PRIMARY_BG
    )
