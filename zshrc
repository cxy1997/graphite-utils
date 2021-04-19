module() { eval `/usr/bin/modulecmd zsh $*`; }
module use ~xc429/modulefiles

alias cuda10='module unload cuda cudnn && module load cuda/10.0 cudnn/v7.3-cuda-10.0'
alias cuda101='module unload cuda cudnn && module load cuda/10.1 cudnn/v7.6-cuda-10.1'
alias cuda9='module unload cuda cudnn && module load cuda/9.0 cudnn/v7.3-cuda-9.0'
alias cuda8='module unload cuda cudnn && module load cuda/8.0 cudnn/v5.1-cuda-8.0'
alias cuda102='module unload cuda cudnn && module load cuda/10.2 cudnn/v7.6-cuda-10.2'

alias gtop='ls -Art /share/nikola/export/graphite_usage/ | tail -n 1 | xargs -I % sh -c "cat /share/nikola/export/graphite_usage/%" | grep "RUNNING\|PENDING" |sort -k 1,1'
alias sq='python $HOME/bin/sq.py'
alias allo='python $HOME/bin/allo.py'
alias wn='watch -n 0.1 nvidia-smi'
alias si='sinfo -o %G,%N,%P'

alias torchver='python -c "import torch; print(\"torch:\", torch.__version__); print(\"cuda:\", torch.version.cuda); print(\"cudnn:\", torch.backends.cudnn.version())"'

export PATH=$PATH:$HOME/bin/:/usr/local/cuda/bin/
