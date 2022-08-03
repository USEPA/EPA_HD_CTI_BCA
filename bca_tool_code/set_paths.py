from pathlib import Path
import shutil


class SetPaths:
    """

    The SetPaths class sets the paths and run_id info used by the tool.

    """
    def __init__(self):
        self.path_code = Path(__file__).parent
        self.path_project = self.path_code.parent
        self.path_inputs = self.path_project / 'inputs'
        self.path_outputs = self.path_project / 'outputs'
        self.path_test = self.path_project / 'test'

    def files_in_code_folder(self):
        """

        This is just a generator that allows for copy/paste of tool code into a bundle of folders and files saved to the outputs folder.

        Returns:
            A generator object.

        """
        files_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_file())

        return files_in_path_code

    def copy_code_to_destination(self, destination):
        """

        This is just a generator that allows for copy/paste of tool code into a bundle of folders and files saved to the outputs folder.

        Parameters:
            destination: Path; the destination folder; destination folder must exist prior to method call.

        Returns:
            Nothing, but copies contents of code folder to the destination.

        """
        # first copy files in the path_code folder
        files_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_file())
        for file in files_in_path_code:
            shutil.copy2(file, destination / file.name)

        # now make subfolders in destination and copy files from path_code subfolders
        dirs_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_dir())
        for d in dirs_in_path_code:
            source_dir_name = Path(d).name
            destination_subdir = destination / source_dir_name
            destination_subdir.mkdir(exist_ok=False)
            files_in_source_dir = (entry for entry in d.iterdir() if entry.is_file())
            for file in files_in_source_dir:
                shutil.copy2(file, destination_subdir / file.name)

        return

    @staticmethod
    def run_id():
        """

        This method allows for a user-interactive identifier (name) for the given run.

        Returns:
            A console prompt to enter a run identifier; entering "test" sends outputs to a test folder; if left blank a
            default name is used.

        """
        # set run id and files to generate
        run_folder_identifier = input('\nProvide a run identifier for your output folder name (press return to use the default name)\n')
        run_folder_identifier = run_folder_identifier if run_folder_identifier != '' else 'HD2027-Costs'
        return run_folder_identifier

    def create_output_paths(self, start_time_readable, run_id):
        """

        Parameters::
            start_time_readable: str; the start time of the run, in text readable format.\n
            run_id: str; the run ID entered by the user or the default value if the user does not provide an ID.

        Returns:
            Output paths into which to save outputs of the given run.

        """
        self.path_outputs.mkdir(exist_ok=True)
        path_of_run_folder = self.path_outputs / f'{start_time_readable}_{run_id}'
        path_of_run_folder.mkdir(exist_ok=False)
        path_of_run_inputs_folder = path_of_run_folder / 'run_inputs'
        path_of_run_inputs_folder.mkdir(exist_ok=False)
        path_of_run_results_folder = path_of_run_folder / 'run_results'
        path_of_run_results_folder.mkdir(exist_ok=False)
        path_of_modified_inputs_folder = path_of_run_folder / 'modified_inputs'
        path_of_modified_inputs_folder.mkdir(exist_ok=False)
        path_of_code_folder = path_of_run_folder / 'code'
        path_of_code_folder.mkdir(exist_ok=False)

        return path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder
