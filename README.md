# Celkie

The friendly Startnext database backup and recovery helper.

Celkie refers and resembles to selkie.
Wikipedia about selkies:

> In Scottish mythology, selkies (also spelled silkies, sylkies, selchies) or selkie folk (Scots: selkie fowk) meaning "seal folk"[a] are mythological beings capable of therianthropy, changing from seal to human form by shedding their skin. They are found in folktales and mythology originating from the Northern Isles of Scotland. 

The mascot of MariaDB is a sealion or seal and Celkie provides access to a database in a temopary different appearance like selkies are told to do. All with a friendly and quite seductive behavior as well as selkies.
Celkie bundles common workflows when working with SQL databases and MariaDB/MySQL.

* Create physical backups with `mariabackup`
* Create logical backups (database dumps) from physical backups
* Create temporary instances of MariaDB with data from a physical backup 

## Requirements

- Docker ≥ 19.03
- Python ≥ 3.8

Python requirements are handled by Pipenv see at the corresponding `Pipfile`

## Install 

Clone this repository.


### Install required Python packagess via Pipenv

```
 $ pipenv install
```

## Usage 

```
  
  celkie list
  celkie backup [--database <database>] [--tables <table> ... ] [--incremental]
  celkie dump --backup <name_of_full_backup> [--database <database> ] [--tables <table> ... ]
  celkie restore <backupname>


```

## Configuration

Configuration is done via the configuration file `celkie.yaml`.

### Example configuration file

```
container_image: "mariadb:10.1.43"
port: "13306"
host: "localhost"
backup_dir: "/var/backups/mariadb"
default_datadir: "/var/lib/mysql"
password: "foobar"
user: "root"
```

## Development 

There is a `vagrant` enviroment for development purposes which can be easily used be calling the target of the included `Makefile`.

```
$ make up
```
Will create the `vagrant` VMs.

```
$ make verify
```

Will verify the behavior of `celkie` with Inspec tests from `./test/celike_test.rb`.

## Debug Docker API calls at socket

To see all API calls to Docker we can use `socat` to mirror the socket of Docker.

```
sudo -s
cd /var/run
mv docker.sock docker.sock.orig
socat -v UNIX-LISTEN:/var/run/docker.sock,group=docker,perm=0660,reuseaddr,fork UNIX-CONNECT:/var/run/docker.sock.orig
```
