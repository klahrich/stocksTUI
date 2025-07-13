import logging
import threading
from textual.app import App

class TextualHandler(logging.Handler):
    """
    A custom logging handler that forwards records to a Textual app's notification system.
    This allows any module in the application to send user-facing notifications
    using the standard logging library.
    """

    def __init__(self, app: App):
        """
        Initializes the handler.

        Args:
            app: The Textual App instance to which notifications will be sent.
        """
        super().__init__()
        self.app = app
        # Store the main thread's identifier to know when we can call app.notify directly.
        self._main_thread_id = threading.main_thread().ident

    def emit(self, record: logging.LogRecord):
        """
        Processes a log record and displays it as a notification in the Textual app.

        This method is thread-safe. It checks if it's being called from the main
        application thread or a worker thread and calls the appropriate Textual method.
        """
        try:
            # Format the message using the handler's formatter
            message = self.format(record)
            
            # Map logging levels to notification severities
            severity = "information"
            if record.levelno >= logging.ERROR:
                severity = "error"
            elif record.levelno >= logging.WARNING:
                severity = "warning"
            
            # FIX: The logging handler can be called from both the main thread (e.g., during
            # on_unmount) and worker threads. We must use `app.notify` directly if on the main
            # thread, and `app.call_from_thread` if on a worker thread.
            if threading.current_thread().ident == self._main_thread_id:
                # We are on the main thread, call notify directly.
                self.app.notify(
                    message,
                    title=record.levelname.capitalize(),
                    severity=severity,
                    timeout=8
                )
            else:
                # We are on a worker thread, must use call_from_thread.
                self.app.call_from_thread(
                    self.app.notify,
                    message,
                    title=record.levelname.capitalize(),
                    severity=severity,
                    timeout=8
                )
        except Exception:
            self.handleError(record)