# multi-docker-pull
Pull multiple Docker images at once and then tarball them

This script will create a group of worker threads that will simultaneously pull docker images to your local docker instance.

# requirements
- script tested with `docker==7.0.0` [pip package](https://pypi.org/project/docker/)
- script tested with `pigz 2.6`, [pigz](https://zlib.net/pigz/)
- script tested with Python 3.10