"""
Groups List View.
Shows all groups the user belongs to with create functionality.
"""
import flet as ft
from ui.components import app_bar, section_title, PrimaryButton, InputField
import theme
from core.db import SessionLocal
from core.auth import get_current_user
from core.logic import get_groups_for_user, create_group

def groups_list_view(page: ft.Page):
    """
    Renders the list of groups the current user is a member of.
    
    Args:
        page (ft.Page): The Flet page object for navigation and updates
        
    Returns:
        ft.View: The groups list view with group cards and create button
        
    Behavior:
        - Loads all groups for the current user
        - Displays group cards showing name, member count, and total spent
        - Provides bottom sheet for creating new groups
        - Allows adding comma-separated member names
        - Automatically adds creator as group member
        - Updates UI in-place when new group is created
        - Navigates to group detail when card is tapped
    """
    """
    Renders the list of groups.
    """
    db = SessionLocal()
    user = get_current_user(db)
    
    if not user:
        page.go("/login")
        return ft.View("/groups", [])

    groups = get_groups_for_user(db, user)
    
    # List of group cards
    group_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    
    for group in groups:
        # Calculate total spent
        total_spent = sum(e.amount for e in group.expenses)
        
        group_list.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(group.name, size=18, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                            ft.Text(f"Rs.{total_spent:.2f}", size=16, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_COLOR)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"{len(group.members)} members", size=12, color=theme.TEXT_SECONDARY)
                    ]),
                    padding=16,
                    on_click=lambda _, g_id=group.id: page.go(f"/groups/{g_id}")
                ),
                color=theme.CARD_BG,  # Pure white
                elevation=2,
                surface_tint_color=theme.PRIMARY_COLOR
            )
        )

    # Bottom sheet for creating new group
    new_group_name = InputField("Group Name")
    new_group_members = InputField("Members (comma separated, e.g. Alice, Bob)")
    error_text = ft.Text("", color=theme.ERROR_COLOR)
    
    def close_bottom_sheet(e):
        create_group_sheet.open = False
        page.update()

    def create_new_group(e):
        if not new_group_name.value:
            error_text.value = "Please enter a group name"
            page.update()
            return
            
        member_names = [m.strip() for m in new_group_members.value.split(",") if m.strip()]
        
        # Create a new session for this action
        action_db = SessionLocal()
        try:
            # Re-fetch user in this session to ensure attachment
            current_user = get_current_user(action_db)
            if current_user:
                new_group = create_group(action_db, new_group_name.value, current_user, member_names)
                create_group_sheet.open = False
                
                # Update UI in-place
                total_spent = 0.0
                group_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text(new_group.name, size=18, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                                    ft.Text(f"Rs.{total_spent:.2f}", size=16, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_COLOR)
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Text(f"{len(new_group.members)} members", size=12, color="grey")
                            ]),
                            padding=15,
                            on_click=lambda _, g_id=new_group.id: page.go(f"/groups/{g_id}")
                        ),
                        color="white",
                        elevation=2
                    )
                )
                
                # Clear inputs
                new_group_name.value = ""
                new_group_members.value = ""
                error_text.value = ""
                
                page.snack_bar = ft.SnackBar(ft.Text("Group created!"))
                page.snack_bar.open = True
                page.update()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Session expired. Please login again."))
                page.snack_bar.open = True
                page.go("/login")
        except Exception as ex:
            print(f"Error creating group: {ex}")
            import traceback
            traceback.print_exc()
            error_text.value = f"Error: {str(ex)}"
            page.update()
        finally:
            action_db.close()

    create_group_sheet = ft.BottomSheet(
        content=ft.Container(
            padding=20,
            bgcolor=theme.CARD_BG,
            content=ft.Column([
                ft.Text("New Group", size=24, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                ft.Divider(color=theme.DIVIDER_COLOR),
                new_group_name,
                new_group_members,
                ft.Text("You are automatically added as a member.", size=12, color=theme.TEXT_SECONDARY),
                error_text,
                ft.Row([
                    ft.TextButton("Cancel", on_click=close_bottom_sheet, style=ft.ButtonStyle(color=theme.TEXT_SECONDARY)),
                    PrimaryButton("Create", create_new_group, width=150)
                ], alignment=ft.MainAxisAlignment.END)
            ], tight=True)
        ),
        open=False
    )

    def open_create_sheet(e):
        # Clear previous inputs
        new_group_name.value = ""
        new_group_members.value = ""
        error_text.value = ""
        create_group_sheet.open = True
        page.update()

    db.close()

    return ft.View(
        "/groups",
        [
            app_bar("SplitJourney", page),
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        section_title("Your Groups"),
                        ft.IconButton("add_circle", icon_color=theme.PRIMARY_COLOR, on_click=open_create_sheet, tooltip="New Group")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    group_list
                ]),
                padding=theme.PADDING,
                expand=True
            ),
            create_group_sheet
        ],
        bgcolor=theme.PRIMARY_BG,  # Pure white
        floating_action_button=ft.FloatingActionButton(
            icon="add",
            bgcolor=theme.PRIMARY_COLOR,  # Teal
            foreground_color=theme.TEXT_ON_DARK,
            on_click=open_create_sheet
        )
    )
