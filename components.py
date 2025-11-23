"""
Reusable UI components for SplitJourney.
Implements the complete brand design system with teal accents and white surfaces.
"""
import flet as ft
import theme

def app_bar(title: str, page, show_back: bool = False):
    """
    Creates a branded app bar with logo and gradient background.
    
    Args:
        title (str): Title text (not displayed, logo used instead)
        page (ft.Page): The Flet page object for navigation
        show_back (bool): Whether to show a back button
    
    Returns:
        ft.Container: Styled app bar with deep teal background
    """
    from core.auth import logout
    
    leading = None
    if show_back:
        leading = ft.IconButton(
            icon="arrow_back",
            icon_color=theme.TEXT_ON_DARK,
            on_click=lambda _: page.go("/groups"),
            tooltip="Back"
        )
    
    # Logo and title (use title parameter for group names)
    logo_and_name = ft.Row([
        ft.Image(
            src="assets/logo.png",
            width=36,
            height=36,
            fit=ft.ImageFit.CONTAIN
        ),
        ft.Text(
            title,  # Use the title parameter
            size=20,
            color=theme.TEXT_ON_DARK,
            weight=ft.FontWeight.W_600
        )
    ], spacing=10, alignment=ft.MainAxisAlignment.START)
    
    return ft.Container(
        content=ft.Row([
            leading if leading else ft.Container(width=48),
            logo_and_name,
            ft.IconButton(
                icon="logout",
                icon_color=theme.TEXT_ON_DARK,
                on_click=lambda _: (logout(), page.go("/login")),
                tooltip="Logout"
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        bgcolor=theme.DARK_TEAL,  # Deep teal header
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        height=64
    )

def section_title(text: str):
    """
    Creates a styled section title.
    
    Args:
        text (str): The title text to display
    
    Returns:
        ft.Text: Styled text widget for section headers
    """
    return ft.Text(
        text,
        size=theme.SUBHEAD_SIZE,
        weight=ft.FontWeight.BOLD,
        color=theme.TEXT_PRIMARY
    )

def PrimaryButton(text: str, on_click, width: float = 200):
    """
    Creates a teal accent button.
    
    Args:
        text (str): Button label text
        on_click (callable): Click handler function
        width (float): Button width in pixels
    
    Returns:
        ft.ElevatedButton: Styled button with teal background
    """
    return ft.ElevatedButton(
        text=text,
        on_click=on_click,
        bgcolor=theme.PRIMARY_COLOR,  # Teal base
        color=theme.TEXT_ON_DARK,
        width=width,
        height=48,
        elevation=2,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=theme.BORDER_RADIUS),
            shadow_color=theme.PRIMARY_COLOR,
        )
    )

def InputField(label: str, password: bool = False, value: str = ""):
    """
    Creates a text input field with soft white background and teal focus ring.
    
    Args:
        label (str): Field label/placeholder text
        password (bool): Whether to obscure input text
        value (str): Initial field value
    
    Returns:
        ft.TextField: Styled text input widget
    """
    return ft.TextField(
        label=label,
        password=password,
        value=value,
        border_radius=theme.BORDER_RADIUS,
        border_color=theme.DIVIDER_COLOR,
        focused_border_color=theme.FOCUS_RING,  # Teal focus ring
        text_size=theme.BODY_SIZE,
        color=theme.TEXT_PRIMARY,
        label_style=ft.TextStyle(color=theme.TEXT_SECONDARY),
        height=56,
        bgcolor=theme.INPUT_BG,  # Soft white
        filled=True
    )

def Card(content, on_click=None):
    """
    Creates a white card with soft shadow.
    
    Args:
        content: The content to display in the card
        on_click (callable): Optional click handler
    
    Returns:
        ft.Card: Styled card container
    """
    return ft.Card(
        content=ft.Container(
            content=content,
            padding=16,
            on_click=on_click
        ),
        color=theme.CARD_BG,  # Pure white
        elevation=theme.CARD_ELEVATION,
        surface_tint_color=theme.PRIMARY_COLOR
    )
