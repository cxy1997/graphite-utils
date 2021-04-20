import os
from subprocess import Popen, PIPE
from itertools import chain

from g2top import parse_server, parse_gpu


SINFO = 'sinfo -o %N\|%G -h -e'
SQ = "squeue -l"
jupyter_log = os.path.expanduser("~/slurm/logs/jupyter.txt")


def read_logs():
    with open(jupyter_log) as f:
        lines = list(map(lambda x: x.split("\t"), f.readlines()))
    res = dict()
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


def parse_qinfo(string, job_dict, server_dict):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: list(filter(lambda y: len(y) > 0, x.split(" "))), lines))[2:]
    res = []
    for line in lines:
        x = dict()
        x["job_id"] = line[0]
        x["partition"] = line[1]
        x["server"] = line[8]
        x["port"] = job_dict.get(x["job_id"], "")
        x["gpu"] = f"{server_dict[line[8]]['num']} x {server_dict[line[8]]['type']}" if line[8] in server_dict and server_dict[line[8]]['type'] != "null" else ""
        res.append(x)
    return res


if __name__ == "__main__":
    server_dict = parse_sinfo(exec(SINFO))
    job_dict = read_logs()
    jobs = parse_qinfo(exec(SQ), job_dict, server_dict)
    if len(jobs) > 0:
        print(f"Job ID\tPartition\tServer\t\t\t{'GPU':15}Port")
        for x in jobs:
            print(f'{x["job_id"]}\t{x["partition"]:14s}\t{x["server"]:16s}\t{x["gpu"]:15}{x["port"]}')
