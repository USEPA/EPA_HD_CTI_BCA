"""
cti_bca_tool.tool_postproc.py

This is the post-processing module of the tool. It really just generates output folders and paths.

"""


# def create_output_paths(settings):
#     """
#
#     Parameters::
#         settings: The SetInputs class.
#
#     Returns:
#         Output paths into which to save outputs of the given run.
#
#     """
#     settings.path_outputs.mkdir(exist_ok=True)
#     path_of_run_folder = settings.path_outputs / f'{settings.start_time_readable}_{settings.run_folder_identifier}'
#     path_of_run_folder.mkdir(exist_ok=False)
#     path_of_run_inputs_folder = path_of_run_folder / 'run_inputs'
#     path_of_run_inputs_folder.mkdir(exist_ok=False)
#     path_of_run_results_folder = path_of_run_folder / 'run_results'
#     path_of_run_results_folder.mkdir(exist_ok=False)
#     path_of_modified_inputs_folder = path_of_run_folder / 'modified_inputs'
#     path_of_modified_inputs_folder.mkdir(exist_ok=False)
#     path_of_code_folder = path_of_run_folder / 'code'
#     path_of_code_folder.mkdir(exist_ok=False)
#
#     return path_of_run_folder, path_of_run_inputs_folder, path_of_run_results_folder, path_of_modified_inputs_folder, path_of_code_folder
