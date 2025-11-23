"""
Place Search Component.
Provides a reusable place search UI with Google Places autocomplete.
"""
import flet as ft
import theme
from core.places_api import search_places, get_place_details
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def place_search_sheet(page: ft.Page, on_place_selected):
    """
    Creates a bottom sheet with place search functionality.
    
    Args:
        page: Flet page object
        on_place_selected: Callback function(place_data) called when place is selected
                          place_data = {place_id, name, address, latitude, longitude}
    
    Returns:
        ft.BottomSheet: Search bottom sheet component
    """
    search_input = ft.TextField(
        label="Search for a place",
        hint_text="e.g., Starbucks, Olive Garden, hotels near me",
        autofocus=True,
        border_color=theme.PRIMARY_COLOR,
        focused_border_color=theme.PRIMARY_COLOR,
        prefix_icon="search",
        on_change=lambda e: perform_search(e.control.value)
    )
    
    search_results = ft.Column([], spacing=0, scroll=ft.ScrollMode.AUTO, height=400)
    loading_indicator = ft.ProgressRing(visible=False, color=theme.PRIMARY_COLOR, width=30, height=30)
    error_text = ft.Text("", color="#EF4444", size=12, visible=False)
    
    def perform_search(query):
        """Performs place search with debouncing."""
        if not query or len(query) < 3:
            search_results.controls.clear()
            loading_indicator.visible = False
            error_text.visible = False
            page.update()
            return
        
        loading_indicator.visible = True
        error_text.visible = False
        search_results.controls.clear()
        page.update()
        
        try:
            # Search places
            places = search_places(query)
            
            loading_indicator.visible = False
            
            if not places:
                error_text.value = "No places found. Try a different search."
                error_text.visible = True
                page.update()
                return
            
            # Display results
            for place in places:
                def on_select(e, p=place):
                    select_place(p)
                
                search_results.controls.append(
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon("location_on", color=theme.PRIMARY_COLOR),
                            title=ft.Text(
                                place['name'],
                                weight=ft.FontWeight.BOLD,
                                color=theme.TEXT_PRIMARY
                            ),
                            subtitle=ft.Text(
                                place.get('address', 'No address'),
                                color=theme.TEXT_SECONDARY,
                                size=12
                            ),
                            on_click=on_select
                        ),
                        border=ft.border.only(bottom=ft.BorderSide(1, theme.DIVIDER_COLOR))
                    )
                )
            page.update()
            
        except Exception as ex:
            loading_indicator.visible = False
            error_text.value = f"Search error: {str(ex)}"
            error_text.visible = True
            page.update()
    
    def select_place(place):
        """Called when user selects a place from results."""
        print(f"Selected place: {place['name']}")  # Debug
        
        # Show loading
        search_sheet.open = False
        page.update()
        
        page.snack_bar = ft.SnackBar(
            content=ft.Text("Loading place details..."),
            bgcolor=theme.PRIMARY_COLOR
        )
        page.snack_bar.open = True
        page.update()
        
        try:
            # Get full place details
            place_details = get_place_details(place['place_id'])
            
            if place_details:
                # Call callback with place data
                on_place_selected(place_details)
                page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"✓ Tagged: {place_details['name']}"),
                    bgcolor=theme.PRIMARY_COLOR
                )
                page.snack_bar.open = True
            else:
                page.snack_bar = ft.SnackBar(
                    content=ft.Text("Error getting place details"),
                    bgcolor="#EF4444"
                )
                page.snack_bar.open = True
            page.update()
            
        except Exception as ex:
            print(f"Error getting place details: {ex}")
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Error: {str(ex)}"),
                bgcolor="#EF4444"
            )
            page.snack_bar.open = True
            page.update()
    
    # Bottom sheet
    search_sheet = ft.BottomSheet(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        "Tag a Place",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=theme.TEXT_PRIMARY
                    ),
                    ft.IconButton(
                        icon="close",
                        on_click=lambda _: close_sheet(),
                        icon_color=theme.TEXT_SECONDARY
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Container(height=10),
                search_input,
                ft.Container(height=10),
                ft.Row([loading_indicator], alignment=ft.MainAxisAlignment.CENTER),
                error_text,
                search_results
            ], tight=True, spacing=10),
            padding=20
        ),
        open=False
    )
    
    def close_sheet():
        """Closes the search sheet."""
        search_sheet.open = False
        search_input.value = ""
        search_results.controls.clear()
        error_text.visible = False
        loading_indicator.visible = False
        page.update()
    
    return search_sheet


def place_display_card(place_tag, on_remove=None, on_view_maps=None):
    """
    Creates a compact card displaying a tagged place.
    
    Args:
        place_tag: PlaceTag object or dict with name, address
        on_remove: Optional callback when remove button clicked
        on_view_maps: Optional callback when "View in Maps" clicked
        
    Returns:
        ft.Container: Place display card
    """
    place_name = place_tag.name if hasattr(place_tag, 'name') else place_tag.get('name', '')
    place_address = place_tag.address if hasattr(place_tag, 'address') else place_tag.get('address', '')
    
    controls = [
        ft.Row([
            ft.Icon("location_on", color=theme.PRIMARY_COLOR, size=18),
            ft.Column([
                ft.Text(
                    place_name,
                    size=14,
                    weight=ft.FontWeight.W_500,
                    color=theme.PRIMARY_COLOR
                ),
                ft.Text(
                    place_address if place_address else "No address",
                    size=11,
                    color=theme.TEXT_SECONDARY
                ) if place_address else ft.Container()
            ], spacing=2, expand=True)
        ], spacing=8)
    ]
    
    # Action buttons row
    action_buttons = []
    
    if on_view_maps:
        action_buttons.append(
            ft.TextButton(
                "View in Maps",
                icon="map",
                on_click=lambda _: on_view_maps(),
                style=ft.ButtonStyle(color=theme.PRIMARY_COLOR)
            )
        )
    
    if on_remove:
        action_buttons.append(
            ft.TextButton(
                "Remove",
                icon="close",
                on_click=lambda _: on_remove(),
                style=ft.ButtonStyle(color="#EF4444")
            )
        )
    
    if action_buttons:
        controls.append(
            ft.Row(action_buttons, spacing=5)
        )
    
    return ft.Container(
        content=ft.Column(controls, spacing=8),
        padding=12,
        bgcolor="#E0F7F7",
        border_radius=theme.BORDER_RADIUS,
        border=ft.border.all(1, "#B2DFDB")
    )
