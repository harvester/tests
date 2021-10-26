from robot.api.deco import keyword


@keyword("Paste String From Clipboard")
def paste():
    try:
        from pyperclip import paste  # Narrow down the dependency
    except ImportError as e:
        raise ImportError("3rd party Library `pyperclip` is required"
                          " before using this keyword.") from e
    else:
        return paste()
