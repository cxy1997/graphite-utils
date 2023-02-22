import os
import sys
import argparse
from subprocess import Popen, PIPE
from itertools import chain
from termcolor import colored

GTOP = "sacct -X --format=User%10,partition%20,NodeList%25,State,AllocTRES%50,Jobid -a --units=G | grep RUNNING | grep billing"
# SINFO = 'sinfo -o %N\|%G\|%C\|%e\|%m -h -e'
SINFO = 'sinfo -O nodehost:50,gres:50,cpusstate,allocmem,memory -h -e'
RESOURCES = ["cpu", "gpu", "mem"]
PARTITIONS = ["priority", "default"]

def exec(cmd):
    return Popen(cmd, shell=True, stdout=PIPE).stdout.read().decode("utf-8")

priority_nodes = {
    'kilian': set([
        "nikola-compute-01",
        "nikola-compute-02",
        "nikola-compute-03",
        "nikola-compute-04",
        "nikola-compute-05",
        "nikola-compute-11",
        "nikola-compute-12",
        "nikola-compute-13",
        "nikola-compute-14",
        "nikola-compute-15",
        "nikola-compute-16",
        "nikola-compute-17",
        "harpo",
        "tripods-compute-01",
        "tripods-compute-02"
    ]),
}


def is_priority(name):
    return not (("default" in name) or ("gpu" in name))

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
        gtype = []
        gnum_total = 0
        for sub in string.split(","):
            slices = sub.split(":")
            gtype.append(slices[1])
            gnum = slices[2]
            end_idx = 0
            while end_idx < len(gnum) and gnum[end_idx].isdigit():
                end_idx += 1
            gnum_total += int(gnum[:end_idx])
        return {"type": f'({"|".join(gtype)})' if len(gtype) > 1 else gtype[0], "num": gnum_total}


def parse_cpu(string):
    return {"idle": int(string.split("/")[1])}


def parse_mem(string):
    a, t = list(map(lambda x: int(x) if x.isdigit() else 0, string))
    return {"idle": t-a, "total": t}


def init_usage():
    return {r: {p: 0 for p in PARTITIONS} for r in RESOURCES}


def parse_sinfo(string, args):
    lines = map(lambda x: x.split(), string.rstrip().split("\n"))
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
                "usage": init_usage(),
                "users": {}
            }
    return res


def parse_usage(string):
    res = {k: 0 for k in RESOURCES}
    for r in RESOURCES:
        if r in string:
            l = string.find(r)
            res[r] = eval(string[l+4:l+string[l:].find(",")].rstrip("G"))
        else:
            res[r] = 0
    return res


def parse_gtop(string, servers):
    lines = string.rstrip().split("\n")
    lines = list(map(lambda x: list(filter(lambda y: len(y) > 0, x.split(" "))), lines))
    lines = list(filter(lambda x: len(x) > 0, lines))
    for line in lines:
        partition = "default" if not is_priority(line[1]) else "priority"
        _servers = parse_server(line[2])
        info = parse_usage(line[4])
        for server in _servers:
            if server in servers:
                servers[server]["users"][line[5]] = {}
                servers[server]["users"][line[5]]['partition'] = line[1]
                servers[server]["users"][line[5]]['netid'] = line[0]
                for r in RESOURCES:
                    servers[server]["usage"][r][partition] += \
                        info[r] // len(_servers)
                    servers[server]["users"][line[5]][r] = \
                        info[r] // len(_servers)
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


def disp_user_resource(job_info, res):
    if res == "cpu":
        s = f"{job_info[res]:2d}"
        if not is_priority(job_info['partition']):
            s = " "*2 + " "*3 + s + " "*3 + " "*2
        else:
            s = s + " "*3 + " "*2 + " "*3 + " "*2
    elif res == "gpu":
        s = f"{job_info[res]}"
        if not is_priority(job_info['partition']):
            s = " " + " "*3 + s + " "*3 + " "
        else:
            s = s + " "*3 + " " + " "*3 + " "
    elif res == "mem":
        s = f"{job_info[res]:5.1f}"
        if not is_priority(job_info['partition']):
            s = " "*5 + " "*3 + s + " "*3 + " "*5
        else:
            s = s + " "*3 + " "*5 + " "*3 + " "*5

    return s


def disp(server, info, disp_users):
    s = f"{server:25}"
    gpu_line = f"{info['gpu']['num']} x {info['gpu']['type']}"
    if disp_users:
        s += " "*35
    s += f"{gpu_line:19}"
    s += "\t".join(disp_resource(info, res) for res in RESOURCES)
    if disp_users:
        for jobid, job_info in info['users'].items():
            user_line = ""
            user_line += "\n" + " " * 25 + \
                f"   {job_info['netid']:^9.9}   {job_info['partition']:^17.17}   "
            gpu_line = f"{job_info['gpu']} x {info['gpu']['type']}"
            user_line += f"{gpu_line:19}"
            user_line += "\t".join(disp_user_resource(job_info, res)
                           for res in RESOURCES)
            if not is_priority(job_info['partition']):
                s += colored(user_line, 'green')
            else:
                s += colored(user_line, 'red')
    # s += "\n"
    return s

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--gpu-only', action="store_true")
    parser.add_argument('--disp-users', action="store_true")
    parser.add_argument('--show-only', type=str, default=None)
    args = parser.parse_args()

    servers = parse_sinfo(exec(SINFO), args)
    if args.show_only is not None:
        for k in list(servers.keys()):
            if k not in priority_nodes[args.show_only]:
                del servers[k]
    usage = parse_gtop(exec(GTOP), servers)

    if args.disp_users:
        print(
            f"{'Server':25}   {'NetID':^9}   {'Partition':^17}   {'GPU':^19}{'CPU Usage':^12}\t{'GPU Usage':9}\tMemory Usage (GB) (P/D/I)")
    else:
        print(f"{'Server':25}{'GPU':19}{'CPU Usage':^12}\t{'GPU Usage':9}\tMemory Usage (GB) (P/D/I)")
    for server in sorted(list(usage.keys())):
        print(disp(server, usage[server], args.disp_users))

