import ftplib
import os
import sys


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


def get_logfile_from_ftp(dir_name: str, ftp: ftplib.FTP) -> bytes:
    """Returns car logfile from ftp server"""
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
        logfile = b''.join(data)
        ftp.cwd('..')
    except ftplib.all_errors:
        pass # log this
    except ValueError:
        pass # log this (too many or not enough values in list)
    else:
        return logfile


def ftp_connect_and_parse():
    ftp = ftplib.FTP(FTP_HOST)
    log_list = []
    try:
        ftp.connect()
        ftp.login(FTP_LOGIN, FTP_PASSWORD)
        directory_list = get_unparsed_dirs_from_ftp(ftp)
        for dir_name in directory_list:
            log_list.append(get_logfile_from_ftp(dir_name, ftp))
    except ftplib.all_errors:
        pass #log this
    finally:
        ftp.close()

    return log_list


if __name__ == '__main__':
    dirs_list = ftp_connect_and_parse()
    print(sys.getsizeof(dirs_list))
