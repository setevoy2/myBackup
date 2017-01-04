ugration** under development **

# Description

I have bunch of Linux boxes (work laptop, laptop and PC at home, 3 VPS etc) and want to have bacups, obviously.

Because of every box have own data to backup (`~/.thunderbird` on home PC, or `/var/www/vhosts` on my VPS, for example) - I made script to have all in one. 

**myBackup** is flexible - thanks to its configuration file, where you can specify which resources (databases, files/dirs on filesystem), when (see `runon` option below, which allows to create backups by specifing weekdays) and where (see the `store` option - save to local filesystem, **S3**, **Glasier**) save backup to. More details about optionis - in the **[Configuration]** section.

It's under development when have some free time. Please - see **[ToDo features]** and **[ToDo development process]** lists at bottom.

Can backup:

- local files;
- #todo: remote files (via SSH);
- #todo: local database (MySQL);
- #todo: remote database (MySQL).

**myBackup** can save backups locally or remote - to the **AWS S3** (#todo - **AWS Glacier**) bucket.

# Workflow

Script uses **myBackup**'s configuration file (`conf/mybackup.ini` by default) to get objects (an *items*, described in config's *sections*) to create backup from.

Each such an item must be added to the configugration file as dedictaed section, e.g.:

```
...
[KeyPass]
source = '/home/setevoy/Dropbox/KeyPass/'
destination = '/home/setevoy/Backups/KeyPass/'
store = 'local'
bkptype = 'full'
...
```

Here - full */home/setevoy/Dropbox/KeePass/* directory content will be saved in a `KeePass_*type*_*date*_tar.gz` file in the local directory `/home/setevoy/Backups/KeePass/`

Please note - section name (e.g. - "KeePass") will be used for archive name + `bkptype` (*full* or *inc*) and date (e.g. *2017_01_03_17_30_35*). Result file will be *KeyPass_full_2017_01_03_17_30_35.tar.gz*.

Script will load `defaults` section first, and will overwrite each parameter with data from item's section.

You can use any scheduler (e.g. `cron` for **Linux**) to run script with desirable periods.

# Prerequisites

**Python** modules:

- ConfigParcer
- argparse

Script tested on **Python3/Linux**.

# Configuration

All configuration can be done via config file (`conf/mybackup.ini` by default).

You can specify another config file using `-c` option, e.g.:

`$ ./mybackup.py -c anotherconfig.ini`

Config file options list:

- `accesskey`: AWS Access key. `AWS_ACCESS_KEY_ID` variable will be used if `accesskey` empty (default).
- `secretkey`: AWS Secret key. `AWS_SECRET_ACCESS_KEY` variable will be used if `secretkey` empty (default).
- `datatype`: *file* - for filesystem data (files, directories) or *db* - for databases (not implemented yet).
- `bkptype`: *full* or *inc* (*incremental*) (see `period` for *inc* backup type).
- `source`: for the *file* `datatype` and *local* `store` only - source file/directory to create tar.gz archive from.
- `destination`: for *file* `datatype` only - destination directory to store created tar.gz file.
- `store`: destination to store created tar.gz archives - *local* or *s3*. 
- `period`: period for the *inceremntal* `bkptype` to search changed files during last `period` (hours).
- `bucket`: for the *s3* `store` only - bucket name for backups.
- `droponpush`: for the *s3* `store` only - delete (*1, "yes", "true", "True"*) or leave local files from the the `desctination` path after upload to S3.
- `fullretain`: full backups number to store in `store`.
- `incretain`: incremental backups number to store in `store`.
- `runon`: days to run backup on item. Available options are: 'mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'. Default - daily.

You can find examples in the existing [config file].

#### ToDo features

- options: overwrite section's parameters with command line options;
- encrypt backups?

#### ToDo development process

- databases backup;
- Logger() class for logs;
- "conf.d" directory for separate configs;

[ToDo features]: https://github.com/setevoy2/myBackup#todo-features
[ToDo development process]: https://github.com/setevoy2/myBackup#todo-development-process
[Configuration]: https://github.com/setevoy2/myBackup#configuration
[config file]: https://github.com/setevoy2/myBackup/blob/master/conf/mybackup.ini
