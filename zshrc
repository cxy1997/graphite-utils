# cuda
module() { eval `/usr/bin/modulecmd zsh $*`; }
module use ~xc429/modulefiles

alias cuda8='module unload cuda cudnn && module load cuda/8.0 cudnn/v5.1-cuda-8.0'
alias cuda9='module unload cuda cudnn && module load cuda/9.0 cudnn/v7.3-cuda-9.0'
alias cuda92='module unload cuda cudnn && module load cuda/9.2 cudnn/v7.6-cuda-9.2'
alias cuda10='module unload cuda cudnn && module load cuda/10.0 cudnn/v7.3-cuda-10.0'
alias cuda101='module unload cuda cudnn && module load cuda/10.1 cudnn/v7.6-cuda-10.1'
alias cuda102='module unload cuda cudnn && module load cuda/10.2 cudnn/v7.6-cuda-10.2'
alias cuda11='module unload cuda cudnn && module load cuda/11.0 cudnn/v8.0-cuda-11.0'
alias cuda113='module unload cuda cudnn && module load cuda/11.3 cudnn/v8.2-cuda-11.3'

# g2
alias g2top='python $HOME/bin/g2top.py --gpu-only'
export LD_LIBRARY_PATH=/home/xc429/lib:$LD_LIBRARY_PATH

# graphite
# alias gtop='ls -Art /share/nikola/export/graphite_usage/ | tail -n 1 | xargs -I % sh -c "cat /share/nikola/export/graphite_usage/%" | grep "RUNNING\|PENDING" |sort -k 1,1'
alias sq='python $HOME/bin/sq.py'
alias allo='python $HOME/bin/allo.py'
alias wn='watch -n 0.1 "nvidia-smi | grep MiB"'
alias kq='sacct --format=User%10,partition%20,NodeList%25,State,AllocTRES%50,Time -a --units=G| grep RUNNING | grep billing | grep kilian'
alias si='sinfo -o %G,%N,%P'

alias torchver='python -c "import sys, torch; print(\"python:\", sys.version.replace(\"\\n\", \" \")); print(\"torch:\", torch.__version__); print(\"cuda:\", torch.version.cuda); print(\"cudnn:\", torch.backends.cudnn.version())"'

export PATH=$PATH:$HOME/bin/:/usr/local/cuda/bin/
