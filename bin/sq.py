import os
from subprocess import Popen, PIPE
from itertools import chain


SQ = "squeue -l"
jupyter_log = "/home/xc429/slurm/logs/jupyter.txt"


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


def parse_qinfo(string, job_dict):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: list(filter(lambda y: len(y) > 0, x.split(" "))), lines))[2:]
    res = []
    for line in lines:
        x = dict()
        x["job_id"] = line[0]
        x["partition"] = line[1]
        x["server"] = line[8]
        x["port"] = job_dict.get(x["job_id"], "")
        res.append(x)
    return res


if __name__ == "__main__":
    job_dict = read_logs()
    jobs = parse_qinfo(exec(SQ), job_dict)
    if len(jobs) > 0:
        print("Job ID\tPartition\tServer\t\t\tPort")
        for x in jobs:
            print(f'{x["job_id"]}\t{x["partition"]:14s}\t{x["server"]:16s}\t{x["port"]}')
