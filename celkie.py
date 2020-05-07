#!/usr/bin/python3

# Copyright (C) 2019, 2020 Gunter Miegel startnext.com

"""Celkie the Startnext database backup/recovery helper


# TODO add passwort parameter for restore
Usage:
  celkie list
  celkie backup [--database=<database>] [--tables=<table> ... ] [--incremental]
  celkie dump --backup=<name_of_full_backup> [--database=<database> ] [--tables=<table,table> ]
  celkie restore <backupname>

Options:
  -h --help     Show this screen.

"""

import time
import os
import sys
import socket
import shutil
from docopt import docopt
import docker
import yaml
import re


def load_conf():
    conf_file_path = os.path.join(os.path.dirname(__file__), "celkie.yaml")
    with open(conf_file_path, "r") as file:
        return yaml.load(file, Loader=yaml.FullLoader)


def spawn_container(datadir):
    client = docker.from_env()
    container = client.containers.run(
        CONTAINER_IMAGE,
        detach=True,
        volumes={
            BACKUP_DIR: {"bind": BACKUP_DIR, "mode": "rw"},
            datadir: {"bind": "/var/lib/mysql", "mode": "rw"},
        },
        environment=["MYSQL_ROOT_PASSWORD=" + PASSWORD, "MYSQL_TCP_PORT=" + PORT,],
        ports={"3306/tcp": ("127.0.0.1", PORT)},
        name="celkie-mariadb",
    )


def dismantle_container():
    print("Remove temporary MariaDB container")
    client = docker.from_env()
    id = client.containers.get("celkie-mariadb")
    id.stop()
    id.remove()


def get_container(container_name):
    client = docker.from_env()
    return client.containers.get(container_name)


def create_directory_for_incremental_backups(full_backup_name):
    dir_name = BACKUP_DIR + "/" + full_backup_name + "/incr"
    try:
        os.mkdir(dir_name)
        print("Directory ", dir_name, " created ")
    except FileExistsError:
        print("Directory ", dir_name, " already exists")


def run_backup(database, tables, incremental):
    client = docker.from_env()
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    if incremental:
        last_full_backup = get_last_full_backup()
        backupname = last_full_backup + "/incr/" + timestamp + "_inc"
        create_directory_for_incremental_backups(last_full_backup)
    else:
        backupname = "_".join(filter(bool, [timestamp, database, "full"]))
    target_dir = "/".join([BACKUP_DIR, backupname])
    cmd = [
        "/usr/bin/mariabackup",
        "--backup",
        "--datadir=" + DEFAULT_DATADIR,
        "--target-dir=" + target_dir,
        "--user=" + USER,
        "--password=" + PASSWORD,
        "--host=127.0.0.1",
    ]
    if database:
        cmd.append("--databases=" + database)
    if incremental:
        cmd.append("--incremental-basedir=" + BACKUP_DIR + "/" + last_full_backup)

    container = client.containers.run(
        CONTAINER_IMAGE,
        cmd,
        auto_remove=True,
        name="celkie-mariadb_run_backup",
        network_mode="host",
        detach=True,
        stdout=True,
        stderr=True,
        volumes={
            BACKUP_DIR: {"bind": BACKUP_DIR, "mode": "rw"},
            "/var/lib/mysql": {"bind": DEFAULT_DATADIR, "mode": "ro"},
            "/var/run/mysqld/mysqld.sock": {
                "bind": "/var/run/mysqld/mysqld.sock",
                "mode": "ro",
            },
        },
    )
    for line in container.logs(stream="True"):
        print(line.decode())
    print("Created physical backup at" + target_dir)


def prepare_backup_for_restore(name_of_full_backup):
    print("Prepare " + name_of_full_backup + " for restore")
    client = docker.from_env()
    container = client.containers.run(
        CONTAINER_IMAGE,
        [
            "/usr/bin/mariabackup",
            "--prepare",
            "--target-dir=" + BACKUP_DIR + "/" + name_of_full_backup,
        ],
        auto_remove=True,
        name="celkie-mariadb_restore_prepare",
        detach=True,
        stdout=True,
        stderr=True,
        volumes={BACKUP_DIR: {"bind": BACKUP_DIR, "mode": "rw"},},
    )
    for line in container.logs(stream="True"):
        print(line.decode())


def cleanup_datadir(dir):
    print("Cleanup temporary datadir")
    shutil.rmtree("dir", ignore_errors=True)


def restore_backup(name_of_full_backup, datadir):
    print("Start restore of the backup " + name_of_full_backup + " to " + datadir)
    # FIXME: On call this function if the directory is really there
    cleanup_datadir(datadir)
    client = docker.from_env()
    container = client.containers.run(
        CONTAINER_IMAGE,
        [
            "/usr/bin/mariabackup",
            "--copy-back",
            "--target-dir=" + BACKUP_DIR + "/" + name_of_full_backup,
        ],
        auto_remove=True,
        name="celkie-mariadb_restore",
        network_mode="host",
        detach=True,
        stdout=True,
        stderr=True,
        volumes={
            BACKUP_DIR: {"bind": BACKUP_DIR, "mode": "rw"},
            datadir: {"bind": "/var/lib/mysql", "mode": "rw"},
        },
    )
    for line in container.logs(stream="True"):
        print(line.decode())


