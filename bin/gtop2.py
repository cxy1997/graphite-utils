import os
from subprocess import Popen, PIPE
from itertools import chain


GTOP = 'ls -Art /share/nikola/export/graphite_usage/ | tail -n 1 | xargs -I % sh -c "cat /share/nikola/export/graphite_usage/%" | grep "RUNNING" |sort -k 1,1'
SINFO = 'sinfo -o %G,%N,%P'


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
        gpu = int(line[4][4:]) if line[4].startswith("gpu") else 0
        if line[1] != "default_gpu":
            res[line[2]]["cpu"]["priority"] += cpu
            res[line[2]]["gpu"]["priority"] += gpu
        else:
            res[line[2]]["cpu"]["default"] += cpu
            res[line[2]]["gpu"]["default"] += gpu
    return res


if __name__ == "__main__":
    servers = parse_sinfo(exec(SINFO))
    used = parse_gtop(exec(GTOP))
    print(f"server{' '*18}GPU\t\tCPU Usage\tGPU Usage\t(default / priority / empty)")
    for server in servers.keys():
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
        print(f"{server}{' '*(24-len(server))}{servers[server]['num']} x {servers[server]['type']}\t{used[server]['cpu']['default']} / {used[server]['cpu']['priority']}\t\t{used[server]['gpu']['default']} / {used[server]['gpu']['priority']} / {servers[server]['num']-used[server]['gpu']['default']-used[server]['gpu']['priority']}")