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


@keyword("Set Default Browser Download Path")
def default_download(dest: str = "") -> str:
    if dest == "":
        from pathlib import Path
        from robot.libraries.BuiltIn import BuiltIn
        b = BuiltIn()
        p = Path(b.get_variable_value("${OUTPUT FILE}"))
        dest = p.parent / (p.stem + '-downloads')
        dest.mkdir(parents=True)
        b.set_global_variable("${BROWSER_DOWNLOAD_PATH}", dest)
        b.log(f"Default download path changed: {dest}", "debug")
    return dest
