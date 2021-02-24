# splitrsync: speed up data transfer with parallel rsync processes 

Splitrsync is a simple python tool to spread a syncing process across multiple parallel rsync processes to increase overall throughtput and reduce syncing time. Rsync is limited in performance mainly by the speed of computing data hashes, an operation which is also single threaded and doesn't take advantage of modern multi core CPU architectures. By splitting the syncing process across multiple concurrent rsync processes this limitation pushed back.

Performance example: with a 32 cores server (16 cores + HT) running splitrsync with 24 processes yields around 4.5 GB/s. Storage system used is using Infiniband and a parallel distributed file system. Note that non parallel storage / file systems (such as NFS) will have very small benefit, if anything at all, from parallelization.

Recent (March 2020) tests with a more powerful server, 80 cores (40 + HT) running with 80 processes exceeded 9 GB/s. Limiting factors can be small file size or CPU power as rsync is CPU intensive with such high throughput. CPU usage on all cores was close to max.

# Limitations

Please note that not all rsync options or features are supported at this time. Run splitrsync --help to see currently implemented options.

Rsync + SSH is not supported in the current version.

# Installation

The following software is required to run splitrsync

- python version 3.6 or newer
- rsync installed and available in PATH environment variable

Splitrsync can be installed both in a [python virtual environment](https://docs.python.org/3/tutorial/venv.html) or using [pip](https://pypi.org/project/pip/). These instructions are valid for both cases. Instructions on how to setup a virtual environment are given on the official website and are out of scope for this document, so it is assumed you already have a virtual environment ready if you want to use one.

Clone the git repo or download one of the release source code
```
git clone https://github.com/fmi-basel/splitrsync.git
```

cd into the directory with the source code and use pip to install

```
pip install .    # or pip3 if your default python is version 2
```

Note on some distributions you have to actually use the ```pip3``` command, as pip might be the python2 version and that wont work. When not installing in a virtualenv you also want to add the ```--user``` option to the install command above.
