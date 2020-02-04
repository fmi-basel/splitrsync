# splitrsync: speed up data transfer with parallel rsync processes 

Splitrsync is a simple python tool to spread a syncing process across multiple parallel rsync processes to increase overall throughtput and reduce syncing time. Rsync is limited in performance mainly by the speed of computing data hashes, an operation which is also single threaded and doesn't take advantage of modern multi core CPU architectures. By splitting the syncing process across multiple concurrent rsync processes this limitation pushed back.

Performance example: with a 32 cores server (16 cores + HT) running splitrsync with 24 processes yields around 4.5 GB/s. Storage system used is using Infiniband and a parallel distributed file system. Note that non parallel storage / file systems (such as NFS) will have very small benefit, if anything at all, from parallelization.

# Limitations

Please note that not all rsync options or features are supported at this time. Run splitrsync --help to see currently implemented options.

Rsync + SSH is not supported in the current version.
