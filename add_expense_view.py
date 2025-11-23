"""
Add Expense View.
Allows adding a new expense to a group with various split types.
"""
import flet as ft
from ui.components import app_bar, PrimaryButton, InputField, section_title
from ui.place_search import place_search_sheet, place_display_card
import theme
from core.db import SessionLocal
from core.models import Group
from core.logic import create_expense, tag_place_to_expense
from datetime import datetime

def add_expense_view(page: ft.Page, group_id: int):
    """
    Renders the form to add a new expense to a group.
    
    Args:
        page (ft.Page): The Flet page object for navigation and updates
        group_id (int): The ID of the group to add the expense to
        
    Returns:
        ft.View: The add expense view with dynamic split configuration
        
    Behavior:
        - Supports four split types: Equal, Unequal, Percentage, Shares
        - Equal: Shows checkboxes to select which members to include
        - Unequal: Shows amount inputs for each member
        - Percentage: Shows percentage inputs (must total 100%)
        - Shares: Shows share inputs (distributed proportionally)
        - Validates all inputs before saving
        - Creates expense and splits in database
        - Navigates back to group detail on success
    """
    """
    Renders the form to add an expense.
    """
    db = SessionLocal()
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        db.close()
        return ft.View("/404", [ft.Text("Group not found")])
        
    members = group.members
    member_options = [ft.dropdown.Option(key=str(m.id), text=m.member_name) for m in members]
    
    # Form Fields
    description_input = InputField("Description (e.g. Dinner)")
    amount_input = InputField("Amount")
    
    payer_dropdown = ft.Dropdown(
        label="Paid By",
        options=member_options,
        border_radius=theme.BORDER_RADIUS,
        border_color=theme.PRIMARY_COLOR,
        text_size=theme.BODY_SIZE,
        value=str(members[0].id) if members else None
    )
    
    split_type_dropdown = ft.Dropdown(
        label="Split Type",
        options=[
            ft.dropdown.Option("Equal"),
            ft.dropdown.Option("Unequal"),
            ft.dropdown.Option("Percentage"),
            ft.dropdown.Option("Shares"),
        ],
        value="Equal",
        border_radius=theme.BORDER_RADIUS,
        border_color=theme.PRIMARY_COLOR,
    )
    
    # Place tagging state
    selected_place = None
    place_display_container = ft.Column([], spacing=10)
    
    def on_place_selected(place_data):
        """Called when user selects a place from search."""
        nonlocal selected_place
        selected_place = place_data
        update_place_display()
    
    def remove_place():
        """Removes the selected place."""
        nonlocal selected_place
        selected_place = None
        update_place_display()
    
    def update_place_display():
        """Updates the place display UI."""
        place_display_container.controls.clear()
        if selected_place:
            place_display_container.controls.append(
                place_display_card(selected_place, on_remove=remove_place)
            )
        page.update()
    
    # Create place search bottom sheet
    place_sheet = place_search_sheet(page, on_place_selected)
    
    def open_place_search(e):
        """Opens the place search bottom sheet."""
        page.open(place_sheet)
        page.update()
    
    # Dynamic Split Inputs Container
    split_inputs_container = ft.Column()
    split_input_controls = {} # Map member_id -> Control
    
    def update_split_inputs(e):
        split_type = split_type_dropdown.value
        split_inputs_container.controls.clear()
        split_input_controls.clear()
        
        if split_type == "Equal":
            # Show checkboxes to select which members to include
            split_inputs_container.controls.append(
                ft.Text("Select members to split equally:", color=theme.TEXT_SECONDARY, size=12)
            )
            for member in members:
                checkbox = ft.Checkbox(
                    label=member.member_name,
                    value=True,
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
                field = InputField(f"{member.member_name} - {label_suffix}")
                split_input_controls[member.id] = field
                split_inputs_container.controls.append(field)
                
        page.update()

    split_type_dropdown.on_change = update_split_inputs
    # Initialize default
    update_split_inputs(None)
    
    error_text = ft.Text("", color=theme.ERROR_COLOR)

    def on_submit(e):
        try:
            amount = float(amount_input.value)
        except ValueError:
            error_text.value = "Invalid total amount"
            page.update()
            return

        if not description_input.value:
            error_text.value = "Please enter a description"
            page.update()
            return
            
        payer_id = int(payer_dropdown.value)
        split_type = split_type_dropdown.value
        
        split_data = {}
        
        # Validation based on split type
        if split_type == "Equal":
            # Collect selected members from checkboxes
            selected_count = 0
            for m_id, control in split_input_controls.items():
                if hasattr(control, 'value') and control.value:  # Checkbox checked
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
        
        # Save
        action_db = SessionLocal()
        try:
            expense = create_expense(
                action_db, 
                group_id, 
                payer_id, 
                description_input.value, 
                amount, 
                datetime.utcnow(), 
                split_type, 
                split_data
            )
            
            # Tag place if selected
            if selected_place:
                try:
                    tag_place_to_expense(action_db, expense.id, selected_place)
                except Exception as place_ex:
                    print(f"Error tagging place: {place_ex}")
            
            page.go(f"/groups/{group_id}")
            page.snack_bar = ft.SnackBar(ft.Text("Expense added!"))
            page.snack_bar.open = True
            page.update()
            
        except Exception as ex:
            error_text.value = f"Error: {str(ex)}"
            page.update()
        finally:
            action_db.close()

    return ft.View(
        f"/groups/{group_id}/expenses/new",
        [
            app_bar("Add Expense", page, show_back=True),
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
                    ft.Divider(),
                    ft.Row([
                        section_title("Location (Optional)"),
                        ft.TextButton(
                            "Tag Place",
                            icon="add_location",
                            on_click=open_place_search,
                            style=ft.ButtonStyle(color=theme.PRIMARY_COLOR)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    place_display_container,
                    error_text,
                    ft.Divider(height=20, color="transparent"),
                    PrimaryButton("Save Expense", on_submit, width=float("inf"))
                ], scroll=ft.ScrollMode.AUTO),
                padding=theme.PADDING,
                expand=True
            )
        ],
        bgcolor=theme.PRIMARY_BG
    )
