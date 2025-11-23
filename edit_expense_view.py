"""
Edit Expense View.
Allows editing or deleting an existing expense.
"""
import flet as ft
from ui.components import app_bar, PrimaryButton, InputField, section_title
import theme
from core.db import SessionLocal
from core.models import Expense
from core.logic import update_expense, delete_expense
from datetime import datetime

def edit_expense_view(page: ft.Page, group_id: int, expense_id: int):
    """
    Renders the form to edit an existing expense.
    
    Args:
        page (ft.Page): The Flet page object for navigation and updates
        group_id (int): The ID of the group the expense belongs to
        expense_id (int): The ID of the expense to edit
        
    Returns:
        ft.View: The edit expense view with pre-populated fields
        
    Behavior:
        - Pre-populates form with existing expense data
        - Allows editing description, amount, payer, and splits
        - Supports all four split types like add expense view
        - Provides "Delete" button with confirmation dialog
        - Updates expense in database on save
        - Navigates back to group detail on success or deletion
    """
    """
    Renders the form to edit an expense.
    """
    db = SessionLocal()
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    
    if not expense:
        db.close()
        return ft.View("/404", [ft.Text("Expense not found")])
    
    group = expense.group
    members = group.members
    member_options = [ft.dropdown.Option(key=str(m.id), text=m.member_name) for m in members]
    
    # Pre-populate form fields
    description_input = InputField("Description", value=expense.description)
    amount_input = InputField("Amount", value=str(expense.amount))
    
    payer_dropdown = ft.Dropdown(
        label="Paid By",
        options=member_options,
        value=str(expense.payer_member_id),
        border_radius=theme.BORDER_RADIUS,
        border_color=theme.PRIMARY_COLOR,
    )
    
    # Determine current split type by analyzing existing splits
    splits_map = {split.member_id: split.amount_owed for split in expense.splits}
    current_split_type = "Equal"  # Default assumption
    
    split_type_dropdown = ft.Dropdown(
        label="Split Type",
        options=[
            ft.dropdown.Option("Equal"),
            ft.dropdown.Option("Unequal"),
            ft.dropdown.Option("Percentage"),
            ft.dropdown.Option("Shares"),
        ],
        value=current_split_type,
        border_radius=theme.BORDER_RADIUS,
        border_color=theme.PRIMARY_COLOR,
    )
    
    split_inputs_container = ft.Column()
    split_input_controls = {}
    
    def update_split_inputs(e):
        split_type = split_type_dropdown.value
        split_inputs_container.controls.clear()
        split_input_controls.clear()
        
        if split_type == "Equal":
            split_inputs_container.controls.append(
                ft.Text("Select members to split equally:", color=theme.TEXT_SECONDARY, size=12)
            )
            for member in members:
                # Check if this member has a split in the original expense
                is_included = member.id in splits_map
                checkbox = ft.Checkbox(
                    label=member.member_name,
                    value=is_included,
                    active_color=theme.PRIMARY_COLOR
                )
                split_input_controls[member.id] = checkbox
                split_inputs_container.controls.append(checkbox)
        else:
            label_suffix = ""
            if split_type == "Unequal": label_suffix = "Amount (Rs.)"
            elif split_type == "Percentage": label_suffix = "%"
            elif split_type == "Shares": label_suffix = "Shares"
            
            for member in members:
                initial_value = str(splits_map.get(member.id, 0))
                field = InputField(f"{member.member_name} - {label_suffix}", value=initial_value)
                split_input_controls[member.id] = field
                split_inputs_container.controls.append(field)
                
        page.update()

    split_type_dropdown.on_change = update_split_inputs
    update_split_inputs(None)
    
    error_text = ft.Text("", color=theme.ERROR_COLOR)

    def on_save(e):
        try:
            amount = float(amount_input.value)
        except ValueError:
            error_text.value = "Invalid amount"
            page.update()
            return

        if not description_input.value:
            error_text.value = "Please enter a description"
            page.update()
            return
            
        payer_id = int(payer_dropdown.value)
        split_type = split_type_dropdown.value
        
        split_data = {}
        
        if split_type == "Equal":
            selected_count = 0
            for m_id, control in split_input_controls.items():
                if hasattr(control, 'value') and control.value:
                    split_data[m_id] = True
                    selected_count += 1
                else:
                    split_data[m_id] = False
            
            if selected_count == 0:
                error_text.value = "Please select at least one member"
                page.update()
                return
                
        elif split_type != "Equal":
            total_entered = 0
            for m_id, control in split_input_controls.items():
                try:
                    val = float(control.value or 0)
                    split_data[m_id] = val
                    total_entered += val
                except ValueError:
                    error_text.value = f"Invalid value for member"
                    page.update()
                    return
            
            if split_type == "Unequal":
                if abs(total_entered - amount) > 0.1:
                    error_text.value = f"Total split ({total_entered}) does not match expense amount ({amount})"
                    page.update()
                    return
            elif split_type == "Percentage":
                if abs(total_entered - 100) > 0.1:
                    error_text.value = f"Total percentage ({total_entered}) must be 100%"
                    page.update()
                    return
        
        action_db = SessionLocal()
        try:
            update_expense(
                action_db,
                expense_id,
                description_input.value,
                amount,
                payer_id,
                split_type,
                split_data
            )
            page.go(f"/groups/{group_id}")
            page.snack_bar = ft.SnackBar(ft.Text("Expense updated!"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            error_text.value = f"Error: {str(ex)}"
            page.update()
        finally:
            action_db.close()

    def on_delete(e):
        def confirm_delete(e):
            action_db = SessionLocal()
            delete_expense(action_db, expense_id)
            action_db.close()
            delete_dialog.open = False
            page.go(f"/groups/{group_id}")
            page.snack_bar = ft.SnackBar(ft.Text("Expense deleted!"))
            page.snack_bar.open = True
            page.update()
        
        def cancel_delete(e):
            delete_dialog.open = False
            page.update()
        
        delete_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete Expense?"),
            content=ft.Text("Are you sure you want to delete this expense? This action cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel_delete),
                ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=theme.ERROR_COLOR)),
            ],
        )
        page.dialog = delete_dialog
        delete_dialog.open = True
        page.update()

    db.close()

    return ft.View(
        f"/groups/{group_id}/expenses/{expense_id}/edit",
        [
            app_bar("Edit Expense", page, show_back=True),
            ft.Container(
                content=ft.Column([
                    description_input,
                    amount_input,
                    ft.Divider(height=10, color="transparent"),
                    payer_dropdown,
                    ft.Divider(height=10, color="transparent"),
                    split_type_dropdown,
                    ft.Divider(),
                    section_title("Split Details"),
                    split_inputs_container,
                    error_text,
                    ft.Divider(height=20, color="transparent"),
                    ft.Row([
                        ft.TextButton("Delete", on_click=on_delete, style=ft.ButtonStyle(color=theme.ERROR_COLOR)),
                        PrimaryButton("Save Changes", on_save, width=200)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], scroll=ft.ScrollMode.AUTO),
                padding=theme.PADDING,
                expand=True
            )
        ],
        bgcolor=theme.PRIMARY_BG
    )
