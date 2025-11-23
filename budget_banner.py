"""
Budget Banner Component.
Displays group budget with progress bar and alert notifications.
"""
import flet as ft
import time
import theme
from core.db import SessionLocal
from core.logic import get_budget_status, update_group_budget
from ui.components import InputField, PrimaryButton

def budget_banner(page: ft.Page, group_id: int):
    """
    Creates a budget banner showing spending progress and alerts.
    
    Args:
        page: Flet page object
        group_id: ID of the group
        
    Returns:
        ft.Container: Budget banner with progress bar and alerts
    """
    db = SessionLocal()
    status = get_budget_status(db, group_id)
    db.close()
    
    # Budget input for bottom sheet
    budget_input = ft.TextField(
        label="Budget Amount (Rs.)",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        border_color=theme.PRIMARY_COLOR,
        focused_border_color=theme.PRIMARY_COLOR
    )
    error_text = ft.Text("", color="#EF4444", size=12)
    
    def save_budget(e):
        """Saves the budget amount."""
        print(f"Save budget clicked, value: {budget_input.value}")  # Debug
        try:
            if not budget_input.value or budget_input.value.strip() == "":
                error_text.value = "Please enter a budget amount"
                page.update()
                return
                
            amount = float(budget_input.value)
            if amount <= 0:
                error_text.value = "Budget must be greater than 0"
                page.update()
                return
                
            action_db = SessionLocal()
            update_group_budget(action_db, group_id, amount)
            action_db.close()
            
            print(f"Budget updated to {amount}")  # Debug
            
            # Close the bottom sheet first
            budget_sheet.open = False
            page.update()
            
            # Show success message
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"✓ Budget set to Rs.{amount:.2f}!"),
                bgcolor=theme.PRIMARY_COLOR
            )
            page.snack_bar.open = True
            page.update()
            
            # Force refresh by navigating to the same route
            time.sleep(0.3)  # Small delay for snackbar to show
            page.go(f"/groups/{group_id}")
            
        except ValueError as ex:
            print(f"ValueError: {ex}")  # Debug
            error_text.value = "Please enter a valid number"
            page.update()
        except Exception as ex:
            print(f"Error: {ex}")  # Debug
            error_text.value = f"Error: {str(ex)}"
            page.update()
    
    # Bottom sheet for budget entry
    budget_sheet = ft.BottomSheet(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Set Group Budget", size=20, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                ft.Container(height=10),
                budget_input,
                error_text,
                ft.Container(height=20),
                ft.Row([
                    ft.TextButton(
                        "Cancel",
                        on_click=lambda _: page.close(budget_sheet)
                    ),
                    ft.ElevatedButton(
                        "Save Budget",
                        on_click=save_budget,
                        bgcolor=theme.PRIMARY_COLOR,
                        color=theme.TEXT_ON_DARK,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=8)
                        )
                    )
                ], alignment=ft.MainAxisAlignment.END, spacing=10)
            ], tight=True, spacing=10),
            padding=20
        ),
        open=False
    )
    
    def open_budget_sheet(e):
        """Opens the budget entry bottom sheet."""
        print("Opening budget sheet...")  # Debug
        budget_input.value = str(status['budget_amount']) if status['budget_amount'] else ""
        error_text.value = ""
        page.open(budget_sheet)
        page.update()
    
    # Build banner content
    if not status['budget_amount']:
        # No budget set - show simplified banner
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Icon("account_balance_wallet", color=theme.TEXT_SECONDARY, size=24),
                    ft.Text("No budget set", size=14, color=theme.TEXT_SECONDARY),
                ], spacing=10),
                ft.ElevatedButton(
                    "Set Budget",
                    icon="add",
                    on_click=open_budget_sheet,
                    bgcolor=theme.PRIMARY_COLOR,
                    color=theme.TEXT_ON_DARK,
                    height=40,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=8)
                    )
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=16,
            bgcolor=theme.CARD_BG,
            border_radius=theme.BORDER_RADIUS,
            border=ft.border.all(1, theme.DIVIDER_COLOR)
        )
    
    # Build progress bar
    percentage = status['percentage_used']
    progress_value = min(percentage / 100, 1.0)  # ProgressBar expects 0.0 to 1.0
    
    progress_color = theme.PRIMARY_COLOR
    if status['percentage_used'] >= 100:
        progress_color = "#E53935"  # Red
    elif status['percentage_used'] >= 80:
        progress_color = "#FF9800"  # Orange
    
    progress_bar = ft.ProgressBar(
        value=progress_value,
        width=None,  # Full width
        height=12,
        color=progress_color,
        bgcolor="#E0E0E0",
        border_radius=6
    )
    
    # Build alert chips
    alert_chips = []
    for alert in status['alerts']:
        chip_color = "#FF9800"  # Orange
        if "exceeded" in alert.lower():
            chip_color = "#E53935"  # Red
        
        alert_chips.append(
            ft.Container(
                content=ft.Text(
                    alert,
                    size=12,
                    color="white",
                    weight=ft.FontWeight.W_500
                ),
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                bgcolor=chip_color,
                border_radius=16
            )
        )
    
    return ft.Container(
        content=ft.Column([
            # Header row
            ft.Row([
                ft.Text("Group Budget", size=16, weight=ft.FontWeight.BOLD, color=theme.TEXT_PRIMARY),
                ft.IconButton(
                    icon="edit",
                    icon_size=18,
                    icon_color=theme.PRIMARY_COLOR,
                    tooltip="Edit Budget",
                    on_click=open_budget_sheet
                )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Budget amount row
            ft.Row([
                ft.Column([
                    ft.Text(
                        f"Rs.{status['total_spent']:.2f} / Rs.{status['budget_amount']:.2f}",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=theme.PRIMARY_COLOR
                    ),
                    ft.Text(
                        f"Used {status['percentage_used']:.1f}% of budget",
                        size=12,
                        color=theme.TEXT_SECONDARY
                    )
                ], spacing=2)
            ]),
            
            # Progress bar
            ft.Container(height=8),
            progress_bar,
            
            # Alert chips
            ft.Container(height=8) if alert_chips else ft.Container(),
            ft.Row(alert_chips, spacing=8, wrap=True) if alert_chips else ft.Container()
            
        ], spacing=8),
        padding=16,
        bgcolor=theme.CARD_BG,
        border_radius=theme.BORDER_RADIUS,
        border=ft.border.all(1, theme.DIVIDER_COLOR)
    )
