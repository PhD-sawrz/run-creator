import argparse
import json
import os
from types import SimpleNamespace

from copy_functions import copy, copy_job_file, copy_files_from_folder
from writing import add_execution_batch, write_bash_script, change_job_label

# ARGUMENT INTERFACE
ap = argparse.ArgumentParser()
ap.add_argument('-c', '--config', required=True, help='path to json file with configurations')
ap.add_argument('-s', '--start', required=False, default=1, help='start number of first run')
ap.add_argument('-e', '--end', required=True, help='last number of generated runs')
args = ap.parse_args()

# DEFAULT SETTINGS
config = dict(run_folder_path=None,
              run_folder_name='run_',
              start_run_number=int(args.start),
              end_run_number=int(args.end),
              job_type=None,
              force_field=None,
              job_queueing_system=None,
              simulation_framework='GROMACS',
              max_gpus=2,
              start_job_file_name='run.job',
              restart_job_file_name='rerun.job',
              start_bash_script_name='run_jobs.sh',
              restart_bash_script_name='rerun_jobs.sh')

# OVERWRITE DEFAULT SETTINGS
with open(args.config) as file:
    config.update(json.load(file))
    config['max_gpus'] = int(config['max_gpus'])

# TRANSLATE SETTINGS TO VARIABLES
name_space = SimpleNamespace(**config)

# CHECK FOR MISSING CONFIGURATION PARAMETERS
if name_space.run_folder_path is None:
    raise Exception('Please specify the path to store all runs.')
if name_space.job_type is None:
    raise Exception('Please specify the job type. You will find those in the job_files folder.')
if name_space.force_field is None:
    raise Exception('Please specify the force field. You will find those in the ff folder.')
if name_space.job_queueing_system is None:
    raise Exception('Please specify the hjob queuing system of your job type.')

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
if name_space.force_field not in FORCE_FIELD_TYPES:
    msg = 'Unknown force field. You can choose between the following options: {types}. You can add new ones.'.format(
        types=FORCE_FIELD_TYPES)
    raise Exception(msg)

if name_space.job_type not in JOB_FILE_TYPES:
    msg = 'Unknown job file type. You can choose between the following options: {types} You can add new ones.'.format(
        types=JOB_FILE_TYPES)
    raise Exception(msg)

# set copy paths
FORCE_FIELD_PATH = os.path.join(FORCE_FIELD_LOCATION, name_space.force_field)
START_JOB_FILE_PATH = os.path.join(START_JOB_FILES_LOCATION, name_space.job_type)
RESTART_JOB_FILE_PATH = os.path.join(RESTART_JOB_FILES_LOCATION, name_space.job_type)
SYSTEM_PATHS = tuple([os.path.join(SYSTEMS_LOCATION, system_type) for system_type in SYSTEM_TYPES])

# creating tuple with all system files
SYSTEM_PATH_FILES = []
for system_path in SYSTEM_PATHS:
    files = os.listdir(system_path)
    file_dirs = tuple([os.path.join(system_path, file) for file in files])
    SYSTEM_PATH_FILES.append(file_dirs)
SYSTEM_PATH_FILES = tuple(SYSTEM_PATH_FILES)

# create folder for runs
if not os.path.exists(name_space.run_folder_path):
    os.makedirs(name_space.run_folder_path)

# create list for execution script
start_bash_script_lines = []
restart_bash_script_lines = []

# create and populate run folders
for run_number in range(name_space.start_run_number, name_space.end_run_number + 1):

    # create run folder
    run_name = '{base_name}{number:03d}'.format(base_name=name_space.run_folder_name, number=run_number)
    dir_name = os.path.join(name_space.run_folder_path, run_name)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    for system_id, (system_type, system_source_file_paths) in enumerate(zip(SYSTEM_TYPES, SYSTEM_PATH_FILES)):
        system_destination_path = os.path.join(dir_name, system_type)

        # make sure system type and folder are the same
        if os.path.basename(system_destination_path) != system_type:
            raise Exception('Mixed Systems. Script needs debugging!')

        # create folder for system type
        if not os.path.exists(system_destination_path):
            os.makedirs(system_destination_path)

        # copy force field into directory
        force_field_destination_path = os.path.join(system_destination_path, name_space.force_field)
        copy(src=FORCE_FIELD_PATH, dest=force_field_destination_path)

        # copy job files into directory
        gpu_id = system_id % name_space.max_gpus

        copy_job_file(src=START_JOB_FILE_PATH, dest=system_destination_path,
                      job_type=name_space.job_type, new_name=name_space.start_job_file_name,
                      simulation_framework=name_space.simulation_framework, gpu_id=gpu_id)
        copy_job_file(src=RESTART_JOB_FILE_PATH, dest=system_destination_path,
                      job_type=name_space.job_type, new_name=name_space.restart_job_file_name,
                      simulation_framework=name_space.simulation_framework, gpu_id=gpu_id)

        # relabel job files
        job_path = os.path.join(system_destination_path, name_space.start_job_file_name)
        change_job_label(file_path=job_path, queueing_system=name_space.job_queueing_system,
                         system_type=system_type, run_number=run_number)

        job_path = os.path.join(system_destination_path, name_space.restart_job_file_name)
        change_job_label(file_path=job_path, queueing_system=name_space.job_queueing_system,
                         system_type=system_type, run_number=run_number)

        # copy simulation data
        copy_files_from_folder(system_source_file_paths, dest=system_destination_path)

        # append run commands for bash script
        execution_path = os.path.relpath(system_destination_path, start=name_space.run_folder_path)

        add_execution_batch(folder=execution_path,
                            job_file=name_space.start_job_file_name,
                            queue_system=name_space.job_queueing_system,
                            bash_list=start_bash_script_lines)

        add_execution_batch(folder=execution_path,
                            job_file=name_space.restart_job_file_name,
                            queue_system=name_space.job_queueing_system,
                            bash_list=restart_bash_script_lines)

script_path = os.path.join(name_space.run_folder_path, name_space.start_bash_script_name)
write_bash_script(script_path, start_bash_script_lines)

script_path = os.path.join(name_space.run_folder_path, name_space.restart_bash_script_name)
write_bash_script(script_path, restart_bash_script_lines)
