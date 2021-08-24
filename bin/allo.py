import argparse
import random
import string
import os
from datetime import datetime

time_str = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
log_dir = os.path.expanduser("~/slurm/logs")
file_dir = os.path.expanduser("~/slurm/files")
os.makedirs(log_dir, exist_ok=True)
os.makedirs(file_dir, exist_ok=True)

parser = argparse.ArgumentParser()
parser.add_argument('--cpu', type=int, default=4)
parser.add_argument('--gpu', type=int, default=1)
parser.add_argument('--mem', type=int, default=64)
parser.add_argument('--time', type=int, default=14)
parser.add_argument('--node', type=str, default=None)
parser.add_argument('--p', type=str, default="default_partition")
args = parser.parse_args()
port = random.randint(32133, 53112)
node="""#!/bin/bash
#SBATCH --job-name=jjob
#SBATCH -o {3}/{4}-job-%j.out                              # Name of stdout output file (%j expands to jobId)
#SBATCH -e {3}/{4}-job-%j.err                             # Name of stderr output file (%j expands to jobId)
#SBATCH --nodes=1
#SBATCH --mem={0}GB
#SBATCH -n {1}
#SBATCH --partition={5}  --gres=gpu:{2}        # Which queue it should run on.
""".format(args.mem, args.cpu, args.gpu, log_dir, time_str, args.p)

if args.time is not None:
    args.time = args.time * 24 * 60
    node += f"#SBATCH -t {args.time}                                          # Run time (hh:mm:ss)\n"
if args.node is not None:
    node += "#SBATCH --nodelist={}\n".format(args.node)

node += """cd $HOME
export XDG_RUNTIME_DIR=""
#Pick a random or predefined port
#Forward the picked port to the prince on the same port. Here log-x is set to be the prince login node.
/home/yy785/.linuxbrew/bin/autossh -M 0 -o "StrictHostKeyChecking=no" -o "ServerAliveInterval 60" -o "ServerAliveCountMax 3" -NfR {0}:0.0.0.0:{0} g2-login.coecis.cornell.edu
#Start the notebook
. /home/yy785/anaconda3/etc/profile.d/conda.sh
conda activate base
export SHELL=/bin/zsh
jupyter notebook --no-browser --port {0}
""".format(port)

file_name = '{}-{}'.format(time_str, args.node)
with open('{}/{}'.format(file_dir, file_name), 'w') as f:
    f.write(node)

r_id = os.popen('sbatch {}/{}'.format(file_dir, file_name)).read().strip().split(' ')[-1]
print('file: {}/{}\tid: {}\tport: {}'.format(file_dir, file_name, r_id, port))
with open(f'{log_dir}/jupyter.txt', 'a') as f:
    f.write('file: {}/{}\tid: {}\tport: {}\n'.format(file_dir, file_name, r_id, port))
print('g2pt {}'.format(port))
