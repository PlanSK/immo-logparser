import ftplib
import os
from typing import Generator
from parser import defenition_logfile_data


FTP_HOST = os.getenv('FTP_HOST')
FTP_LOGIN = os.getenv('FTP_LOGIN')
FTP_PASSWORD = os.getenv('FTP_PASSWORD')

CAR_LOGFILE_PREFIX = 'ImmobilizerLog'
IGNOREFILE = 'ignore_dirs.log'


def get_unparsed_dirs_from_ftp(ftp: ftplib.FTP) -> list[str]:
    """Returns unparsed directory list from ftp server"""
    try:
        with open(IGNOREFILE, 'r') as file:
            ignore_dirs_list = [dir_name.strip() for dir_name in file]
    except FileNotFoundError:
        ignore_dirs_list = []
        pass # log this
    ftp_directory_list = ftp.nlst()
    unparsed_dirs_list = [
        dir_name for dir_name in ftp_directory_list
        if dir_name.isdigit() and dir_name not in ignore_dirs_list
    ]
    return unparsed_dirs_list


def get_logfile_from_ftp(dir_name: str, ftp: ftplib.FTP) -> list[str]:
    """Returns list with car logfile strings from ftp server"""
    try:
        ftp.cwd(dir_name)
        logfiles_list = [
            filename for filename in ftp.nlst()
            if filename.find(CAR_LOGFILE_PREFIX) >= 0
        ]
        logfile_name, = logfiles_list
        data = []
        ftp.retrbinary('RETR ' + logfile_name,
                       callback=lambda x: data.append(x))
        ftp.cwd('..')
        logfile = b''.join(data)
    except ftplib.all_errors:
        pass # log this
    except ValueError:
        pass # log this (too many or not enough values in list)
    else:
        return logfile.decode('utf-8').split('\r\n')
    # default return


def get_logfiles_generator(ftp: ftplib.FTP) -> Generator[tuple[str, list],
                                                         None, None]:
    """Returns Generator with tuples(directory_name, bytes)"""
    directory_list = get_unparsed_dirs_from_ftp(ftp)
    logfiles = (
        (dir_name, get_logfile_from_ftp(dir_name, ftp))
        for dir_name in directory_list
    )
    return logfiles


if __name__ == '__main__':
    ftp = ftplib.FTP(FTP_HOST)
    log_list = []
    try:
        ftp.connect()
        ftp.login(FTP_LOGIN, FTP_PASSWORD)
        for dir_name, file_strings in get_logfiles_generator(ftp):
            logfile_data = defenition_logfile_data(dir_name, file_strings)
            print(logfile_data)
            # import data to db
            with open(IGNOREFILE, 'a') as ignorefile:
                ignorefile.write(dir_name + '\n')
    except ftplib.all_errors:
        pass #log this
    finally:
        ftp.close()
