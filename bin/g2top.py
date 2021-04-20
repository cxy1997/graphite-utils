import os
import sys
import argparse
from subprocess import Popen, PIPE
from itertools import chain


GTOP = "sacct --format=User%10,partition%20,NodeList%25,State,AllocTRES%50 -a --units=G | grep RUNNING | grep billing"
SINFO = 'sinfo -o %N\|%G\|%C\|%e\|%m -h -e'
RESOURCES = ["cpu", "gpu", "mem"]
PARTITIONS = ["priority", "default"]


def exec(cmd):
    return Popen(cmd, shell=True, stdout=PIPE).stdout.read().decode("utf-8")


def _get_suffix(string):
    if "-" in string:
        mid = string.find("-")
        left = int(string[:mid])
        right = int(string[mid + 1:])
        return list(map(lambda x: "%02d" % x, range(left, right + 1)))
    else:
        return [string]


def get_suffix(string):
    string = string.split(",")
    string = list(map(_get_suffix, string))
    return list(chain(*string))


def parse_server(string):
    bracket_cnt = 0
    q = 0
    _servers = []
    for p in range(len(string)):
        if string[p] == "[":
            bracket_cnt += 1
        elif string[p] == "]":
            bracket_cnt -= 1
        elif string[p] == "," and bracket_cnt == 0:
            _servers.append(string[q:p])
            q = p + 1
    _servers.append(string[q:])

    servers = []
    for s in _servers:
        lb, rb = s.find("["), s.find("]")
        if 0 <= lb < rb:
            base_name = s[:lb]
            suffix = get_suffix(s[lb + 1:rb])
            for su in suffix:
                servers.append(base_name + su)
        else:
            servers.append(s)

    return servers


def parse_gpu(string):
    if "null" in string:
        return {"type": "null", "num": 0}
    else:
        _, gtype, gnum = string.split(":")
        return {"type": gtype, "num": int(gnum)}


def parse_cpu(string):
    return {"idle": int(string.split("/")[1])}


def parse_mem(string):
    i, t = list(map(lambda x: int(x) if x.isdigit() else 0, string))
    return {"idle": i, "total": t}


def init_usage():
    return {r: {p: 0 for p in PARTITIONS} for r in RESOURCES}


def parse_sinfo(string, args):
    lines = map(lambda x: x.split("|"), string.rstrip().split("\n"))
    res = dict()
    for line in lines:
        servers = parse_server(line[0])
        gpu = parse_gpu(line[1])
        cpu = parse_cpu(line[2])
        mem = parse_mem(line[3:5])
        if args.gpu_only and gpu["type"] == "null":
            continue
        for server in servers:
            res[server] = {
                "gpu": gpu,
                "cpu": cpu,
                "mem": mem,
                "usage": init_usage()
            }
    return res


def parse_usage(string):
    res = {k: 0 for k in RESOURCES}
    for r in RESOURCES:
        if r in string:
            l = string.find(r)
            res[r] = eval(string[l+4:l+string[l:].find(",")].rstrip("G"))
    return res


def parse_gtop(string, servers):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: list(filter(lambda y: len(y) > 0, x.split(" "))), lines))
    lines = list(filter(lambda x: len(x) > 0, lines))
    for line in lines:
        partition = "default" if "default" in line[1] else "priority"
        _servers = parse_server(line[2])
        info = parse_usage(line[4])
        for server in _servers:
            if server in servers:
                for r in RESOURCES:
                    servers[server]["usage"][r][partition] += info[r]
    return servers


def disp_resource(info, res):
    s = list(map(info["usage"][res].get, PARTITIONS))
    if res == "cpu":
        s.append(info[res]["idle"])
        return " / ".join([f"{x:2d}" for x in s])
    elif res == "gpu":
        s.append(info[res]["num"] - sum(s))
        return " / ".join([f"{x}" for x in s])
    elif res == "mem":
        s.append(info[res]["idle"] / 1024.0)
        return " / ".join([f"{x:5.1f}" for x in s])



def disp(server, info):
    s = f"{server:24}"
    s += f"{info['gpu']['num']} x {info['gpu']['type']}\t"
    s += "\t".join(disp_resource(info, res) for res in RESOURCES)
    return s



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu-only', action="store_true")
    args = parser.parse_args()

    servers = parse_sinfo(exec(SINFO), args)
    usage = parse_gtop(exec(GTOP), servers)

    print(f"{'Server':24}GPU\t\tCPU Usage\tGPU Usage\tMemory Usage (GB)\t\t(priority / default / idle)")
    for server in usage.keys():
        print(disp(server, usage[server]))
