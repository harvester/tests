import docker
import argparse
import asyncio
import time
from threading import Thread
import subprocess
client = docker.from_env()


def tar_docker(docker_list, tarName, pigz):
    started_at = time.monotonic()
    new_list = ""
    for i in docker_list:
        new_list += i.strip()+" "
    print(new_list)
    # This part is if you need to do this with gzip for any reason
    if pigz:
        process = subprocess.run("docker save " + new_list + " | pigz -c -4 > " +
                                 tarName, shell=True,
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
    else:
        process = subprocess.run("docker save " + new_list + " | gzip --stdout > " +
                                 tarName, shell=True,
                                 stdout=subprocess.PIPE,
                                 universal_newlines=True)
    # Creates the tar.gz file with pigz
    process
    print(process.stdout)
    total_time = time.monotonic() - started_at
    print('====')
    print(f' tar.gz process took {total_time:.2f} seconds')


def worker_job(docker_list):
    # This prints the images being pulled then pulls them
    print(docker_list)
    # image = client.images.pull(docker_list)


def docker_prune():
    client.images.prune()


async def main():
    # Adds in the parameters and help for the script
    parser = argparse.ArgumentParser(description='Download Rancher images locally.')
    parser.add_argument('filename',
                        help='Filename of image list')
    parser.add_argument('--workers', type=int, default=8, help='Number of Threads')
    parser.add_argument('--save',
                        type=bool, default=False, help='bool for saving images to tar.gz')
    parser.add_argument('--tarName',
                        default='rancher-images.tar.gz', help="Filename of output Tar")
    parser.add_argument('--pigz',
                        type=bool, default=True, help="bool for using pigz")
    args = parser.parse_args()
    parser.print_help()

    # Open the file from the parameter and read in every line
    file1 = open(args.filename, 'r')
    Lines = file1.readlines()
    started_at = time.monotonic()
    iteration = 1
    # Check the length of the file then iterate through it
    length = len(Lines)
    if args.workers > length:
        raise Exception("number of workers can't be more than the length of image-list")
    if args.workers <= 0:
        raise Exception("workers can't be less than or equal to 0")
    while length > 0:
        threads = []
        # Creates the pool of threads and then loops them until the total file has been parsed
        for i in range(args.workers):
            worker = Thread(target=worker_job, args=(Lines[length-1].strip(),))
            worker.setDaemon(True)
            worker.start()
            threads.append(worker)
            length = length - 1
        for thread in threads:
            thread.join()
        iteration = iteration + 1
    # Checks if save is true and tars the docker images
    if args.save:
        tar_docker(Lines, args.tarName, args.pigz)

    # Get the amount of time and number of total threads.
    total_slept_for = time.monotonic() - started_at
    total_workers = iteration * args.workers
    print('====')
    print(f'{total_workers} workers processed in parallel for {total_slept_for:.2f} seconds')

asyncio.run(main())
