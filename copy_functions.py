import os
import shutil, errno


def copy(src, dest):
    try:
        shutil.copytree(src, dest)
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
        else:
            print('Directory not copied. Error: %s' % e)


def copy_job_file(src, dest, job_type, new_name):
    # copy job file into directory
    copy(src, dest)

    # rename job_file
    old_job_name = os.path.join(dest, job_type)
    new_job_name = os.path.join(dest, new_name)
    os.rename(old_job_name, new_job_name)


def copy_files_from_folder(file_src, dest):
    for file_path in file_src:
        copy(src=file_path, dest=dest)
