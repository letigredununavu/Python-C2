import logging
from colorama import Fore, Style


class Logger:

    def __init__(self, verbosity: str = "info"):

        """
        Initializing the logger with a specified verbosity level

        :param verbosity: Logging level ('debug', 'info', 'warning', 'error', 'critical')
        """
        self.logger = logging.getLogger("CustomLogger")
        self.logger.setLevel(self._get_log_level(verbosity))

        # Avoid adding multiple handlers
        if not self.logger.hasHandlers():
            # Configure Logging format
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S")

            # Create a console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)

            self.logger.addHandler(console_handler)


    def _get_log_level(self, verbosity:str):
        """
        Convert verbosity string to logging level
        """

        levels = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }

        return levels.get(verbosity.lower(), logging.INFO)
    

    def debug(self, message:str):
        """Log a debug message with color."""
        self.logger.debug(Fore.BLUE + message + Style.RESET_ALL)


    def info(self, message: str):
        """Log an info message with color."""
        self.logger.info(Fore.GREEN + message + Style.RESET_ALL)


    def warning(self, message: str):
        """Log a warning message with color."""
        self.logger.warning(Fore.YELLOW + message + Style.RESET_ALL)


    def error(self, message: str):
        """Log an error message with color."""
        self.logger.error(Fore.RED + message + Style.RESET_ALL)


    def critical(self, message: str):
        """Log a critical message with color."""
        self.logger.critical(Fore.MAGENTA + message + Style.RESET_ALL)

