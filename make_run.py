import os, json, argparse
from copy_functions import copy, copy_job_file, copy_files_from_folder
from writing import add_execution_batch, write_bash_script, change_job_label

#ap = argparse.ArgumentParser()
#ap.add_argument('-c', '--config', required=True, help='path to json file with configurations')



# USER SETTINGS
RUN_FOLDER_PATH = '/scratch/sawrz/CUC'
RUN_FOLDER_NAME = 'run_'
start_run_number = 25
end_run_number = 30
job_type = 'tron'
force_field = 'amber14sb_OL15.ff'
job_queueing_system = 'slurm'
start_job_file_name = 'run.job'
restart_job_file_name = 'rerun.job'
start_bash_script_name = 'run_jobs.sh'
restart_bash_script_name = 'rerun_jobs.sh'


# locations/paths of files
FILES_LOCATION = 'create_run'
FORCE_FIELD_LOCATION = os.path.join(FILES_LOCATION, 'ff')
JOB_FILES_LOCATION = os.path.join(FILES_LOCATION, 'job_files')
START_JOB_FILES_LOCATION = os.path.join(JOB_FILES_LOCATION, 'start')
RESTART_JOB_FILES_LOCATION = os.path.join(JOB_FILES_LOCATION, 'restart')
SYSTEMS_LOCATION = os.path.join(FILES_LOCATION, 'systems')

# set choosing options to build run
FORCE_FIELD_TYPES = tuple(os.listdir(FORCE_FIELD_LOCATION))
JOB_FILE_TYPES = tuple(os.listdir(START_JOB_FILES_LOCATION))
SYSTEM_TYPES = tuple(os.listdir(SYSTEMS_LOCATION))

# check if input is right
if force_field not in FORCE_FIELD_TYPES:
    msg = 'Unknown force field. You can choose between the following options: {types}'.format(types=FORCE_FIELD_TYPES)
    raise Exception(msg)

if job_type not in JOB_FILE_TYPES:
    msg = 'Unknown job file type. You can choose between the following options: {types}'.format(types=JOB_FILE_TYPES)
    raise Exception(msg)

# set copy paths
FORCE_FIELD_PATH = os.path.join(FORCE_FIELD_LOCATION, force_field)
START_JOB_FILE_PATH = os.path.join(START_JOB_FILES_LOCATION, job_type)
RESTART_JOB_FILE_PATH = os.path.join(RESTART_JOB_FILES_LOCATION, job_type)
SYSTEM_PATHS = tuple([os.path.join(SYSTEMS_LOCATION, system_type) for system_type in SYSTEM_TYPES])

# creating tuple with all system files
SYSTEM_PATH_FILES = []
for system_path in SYSTEM_PATHS:
    files = os.listdir(system_path)
    file_dirs = tuple([os.path.join(system_path, file) for file in files])
    SYSTEM_PATH_FILES.append(file_dirs)
SYSTEM_PATH_FILES = tuple(SYSTEM_PATH_FILES)

# create folder for runs
if not os.path.exists(RUN_FOLDER_PATH):
    os.makedirs(RUN_FOLDER_PATH)

# create list for execution script
start_bash_script_lines = []
restart_bash_script_lines = []

# create and populate run folders
for run_number in range(start_run_number, end_run_number+1):

    # create run folder
    run_name = '{base_name}{number:03d}'.format(base_name=RUN_FOLDER_NAME, number=run_number)
    dir_name = os.path.join(RUN_FOLDER_PATH, run_name)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    for system_type, system_source_file_paths in zip(SYSTEM_TYPES, SYSTEM_PATH_FILES):
        system_destination_path = os.path.join(dir_name, system_type)

        # make sure system type and folder are the same
        if os.path.basename(system_destination_path) != system_type:
            raise Exception('Mixed Systems. Script needs debugging!')

        # create folder for system type
        if not os.path.exists(system_destination_path):
            os.makedirs(system_destination_path)

        # copy force field into directory
        force_field_destination_path = os.path.join(system_destination_path, force_field)
        copy(src=FORCE_FIELD_PATH, dest=force_field_destination_path)

        # copy job files into directory
        copy_job_file(src=START_JOB_FILE_PATH, dest=system_destination_path,
                      job_type=job_type, new_name=start_job_file_name)
        copy_job_file(src=RESTART_JOB_FILE_PATH, dest=system_destination_path,
                      job_type=job_type, new_name=restart_job_file_name)

        # relabel job files
        job_path = os.path.join(system_destination_path, start_job_file_name)
        change_job_label(file_path=job_path, queueing_system=job_queueing_system,
                         system_type=system_type, run_number=run_number)

        job_path = os.path.join(system_destination_path, restart_job_file_name)
        change_job_label(file_path=job_path, queueing_system=job_queueing_system,
                         system_type=system_type, run_number=run_number)

        # copy simulation data
        copy_files_from_folder(system_source_file_paths, dest=system_destination_path)

        # append run commands for bash script
        execution_path = os.path.relpath(system_destination_path, start=RUN_FOLDER_PATH)

        add_execution_batch(folder=execution_path,
                            job_file=start_job_file_name,
                            queue_system=job_queueing_system,
                            bash_list=start_bash_script_lines)

        add_execution_batch(folder=execution_path,
                            job_file=restart_job_file_name,
                            queue_system=job_queueing_system,
                            bash_list=restart_bash_script_lines)

script_path = os.path.join(RUN_FOLDER_PATH, start_bash_script_name)
write_bash_script(script_path, start_bash_script_lines)

script_path = os.path.join(RUN_FOLDER_PATH, restart_bash_script_name)
write_bash_script(script_path, restart_bash_script_lines)