def list_available_backups():
    for backup in sorted(os.listdir(BACKUP_DIR)):
        print(backup)


def get_last_full_backup():
    dir_list = os.listdir(BACKUP_DIR)
    r = re.compile(".*full$")
    last_available_full_backup = sorted(list(filter(r.match, dir_list)))[-1]
    return last_available_full_backup


def exec_command(container_name, command):
    client = docker.from_env()
    container = client.containers.get(container_name)
    print(container)
    print(command)
    response = container.exec_run(command, stream=False, tty=True)
    # next(response.output)
    print(response)
    # next(response.output)


def wait_for_port(host, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((host, port))
    except:
        time.sleep(2)
        print("Waiting for " + host + " to listen on port " + port)
    # finally:
    #    s.shutdown(socket.SHUT_RDWR)
    #    s.close


def create_dump(name_of_full_backup, database, tables):
    print(
        "Create logical database from physical database backup " + name_of_full_backup
    )
    temp_datadir = "/tmp/" + name_of_full_backup + "/var/lib/mysql"
    print("Used temporary DATADIR: " + temp_datadir)

    name_elements = []
    # If arguments are not used they come as boolean FALSE by docopt
    # and have to be filtered before joining opts.
    # Empty multiple options come as empty list [] and have to be
    # set to boolean False to be filtered out afterwards.
    if not tables:
        t = False
    else:
        t = tables[0].replace(" ", "_")

    for e in filter(
        bool, [name_of_full_backup, database, t,".sql"]
    ):
        if e != [] or None:
            name_elements.append(e)
    #print(name_elements)
    dump_name = "_".join(name_elements)

    # if database:
    #    # Password parameter needs no space between -p and password
    #    dump_name = "_".join(
    #        filter(
    #            bool,
    #            [name_of_full_backup, database, tables[0].replace(" ", "_"), ".sql"],
    #        )
    #    )
    #    dump_path = BACKUP_DIR + "/" + dump_name
    #    opts = [database, " ".join(tables), "-u", USER, "-p" + PASSWORD, ">", dump_path]
    ## print(opts)
    # else:
    #    dump_name = "_".join(filter(bool, [name_of_full_backup, ".sql"]))
    #    dump_path = BACKUP_DIR + "/" + dump_name
    #    opts = ["--all-databases", "-u", USER, "-p" + PASSWORD, ">", dump_path]

    dump_path = BACKUP_DIR + "/" + dump_name
    opts = ["-u", USER, "-p" + PASSWORD, ">", dump_path]
    if not database:
        opts.insert(0,"--all-databases")
    else:
        opts.insert(0,"--database " + database + " " + " ".join(tables))
    prepare_backup_for_restore(name_of_full_backup)
    restore_backup(name_of_full_backup, temp_datadir)
    spawn_container(temp_datadir)
    wait_for_port(HOST, PORT)

    exec_command(
        "celkie-mariadb",
        ["sh", "-c", "/usr/bin/mysqldump -h 127.0.0.1 " + " ".join(filter(bool, opts))],
    )
    print("Database dump created and stored at: " + dump_path)

    dismantle_container()


def main(arguments):
    #print(arguments)
    # Replace the commas with whitespace as separator between tables.
    tables = [t.replace(",", " ") for t in arguments["--tables"]]
    # print(tables)
    if arguments["backup"]:
        run_backup(
            arguments["--database"], tables, arguments["--incremental"],
        )
    if arguments["list"]:
        list_available_backups()
    if arguments["dump"]:
        if arguments["--backup"]:
            create_dump(
                arguments["--backup"], arguments["--database"], tables,
            )
        else:
            sys.exit("Please specify the backup to use for dumping.")


if __name__ == "__main__":
    ARGUMENTS = docopt(
        __doc__, version="Startnext database backup/recovery helper v0.1"
    )
    CONF = load_conf()
    CONTAINER_IMAGE = CONF["container_image"] or "mariadb:10.1.43"
    PORT = CONF["port"] or "13306"
    BACKUP_DIR = CONF["backup_dir"] or "/var/backups/mariadb"
    DEFAULT_DATADIR = CONF["default_datadir"] or "/var/lib/mysql"
    # Defaulting to the offical most secure password of the world
    # https://www.the-postillon.com/2017/03/mb2r5ohf-0t.html
    PASSWORD = CONF["password"] or "Mb2.r5oHf-0t"
    USER = CONF["user"] or "root"
    # Not configurable cause mariabackup only works on localhost
    HOST = "localhost"

    main(ARGUMENTS)
