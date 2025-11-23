"""
Group Detail View.
Shows expenses, chat, polls, and balance information for a specific group.
"""
import flet as ft
from ui.components import app_bar, section_title, PrimaryButton
from ui.chat_tab import chat_tab
from ui.polls_tab import polls_tab, create_poll_fab
from ui.budget_banner import budget_banner
import theme
from core.db import SessionLocal
from core.models import Group, GroupMember
from core.logic import calculate_member_balances, simplify_debts, record_settlement, get_expense_place
from core.auth import logout
from core.pdf_export import generate_trip_pdf
import webbrowser
import os
from collections import defaultdict

def group_detail_view(page: ft.Page, group_id: int):
    """
    Renders the details of a specific group with 4 tabs.
    
    Args:
        page (ft.Page): The Flet page object for navigation and updates
        group_id (int): The ID of the group to display
        
    Returns:
        ft.View: The group detail view with Expenses, Chat, Polls, and Balances tabs
    """
    db = SessionLocal()
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        db.close()
        return ft.View("/404", [ft.Text("Group not found")])

    # --- Expenses Tab Content ---
    expenses = group.expenses
    expenses.sort(key=lambda x: x.date, reverse=True)

    # View state
    show_daily_view = False
    expense_display_container = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    
    def build_list_view():
        """Builds traditional list view of expenses."""
        expense_display_container.controls.clear()
        
        for expense in expenses:
            # Get place tag if exists
            place_tag = get_expense_place(db, expense.id)
            
            # Build expense item
            subtitle_text = f"Paid by {expense.payer_member.member_name}"
            
            expense_tile = ft.ListTile(
                leading=ft.Icon("receipt", color=theme.PRIMARY_COLOR),
                title=ft.Text(expense.description, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                subtitle=ft.Text(subtitle_text, color=theme.TEXT_SECONDARY),
                trailing=ft.Text(f"Rs.{expense.amount:.2f}", size=16, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_COLOR),
                on_click=lambda _, e_id=expense.id: page.go(f"/groups/{group_id}/expenses/{e_id}/edit")
            )
            
            # If place is tagged, show it below the expense
            if place_tag:
                def view_in_maps(e, lat=place_tag.latitude, lng=place_tag.longitude):
                    if lat and lng:
                        url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
                        webbrowser.open(url)
                
                expense_display_container.controls.append(expense_tile)
                expense_display_container.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon("location_on", size=14, color=theme.PRIMARY_COLOR),
                            ft.Text(
                                place_tag.name,
                                size=13,
                                color=theme.PRIMARY_COLOR,
                                weight=ft.FontWeight.W_500
                            ),
                            ft.TextButton(
                                "View in Maps",
                                icon="map",
                                icon_size=14,
                                on_click=view_in_maps,
                                style=ft.ButtonStyle(
                                    color=theme.PRIMARY_COLOR,
                                    padding=ft.padding.only(left=8)
                                )
                            ) if place_tag.latitude and place_tag.longitude else ft.Container()
                        ], spacing=5),
                        padding=ft.padding.only(left=56, bottom=8),
                    )
                )
            else:
                expense_display_container.controls.append(expense_tile)
        
        if not expenses:
            expense_display_container.controls.append(
                ft.Container(
                    content=ft.Text("No expenses yet. Add one!", color=theme.TEXT_SECONDARY),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
    
    def build_daily_view():
        """Builds day-wise view of expenses."""
        expense_display_container.controls.clear()
        
        # Group expenses by day
        grouped = defaultdict(list)
        for expense in expenses:
            if expense.date:
                day_key = expense.date.strftime("%Y-%m-%d")
                grouped[day_key].append(expense)
        
        if not grouped:
            expense_display_container.controls.append(
                ft.Container(
                    content=ft.Text("No expenses yet. Add one!", color=theme.TEXT_SECONDARY),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
            return
        
        # Sort by date (descending)
        for day_key in sorted(grouped.keys(), reverse=True):
            day_expenses = grouped[day_key]
            date_obj = day_expenses[0].date
            day_display = date_obj.strftime("%A, %B %d, %Y")
            day_total = sum(exp.amount for exp in day_expenses)
            
            # Day header
            expense_display_container.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("calendar_today", color=theme.PRIMARY_COLOR, size=20),
                            ft.Text(
                                day_display,
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=theme.TEXT_PRIMARY
                            )
                        ], spacing=8),
                        ft.Text(
                            f"Total: Rs. {day_total:,.2f}",
                            size=14,
                            color=theme.TEXT_SECONDARY
                        )
                    ], spacing=4),
                    padding=12,
                    bgcolor=theme.CARD_BG,
                    border_radius=theme.BORDER_RADIUS,
                    border=ft.border.all(2, theme.PRIMARY_COLOR)
                )
            )
            
            # Day's expenses
            for expense in day_expenses:
                place_tag = get_expense_place(db, expense.id)
                time_str = expense.date.strftime("%I:%M %p") if expense.date else ""
                
                expense_tile = ft.ListTile(
                    leading=ft.Icon("receipt", color=theme.PRIMARY_COLOR, size=20),
                    title=ft.Row([
                        ft.Text(time_str, size=11, color=theme.TEXT_SECONDARY, width=70),
                        ft.Text(expense.description, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY)
                    ], spacing=8),
                    subtitle=ft.Text(f"Paid by {expense.payer_member.member_name}", color=theme.TEXT_SECONDARY, size=12),
                    trailing=ft.Text(f"Rs.{expense.amount:.2f}", size=15, weight=ft.FontWeight.BOLD, color=theme.PRIMARY_COLOR),
                    on_click=lambda _, e_id=expense.id: page.go(f"/groups/{group_id}/expenses/{e_id}/edit")
                )
                
                if place_tag:
                    def view_in_maps(e, lat=place_tag.latitude, lng=place_tag.longitude):
                        if lat and lng:
                            webbrowser.open(f"https://www.google.com/maps/search/?api=1&query={lat},{lng}")
                    
                    expense_display_container.controls.append(expense_tile)
                    expense_display_container.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon("location_on", size=14, color=theme.PRIMARY_COLOR),
                                ft.Text(place_tag.name, size=12, color=theme.PRIMARY_COLOR),
                                ft.TextButton(
                                    "Maps",
                                    icon="map",
                                    icon_size=12,
                                    on_click=view_in_maps,
                                    style=ft.ButtonStyle(color=theme.PRIMARY_COLOR, padding=ft.padding.only(left=5))
                                ) if place_tag.latitude and place_tag.longitude else ft.Container()
                            ], spacing=5),
                            padding=ft.padding.only(left=56, bottom=8)
                        )
                    )
                else:
                    expense_display_container.controls.append(expense_tile)
            
            # Add spacing after each day
            expense_display_container.controls.append(ft.Container(height=10))
    
    def toggle_view(e):
        """Toggles between list and daily view."""
        nonlocal show_daily_view
        show_daily_view = e.control.value
        if show_daily_view:
            build_daily_view()
        else:
            build_list_view()
        page.update()
    
    def download_pdf(e):
        """Generates and downloads trip PDF."""
        try:
            # Show loading
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Generating PDF..."),
                bgcolor=theme.PRIMARY_COLOR
            )
            page.snack_bar.open = True
            page.update()
            
            # Prepare data
            balances = calculate_member_balances(db, group_id)
            settlements = simplify_debts(balances)
            
            # Get place tags
            place_tags = {}
            for expense in expenses:
                tag = get_expense_place(db, expense.id)
                if tag:
                    place_tags[expense.id] = tag
            
            # Generate PDF
            os.makedirs("downloads", exist_ok=True)
            filename = f"{group.name.replace(' ', '_')}_trip_report.pdf"
            filepath = os.path.abspath(os.path.join("downloads", filename))
            
            generate_trip_pdf(group, expenses, balances, settlements, place_tags, filepath)
            
            # Open PDF (Works on web if downloads is mounted as assets)
            page.launch_url(f"/{filename}")
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✓ PDF saved to downloads/{filename}"),
                bgcolor=theme.PRIMARY_COLOR
            )
            page.snack_bar.open = True
            page.update()
            
        except Exception as ex:
            print(f"PDF generation error: {ex}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error generating PDF: {str(ex)}"),
                bgcolor="#EF4444"
            )
            page.snack_bar.open = True
            page.update()
    
    # Build initial view
    build_list_view()

    # Toggle and PDF button row
    view_controls = ft.Row([
        ft.Row([
            ft.Text("List", size=13, color=theme.TEXT_SECONDARY),
            ft.Switch(
                value=False,
                active_color=theme.PRIMARY_COLOR,
                on_change=toggle_view
            ),
            ft.Text("Daily", size=13, color=theme.TEXT_SECONDARY)
        ], spacing=5),
        ft.ElevatedButton(
            "Download PDF",
            icon="picture_as_pdf",
            on_click=download_pdf,
            bgcolor=theme.PRIMARY_COLOR,
            color=theme.TEXT_ON_DARK,
            height=36
        )
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    expenses_tab_content = ft.Container(
        content=ft.Column([
            view_controls,
            ft.Divider(height=20, color="transparent"),
            expense_display_container
        ]),
        padding=theme.PADDING
    )

    # --- Balances Tab Content ---
    balances = calculate_member_balances(db, group_id)
    simplified_debts = simplify_debts(balances)
    
    balance_list = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
    
    # Show net balances
    balance_list.controls.append(section_title("Net Balances"))
    for member in group.members:
        net = balances.get(member.id, 0)
        color = "#10B981" if net > 0 else "#EF4444" if net < 0 else theme.TEXT_SECONDARY
        text = f"Should receive Rs.{net:.2f}" if net > 0 else f"Should pay Rs.{abs(net):.2f}" if net < 0 else "Settled"
        
        balance_list.controls.append(
            ft.ListTile(
                title=ft.Text(member.member_name, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                trailing=ft.Text(text, color=color, weight=ft.FontWeight.BOLD)
            )
        )
        
    balance_list.controls.append(ft.Divider(color=theme.DIVIDER_COLOR))
    
    # Show simplified debts with settlement buttons
    balance_list.controls.append(section_title("Settlement Plan"))
    
    if not simplified_debts:
        balance_list.controls.append(
            ft.Container(
                content=ft.Text("✓ All settled - No debts to pay!", color="#10B981", weight=ft.FontWeight.W_500),
                padding=10
            )
        )
    else:
        # Map IDs to names for display
        member_map = {m.id: m.member_name for m in group.members}
        
        for payer_id, receiver_id, amount in simplified_debts:
            payer_name = member_map.get(payer_id, "Unknown")
            receiver_name = member_map.get(receiver_id, "Unknown")
            
            def on_record_payment(e, p_id=payer_id, r_id=receiver_id, amt=amount):
                action_db = SessionLocal()
                try:
                    record_settlement(action_db, group_id, p_id, r_id, amt)
                    page.snack_bar = ft.SnackBar(ft.Text(f"✓ Payment recorded: {member_map[p_id]} paid Rs.{amt:.2f}"))
                    page.snack_bar.open = True
                    page.go(f"/groups/{group_id}")
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"))
                    page.snack_bar.open = True
                finally:
                    action_db.close()
                page.update()
            
            balance_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"{payer_name}", weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY, size=14),
                            ft.Icon("arrow_forward", color=theme.TEXT_SECONDARY, size=16),
                            ft.Text(f"{receiver_name}", weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY, size=14),
                        ], spacing=8),
                        ft.Row([
                            ft.Text(
                                f"Rs.{amount:.2f}",
                                color=theme.PRIMARY_COLOR,
                                weight=ft.FontWeight.BOLD,
                                size=18
                            ),
                            ft.ElevatedButton(
                                "Record Payment",
                                on_click=on_record_payment,
                                bgcolor=theme.PRIMARY_COLOR,
                                color=theme.TEXT_ON_DARK,
                                height=36,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                )
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ], spacing=8),
                    padding=16,
                    bgcolor="#E0F7F7",
                    border_radius=theme.BORDER_RADIUS,
                    border=ft.border.all(1, "#B2DFDB"),
                    margin=ft.margin.only(bottom=8)
                )
            )

    balances_tab_content = ft.Container(
        content=balance_list,
        padding=theme.PADDING
    )

    db.close()

    # Create tabs
    tabs_control = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="Expenses", content=expenses_tab_content),
            ft.Tab(text="Chat", content=chat_tab(page, group_id)),
            ft.Tab(text="Polls", content=polls_tab(page, group_id)),
            ft.Tab(text="Balances", content=balances_tab_content),
        ],
        expand=True,
        indicator_color=theme.PRIMARY_COLOR,
        label_color=theme.PRIMARY_COLOR,
        unselected_label_color=theme.TEXT_SECONDARY
    )

    # FAB changes based on selected tab
    fab_ref = ft.Ref[ft.FloatingActionButton]()
    
    def on_tab_change(e):
        """Changes FAB based on selected tab."""
        if e.control.selected_index == 0:  # Expenses
            fab_ref.current.visible = True
            fab_ref.current.icon = "add"
            fab_ref.current.on_click = lambda _: page.go(f"/groups/{group_id}/expenses/new")
        elif e.control.selected_index == 1:  # Chat
            fab_ref.current.visible = False
        elif e.control.selected_index == 2:  # Polls
            fab_ref.current.visible = True
            fab_ref.current.icon = "add"
            fab_ref.current.on_click = lambda _: page.go(f"/groups/{group_id}/polls/new")
        elif e.control.selected_index == 3:  # Balances
            fab_ref.current.visible = False
        page.update()
    
    tabs_control.on_change = on_tab_change

    return ft.View(
        f"/groups/{group_id}",
        [
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon="arrow_back",
                        icon_color=theme.TEXT_ON_DARK,
                        on_click=lambda _: page.go("/groups"),
                        tooltip="Back"
                    ),
                    ft.Row([
                        ft.Image(
                           src="assets/logo.png",
                            width=36,
                            height=36,
                            fit=ft.ImageFit.CONTAIN
                        ),
                        ft.Text(
                            group.name,
                            size=20,
                            color=theme.TEXT_ON_DARK,
                            weight=ft.FontWeight.W_600
                        )
                    ], spacing=10),
                    ft.Row([
                        ft.IconButton(
                            icon="group",
                            icon_color=theme.TEXT_ON_DARK,
                            tooltip="Manage Members",
                            on_click=lambda _: page.go(f"/groups/{group_id}/members")
                        ),
                        ft.IconButton(
                            icon="logout",
                            icon_color=theme.TEXT_ON_DARK,
                            on_click=lambda _: (page.client_storage.remove("user_id"), logout(), page.go("/login")),
                            tooltip="Logout"
                        )
                    ])
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=theme.DARK_TEAL,
                padding=ft.padding.symmetric(horizontal=12, vertical=10),
                height=64
            ),
            ft.Container(
                content=budget_banner(page, group_id),
                padding=ft.padding.only(left=16, right=16, top=12, bottom=8)
            ),
            tabs_control
        ],
        bgcolor=theme.PRIMARY_BG,
        floating_action_button=ft.FloatingActionButton(
            ref=fab_ref,
            icon="add",
            bgcolor=theme.PRIMARY_COLOR,
            foreground_color=theme.TEXT_ON_DARK,
            on_click=lambda _: page.go(f"/groups/{group_id}/expenses/new")
        )
    )
