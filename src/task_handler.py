from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.kampus import Course

from threading import Thread
from multiprocessing import Process
import os

from src.downloader import download_all_in_course
from src.configuration import Config
from src.db_handler import DB
from src import logger


def start_tasks(courses: list[Course]) -> None:

    if os.name == "nt": # true is debug only
        logger.warning("Windows işletim sistemi tespit edildi. Program tek çekirdek üzerinde çalışacak.")
        thread_launcher(courses, Config.get_settings_tuple())
    else:
        if Config.core_count > len(courses):
            Config.core_count = len(courses)
            logger.info(
                f"İhtiyaç duyulandan daha fazla çekirdek verildi. Çekirdek sayısı {len(courses)}'a düşürüldü"
            )

        core_list: list[Process] = list()

        fragment_length = len(courses) // Config.core_count

        for i in range(Config.core_count):
            fragmented_list: list
            if i == Config.core_count - 1:
                fragmented_list = courses[fragment_length * i :]
            else:
                fragmented_list = courses[fragment_length * i : fragment_length * (i + 1)]

            settings = Config.get_settings_tuple()

            core = Process(
                target=thread_launcher,
                args=(fragmented_list, settings),
            )
            core.start()
            core_list.append(core)

        for core in core_list:
            core.join()

# Launches a thread for each course in Ninova
def thread_launcher(courses: list[Course], settings) -> None:
    Config.load_from_tuple(settings)
    proc_list: list[Thread] = []
    for course in courses:
        session_copy = Config.get_session_copy()
        proc = Thread(
            target=download_all_in_course,
            args=(session_copy, course),
        )
        proc.start()
        proc_list.append(proc)

    for proc in proc_list:
        proc.join()