from pathlib import Path
from tkinter import *
from tkinter import filedialog


def select_folder(prompt):
    """

    Args:
        prompt: The message to be displayed in the top bar of the dialog window.

    Returns:
        The user selected folder.

    """
    root = Tk()
    root.withdraw()
    path_here = Path(__file__).parent
    root.directory = filedialog.askdirectory(initialdir=path_here, title='Select ' + prompt)
    folder_name = Path(root.directory) # this converts the string from above to a pathlib Path
    root.destroy()
    root.quit()
    return folder_name


def get_folder(message):
    """

    Args:
        message: The message to be displayed in the terminal or console window.

    Returns:
        The user selected folder.

    """
    print('\nRequesting ' + message)
    folder_requested = select_folder(message)
    return folder_requested


if __name__ == '__main__':
    path_inputs = get_folder('folder containing input files for the run')
    print(path_inputs)
