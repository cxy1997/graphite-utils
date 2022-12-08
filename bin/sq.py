import os
import argparse
from subprocess import Popen, PIPE
from itertools import chain

from g2top import parse_server, parse_gpu, parse_usage


parser = argparse.ArgumentParser()
parser.add_argument('--verbose', '-v', action="store_true")
args = parser.parse_args()


GTOP = "sacct -X --format=Jobid,State,AllocTRES%50,ElapsedRaw,TimelimitRaw --units=G | grep RUNNING | grep billing"
SINFO = 'sinfo -o %N\|%G -h -e'
SQ = "squeue -l"
jupyter_log = os.path.expanduser("~/slurm/logs/jupyter.txt")


def read_logs():
    res = dict()
    if os.path.isfile(jupyter_log):
        with open(jupyter_log) as f:
            lines = list(map(lambda x: x.split("\t"), f.readlines()))
        for line in lines:
            job_id = line[1].split(" ")[1]
            port = line[2].rstrip().split(" ")[1]
            res[job_id] = port
    return res


def exec(cmd):
    return Popen(cmd, shell=True, stdout=PIPE).stdout.read().decode("utf-8")


def parse_sinfo(string):
    lines = map(lambda x: x.split("|"), string.rstrip().split("\n"))
    res = dict()
    for line in lines:
        servers = parse_server(line[0])
        gpu = parse_gpu(line[1])
        for server in servers:
            res[server] = gpu
    return res


def parse_qinfo(string, job_dict, server_dict, usage_dict):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: list(filter(lambda y: len(y) > 0, x.split(" "))), lines))[2:]
    res = []
    for line in lines:
        x = dict()
        x["job_id"] = line[0]
        x["partition"] = line[1]
        x["server"] = line[8]
        x["port"] = job_dict.get(line[0], "")
        x["gpu"] = f"{usage_dict[line[0]]['gpu']} x {server_dict[line[8]]['type']}" if line[0] in usage_dict and line[8] in server_dict and server_dict[line[8]]['type'] != "null" else ""
        x["time_left"] = usage_dict[line[0]]["time_left"]
        if args.verbose:
            x["cpu"] = str(usage_dict[line[0]]['cpu'])
            x["mem"] = f"{usage_dict[line[0]]['mem']}G"
        res.append(x)
    return res


def parse_gtop(string):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: list(filter(lambda y: len(y) > 0, x.split(" "))), lines))
    lines = list(filter(lambda x: len(x) > 0, lines))
    res = dict()
    for line in lines:
        res[line[0]] = parse_usage(line[2])
        time_left = int(line[4]) * 60 - int(line[3])
        res[line[0]]["time_left"] = f"{time_left // 86400:>2d}d {time_left % 86400 // 3600:>2d}h {time_left % 3600 // 60:>2d}m {time_left % 60:>2d}s"
    return res


if __name__ == "__main__":
    server_dict = parse_sinfo(exec(SINFO))
    job_dict = read_logs()
    usage_dict = parse_gtop(exec(GTOP))
    jobs = parse_qinfo(exec(SQ), job_dict, server_dict, usage_dict)
    if len(jobs) > 0:
        if args.verbose:
            print(f"Job ID\tPartition\tServer\t\t\t{'CPU':6}{'Memory':9}{'GPU':15}{'Port':8}{'Time Left':17}")
            for x in jobs:
                print(
                    f'{x["job_id"]}\t{x["partition"]:14s}\t{x["server"]:16s}\t{x["cpu"]:6}{x["mem"]:9}{x["gpu"]:15}{x["port"]:8}{x["time_left"]:17}')
        else:
            print(f"Job ID\tPartition\tServer\t\t\t{'GPU':15}{'Port':8}{'Time Left':17}")
            for x in jobs:
                print(f'{x["job_id"]}\t{x["partition"]:14s}\t{x["server"]:16s}\t{x["gpu"]:15}{x["port"]:8}{x["time_left"]:17}')
