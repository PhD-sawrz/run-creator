import numpy as np


def add_execution_batch(folder, job_file, queue_system, bash_list):
    # change directory
    command = 'cd {folder}\n'.format(folder=folder)
    bash_list.append(command)

    # submit job
    if queue_system.lower() == 'slurm':
        command = 'sleep $((RANDOM%10))\n'
        bash_list.append(command)

        command = 'sbatch {job_file}\n'.format(job_file=job_file)
    else:
        command = './{job_file}\n'.format(job_file=job_file)
    bash_list.append(command)

    # go one dir-level back
    command = 'cd ../..\n'
    bash_list.append(command)

    # enter another paragraph
    bash_list.append('\n')


def write_bash_script(file_name, command_list):
    with open(file_name, 'w') as script:
        for command in command_list:
            script.write(command)


def edit_gromacs_job_file(job_file, gpu_id):
    with open(job_file, 'r') as file:
        content = file.readlines()

    parameter = '-gpu_id'
    for line_number, line in enumerate(content):
        if parameter in line:
            line = np.array(line.split(' '))

            index = np.where(line == parameter)[0][0]
            line[index + 1] = str(gpu_id)

            content[line_number] = ' '.join(line)

    with open(job_file, 'w') as file:
        file.writelines(content)


def change_job_label(file_path, queueing_system, run_number, system_type):
    with open(file_path, 'r') as file:
        content = file.readlines()

    if queueing_system.lower() == 'slurm':
        key_word = '#SBATCH --job-name='
    elif queueing_system.lower() == 'tsp':
        key_word = 'label='
    else:
        raise Exception('Unknown queing system')

    for line_number, line in enumerate(content):
        if key_word in line:
            new_line = '{key_word}{run_number:03d}_{system_type}\n'.format(
                run_number=run_number, system_type=system_type,
                key_word=key_word)
            content[line_number] = new_line

    with open(file_path, 'w') as file:
        file.writelines(content)
