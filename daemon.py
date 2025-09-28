import os
import sys
import time
import logging
import subprocess

from project import Project
import common

import pyrage


logger = logger = logging.getLogger(__name__)


class DaemonError(Exception):
    pass


class Daemon:
    def __init__(self, config_path):
        self.config_path = config_path
        try:
            self.config = common.read_config(self.config_path)
        except FileNotFoundError:
            cwd = os.getcwd()
            raise DaemonError(f"Configuration file '{self.config_path}' not found", 1)

    def find_project_dirs(self, base_dirs):
        project_dirs = []
        for base_dir in base_dirs:
            base_dir = os.path.expanduser(base_dir)
            logger.info("Finding directories containing .lockdown.conf files under %s", base_dir)
            for subdir, dirs, files in os.walk(base_dir):
                if ".lockdown.conf" in files:
                    project_dirs.append(subdir)

        return project_dirs

    def load_projects(self, project_dirs):
        projects = {}
        for project_dir in project_dirs:
            lockdown_conf_path = os.path.join(project_dir, ".lockdown.conf")
            logger.debug("Loading project from '%s'", lockdown_conf_path)
            try:
                project = Project(lockdown_conf_path)
            except Exception as err:
                logger.error("Invalid .lockdown.conf file '%s': %s", lockdown_conf_path, err)
                continue
            projects[project_dir] = project

        return projects

    def run(self):
        projects = self.load_projects(self.find_project_dirs(self.config["base_dirs"]))

        timer = time.time()
        while True:
            for project_dir, project in projects.items():
                logger.debug("Inspecting '%s' for stale lock files", project_dir)
                for lock_file, lock_file_age in project.lock_age().items():
                    if lock_file_age > self.config["lock_time"]:
                        logger.info("Lock file '%s' older than %s seconds old. Locking project.", lock_file, self.config["lock_time"])

                        if (
                            self.config["no_lock_when_dir_in_use"] is True and
                            common.user_session_in_dir(project_dir)
                        ):
                            logger.info("User has process running in '%s'. Not locking.", project_dir)
                            # Continue to next project
                            break

                        project.lock()

                        if self.config["desktop_notify"] is True:
                            f = subprocess.run(
                                [
                                    "notify-send",
                                    "-i",
                                    "dialog-information",
                                    "Lockdown: Project locked",
                                    f"Project '{project_dir}' has been automatically locked"
                                ]
                            )

                        # Continue to next project
                        break

            # Check whether its time to rescan for .lockdown.conf files
            now = time.time()
            if now - timer > self.config["rescan_interval"]:
                logger.info("Rescan interval reached. Rescanning for .lockdown.conf files")
                projects = self.load_projects(self.find_project_dirs(self.config["base_dirs"]))
                timer = now

            time.sleep(self.config["inspect_interval"])
