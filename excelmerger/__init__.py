from version import __version__


def main():
    from excelmerger.app import main as gui_main

    return gui_main()

__all__ = ["__version__", "main"]
