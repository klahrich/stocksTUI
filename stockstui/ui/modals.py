from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual.app import on

# FIX: Changed 'from common import ...' to an absolute import from the package root.
from stockstui.common import NotEmpty
from stockstui.utils import slugify

class ConfirmDeleteModal(ModalScreen[bool]):
    """A modal dialog for confirming a deletion, optionally requiring text input for confirmation."""
    def __init__(self, item_name: str, prompt: str, require_typing: bool = False) -> None:
        """
        Args:
            item_name: The name of the item being deleted (used for confirmation typing).
            prompt: The message displayed to the user.
            require_typing: If True, the user must type `item_name` to enable the delete button.
        """
        super().__init__()
        self.item_name = item_name
        self.prompt_text = prompt
        self.require_typing = require_typing

    def compose(self) -> ComposeResult:
        """Creates the layout for the confirmation modal."""
        with Vertical(id="dialog"):
            yield Label(self.prompt_text)
            if self.require_typing:
                yield Input(placeholder=self.item_name, id="confirmation_input")
            with Horizontal(id="dialog-buttons"):
                yield Button("Delete", variant="error", id="delete", disabled=self.require_typing)
                yield Button("Cancel", id="cancel")

    @on(Input.Changed, "#confirmation_input")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Enables/disables the delete button based on confirmation input."""
        self.query_one("#delete", Button).disabled = event.value != self.item_name

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Dismisses the modal, returning True if delete was pressed, False otherwise."""
        self.dismiss(event.button.id == "delete")

class EditListModal(ModalScreen[str | None]):
    """A modal dialog for editing the name of an existing list."""
    def __init__(self, current_name: str) -> None:
        """
        Args:
            current_name: The current name of the list being edited.
        """
        super().__init__()
        self.current_name = current_name

    def compose(self) -> ComposeResult:
        """Creates the layout for the edit list modal."""
        with Vertical(id="dialog"):
            yield Label("Enter new list name:")
            yield Input(value=self.current_name, id="list-name-input", validators=[NotEmpty()])
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Sets focus to the input field when the modal is mounted."""
        self.query_one(Input).focus()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button presses, dismissing the modal with the new name or None."""
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        input_widget = self.query_one(Input)
        if event.button.id == "save" and input_widget.validate(input_widget.value).is_valid:
            self.dismiss(slugify(input_widget.value))

class AddListModal(ModalScreen[str | None]):
    """A modal dialog for adding a new list."""
    def compose(self) -> ComposeResult:
        """Creates the layout for the add list modal."""
        with Vertical(id="dialog"):
            yield Label("Enter new list name (e.g., 'crypto'):")
            yield Input(placeholder="List Name", id="list-name-input", validators=[NotEmpty()])
            with Horizontal(id="dialog-buttons"):
                yield Button("Add", variant="primary", id="add")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Sets focus to the input field when the modal is mounted."""
        self.query_one(Input).focus()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button presses, dismissing the modal with the new name or None."""
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        input_widget = self.query_one(Input)
        if event.button.id == "add" and input_widget.validate(input_widget.value).is_valid:
            self.dismiss(slugify(input_widget.value))

class AddTickerModal(ModalScreen[tuple[str, str, str] | None]):
    """A modal dialog for adding a new ticker to a list."""
    def compose(self) -> ComposeResult:
        """Creates the layout for the add ticker modal."""
        with Vertical(id="dialog"):
            yield Label("Enter new ticker, alias, and note:")
            yield Input(placeholder="Ticker (e.g., AAPL)", id="ticker-input", validators=[NotEmpty()])
            yield Input(placeholder="Alias (optional, e.g., Apple)", id="alias-input")
            yield Input(placeholder="Note (optional, e.g., Personal reminder)", id="note-input")
            with Horizontal(id="dialog-buttons"):
                yield Button("Add", variant="primary", id="add")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Sets focus to the ticker input field when the modal is mounted."""
        self.query_one("#ticker-input").focus()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button presses, dismissing the modal with ticker details or None."""
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        ticker_input = self.query_one("#ticker-input", Input)
        if event.button.id == "add" and ticker_input.validate(ticker_input.value).is_valid:
            ticker = ticker_input.value.strip().upper()
            alias = self.query_one("#alias-input").value.strip() or ticker # Default alias to ticker if empty
            note = self.query_one("#note-input").value.strip()
            self.dismiss((ticker, alias, note))

class EditTickerModal(ModalScreen[tuple[str, str, str] | None]):
    """A modal dialog for editing an existing ticker's details."""
    def __init__(self, ticker: str, alias: str, note: str) -> None:
        """
        Args:
            ticker: The current ticker symbol.
            alias: The current alias for the ticker.
            note: The current note for the ticker.
        """
        super().__init__()
        self.ticker = ticker
        self.alias = alias
        self.note = note

    def compose(self) -> ComposeResult:
        """Creates the layout for the edit ticker modal."""
        with Vertical(id="dialog"):
            yield Label("Edit ticker, alias, and note:")
            yield Input(value=self.ticker, id="ticker-input", validators=[NotEmpty()])
            yield Input(value=self.alias, id="alias-input")
            yield Input(value=self.note, id="note-input")
            with Horizontal(id="dialog-buttons"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Sets focus to the ticker input field when the modal is mounted."""
        self.query_one("#ticker-input").focus()

    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button presses, dismissing the modal with updated ticker details or None."""
        if event.button.id == "cancel":
            self.dismiss(None)
            return
        ticker_input = self.query_one("#ticker-input", Input)
        if event.button.id == "save" and ticker_input.validate(ticker_input.value).is_valid:
            ticker = ticker_input.value.strip().upper()
            alias = self.query_one("#alias-input").value.strip() or ticker # Default alias to ticker if empty
            note = self.query_one("#note-input").value.strip()
            self.dismiss((ticker, alias, note))

class CompareInfoModal(ModalScreen[str | None]):
    """A modal dialog to get a ticker symbol for the info comparison debug test."""
    def compose(self) -> ComposeResult:
        """Creates the layout for the compare info modal."""
        with Vertical(id="dialog"):
            yield Label("Enter ticker symbol to compare info:")
            yield Input(placeholder="e.g., AAPL", id="ticker-input", validators=[NotEmpty()])
            with Horizontal(id="dialog-buttons"):
                yield Button("Run Test", variant="primary", id="run")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Sets focus to the input field when the modal is mounted."""
        self.query_one(Input).focus()

    def _submit(self) -> None:
        """Validates the input and dismisses the modal with the uppercase ticker symbol."""
        ticker_input = self.query_one("#ticker-input", Input)
        if ticker_input.validate(ticker_input.value).is_valid:
            self.dismiss(ticker_input.value.strip().upper())
            
    @on(Button.Pressed)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handles button presses (Run Test or Cancel)."""
        if event.button.id == "cancel":
            self.dismiss(None)
        elif event.button.id == "run":
            self._submit()

    @on(Input.Submitted, "#ticker-input")
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handles input submission (Enter key), triggering the submit logic."""
        self._submit()