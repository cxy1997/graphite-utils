import os
from subprocess import Popen, PIPE
from itertools import chain

from g2top import parse_server, parse_gpu, parse_usage


GTOP = "sacct -X --format=Jobid,State,AllocTRES%50 --units=G | grep RUNNING | grep billing"
SINFO = 'sinfo -o %N\|%G -h -e'
SQ = "squeue -l"
jupyter_log = os.path.expanduser("~/slurm/logs/jupyter.txt")


def read_logs():
    res = dict()
    if os.path.exists(jupyter_log):
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
        x["mem"] = f"{usage_dict[line[0]]['mem']}G"
        x["cpu"] = f"{usage_dict[line[0]]['cpu']}"
        res.append(x)
    return res


def parse_gtop(string):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: list(filter(lambda y: len(y) > 0, x.split(" "))), lines))
    lines = list(filter(lambda x: len(x) > 0, lines))
    res = dict()
    for line in lines:
        res[line[0]] = parse_usage(line[2])
    return res


if __name__ == "__main__":
    server_dict = parse_sinfo(exec(SINFO))
    job_dict = read_logs()
    usage_dict = parse_gtop(exec(GTOP))
    jobs = parse_qinfo(exec(SQ), job_dict, server_dict, usage_dict)
    if len(jobs) > 0:
        print(f"{'Job ID':^8}{'Partition':^14}{'Server':^20}{'Port':^8}{'GPU':^15}{'CPU':5}{'RAM':5}")
        for x in jobs:
            print(f'{x["job_id"]:^8}{x["partition"]:^14}{x["server"]:20}{x["port"]:8}{x["gpu"]:^15}{x["cpu"]:5}{x["mem"]:5}')
