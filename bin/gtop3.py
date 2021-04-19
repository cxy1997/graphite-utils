import os
from subprocess import Popen, PIPE
from itertools import chain
import argparse

GTOP = 'cat /share/nikola/export/graphite_usage/$(date "+sacct.%m%d%Y-%H")`printf %02d $(($(date "+%M") / 15 * 15))` | grep "RUNNING" |sort -k 1,1'
# GTOP = 'cat /tmp/gtop.txt'
SINFO = 'sinfo -o %G,%N,%P'
SINFO_part = 'sinfo -o %n:%P'
SINFO_ram = 'sinfo -o %n:%e:%m'
SINFO_cpu = 'sinfo -o %n:%C'

def exec(cmd):
    return Popen(cmd, shell=True, stdout=PIPE).stdout.read().decode("utf-8")


def _get_suffix(string):
    mid = string.find("-")
    left = int(string[:mid])
    right = int(string[mid+1:])
    return list(map(lambda x: "%02d" % x, range(left, right+1)))


def get_suffix(string):
    string = string.split(",")
    string = list(map(_get_suffix, string))
    return list(chain(*string))


def parse_server(string):
    bracket_cnt = 0
    p = 0
    while string[p].isdigit():
        p += 1
    assert string[p] == ","
    gnum = int(string[:p])
    string = string[p+1:]

    q = 0
    _servers = []
    for p in range(len(string)):
        if string[p] == "[":
            bracket_cnt += 1
        elif string[p] == "]":
            bracket_cnt -= 1
        elif string[p] == "," and bracket_cnt == 0:
            _servers.append(string[q:p])
            q = p+1

    servers = []
    for s in _servers:
        lb, rb = s.find("["), s.find("]")
        if 0 <= lb < rb:
            base_name = s[:lb]
            suffix = get_suffix(s[lb+1:rb])
            for su in suffix:
                servers.append(base_name+su)
        else:
            servers.append(s)

    return gnum, servers


def parse_sinfo(string):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: x.split(":"), lines))
    res = dict()
    for line in filter(lambda x: len(x) == 3, lines):
        gtype = line[1]
        gnum, servers = parse_server(line[2])
        for server in servers:
            res[server] = {
                "type": gtype,
                "num": gnum
            }

    return res


def parse_gtop(string):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: list(filter(lambda y: len(y) > 0, x.split(" "))), lines))
    lines = list(filter(lambda x: len(x) > 0, lines))
    res = dict()
    for line in lines:
        if line[2] not in res.keys():
            res[line[2]] = {
                "cpu": {
                    "default": 0,
                    "priority": 0,
                },
                "gpu": {
                    "default": 0,
                    "priority": 0,
                },
            }
        cpu = int(line[3])
        gpu = int(line[4].split(":")[1]) if line[4].startswith(
            "gpu") or line[4].startswith("7696487") else 0
        if line[1] != "default_gpu":
            res[line[2]]["cpu"]["priority"] += cpu
            res[line[2]]["gpu"]["priority"] += gpu
        else:
            res[line[2]]["cpu"]["default"] += cpu
            res[line[2]]["gpu"]["default"] += gpu
    return res

def get_server_partitions(string):
    lines = string.rstrip().split("\n")
    lines = list(
        map(lambda x: list(filter(lambda y: len(y) > 0, x.split(":"))), lines))
    lines = list(filter(lambda x: len(x) > 0, lines))
    infos = dict()
    for line in lines:
        if line[1] in ("interactive_cpu", "interactive", "default_gpu*"):
            continue
        if line[0] not in infos:
            infos[line[0]] = line[1]
        else:
            infos[line[0]] += ", " + line[1]
    return infos

def get_server_ram(string):
    lines = string.rstrip().split("\n")
    lines = list(
        map(lambda x: list(filter(lambda y: len(y) > 0, x.split(":"))), lines))
    lines = list(filter(lambda x: len(x) > 0, lines))
    infos = dict()
    for line in lines[1:]:
        try:
            infos[line[0]] = (float(line[1]) / 1024, float(line[2]) / 1024)
        except ValueError:
            infos[line[0]] = (0, 0)
    return infos

def get_server_cpu(string):
    lines = string.rstrip().split("\n")
    lines = list(
        map(lambda x: list(filter(lambda y: len(y) > 0, x.split(":"))), lines))
    lines = list(filter(lambda x: len(x) > 0, lines))
    infos = dict()
    for line in lines[1:]:
        try:
            infos[line[0]] = [int(x) for x in line[1].split("/")]
        except ValueError:
            infos[line[0]] = (0, 0, 0, 0)
    return infos


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only_partition", type=str, default=None)
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    servers = parse_sinfo(exec(SINFO))
    used = parse_gtop(exec(GTOP))
    server_parts = get_server_partitions(exec(SINFO_part))
    server_ram = get_server_ram(exec(SINFO_ram))
    server_cpu = get_server_cpu(exec(SINFO_cpu))
    print(
        f"server{' '*18}GPU{' '*11}partition{' '*7}RAM Usage (E/T){' '*4}CPU (D/P/T){' '*3}GPU (D/P/E)")
    servers = {k: v for k, v in sorted(
        servers.items(), key=lambda item: item[0])}
    for server in servers.keys():
        if args.only_partition is not None:
            if not args.only_partition in server_parts[server]:
                continue
        if server not in used.keys():
            used[server] = {
                "cpu": {
                    "default": 0,
                    "priority": 0,
                },
                "gpu": {
                    "default": 0,
                    "priority": 0,
                },
            }
        print(f"{server: <24}{servers[server]['num']: <1} x {servers[server]['type']: <10}{server_parts[server]: <16}{server_ram[server][0]:5.1f} G / {server_ram[server][1]:5.1f} G{' '*2}{used[server]['cpu']['default']: <2} / {used[server]['cpu']['priority']: <2} / {server_cpu[server][3]: <4}{used[server]['gpu']['default']} / {used[server]['gpu']['priority']} / {servers[server]['num']-used[server]['gpu']['default']-used[server]['gpu']['priority']}")
