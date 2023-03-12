import datetime
import ftplib
import logging
import os
import time
from typing import Generator

from django.conf import settings
from django.utils import timezone

from dzllogparser.services.parser import (defenition_logfile_data,
                                          get_date_from_timestamp_str)
from dzllogparser.services.db import import_logfile_data_into_db, RecordsStatus


ftp_logger = logging.getLogger(__name__)


def get_unparsed_dirs_from_ftp(ftp: ftplib.FTP) -> list[str]:
    """Returns unparsed directory list from ftp server"""
    try:
        with open(settings.IGNOREFILE, 'r') as file:
            ignore_dirs_list = [dir_name.strip() for dir_name in file]
    except FileNotFoundError:
        ignore_dirs_list = []
        ftp_logger.info(f'File {settings.IGNOREFILE} is not found.')
    ftp_directory_list = ftp.nlst()
    unparsed_dirs_list = [
        dir_name for dir_name in ftp_directory_list
        if dir_name.isdigit() and dir_name not in ignore_dirs_list
    ]
    return unparsed_dirs_list


def get_logfile_from_ftp(dir_name: str, ftp: ftplib.FTP) -> list[str]:
    """Returns list with car logfile strings from ftp server"""
    try:
        ftp.cwd('/' + dir_name)
        logfiles_list = [
            filename for filename in ftp.nlst()
            if filename.find(settings.CAR_LOGFILE_PREFIX) >= 0
        ]
        logfile_name, = logfiles_list
        data = []
        ftp.retrbinary('RETR ' + logfile_name,
                       callback=lambda x: data.append(x))
        logfile = b''.join(data)
    except ftplib.all_errors as exception:
        ftp_logger.error(f'FTP Error: {exception}.')
        # raise
    except ValueError:
        ftp_logger.warning(f'Log file search error in directory {dir_name}')
    else:
        return logfile.decode('utf-8').split('\r\n')
    return []


def get_logfiles_generator(ftp: ftplib.FTP) -> Generator[tuple[str, list],
                                                         None, None]:
    """Returns Generator with tuples(directory_name, bytes)"""
    if settings.DAYS_LIMIT:
        limit_date = timezone.now().date() - datetime.timedelta(
            days=settings.DAYS_LIMIT)
        directory_list_to_work = [
            dir_name_str for dir_name_str in get_unparsed_dirs_from_ftp(ftp)
            if get_date_from_timestamp_str(dir_name_str) > limit_date
        ]
    else:
        directory_list_to_work = get_unparsed_dirs_from_ftp(ftp)
    logfiles = (
        (dir_name, get_logfile_from_ftp(dir_name, ftp))
        for dir_name in directory_list_to_work
    )
    return logfiles


def get_summary_result(common_result: RecordsStatus,
                       current_result: RecordsStatus) -> None:
    """Summarizes class attributes RecordStatus."""
    for attr in common_result.__dict__.keys():
        common_result_attr = getattr(common_result, attr)
        setattr(common_result, attr,
                common_result_attr + getattr(current_result, attr))


def get_updates_from_ftp() -> RecordsStatus:
    """Get logfiles data from ftp server."""
    ftp = ftplib.FTP(settings.FTP_HOST)
    log_list = []
    result = RecordsStatus()
    start_time = time.monotonic()
    try:
        ftp.connect()
        ftp.login(settings.FTP_LOGIN, settings.FTP_PASSWORD)
        for dir_name, file_strings in get_logfiles_generator(ftp):
            logfile_data = defenition_logfile_data(dir_name, file_strings)
            current_result = import_logfile_data_into_db(logfile_data,
                                                         settings.DAYS_LIMIT)
            get_summary_result(result, current_result)
            with open(settings.IGNOREFILE, 'a') as ignorefile:
                ignorefile.write(dir_name + '\n')
    except ftplib.all_errors as exception:
        ftp_logger.error(f'FTP Error: {exception}.')
        # raise
    finally:
        ftp.close()
    result.elapsed_time = round(time.monotonic() - start_time, 3)
    return result
