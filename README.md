# Graphite Utils

## Installation
By default, [Oh My Zsh](https://github.com/ohmyzsh/ohmyzsh) is used.
1. Add [ssh congurations](./ssh_config) to local `~/.ssh/config`
2. Add [port forwarding functions](./local_zshrc) to local `~/.zshrc`
3. Add [zsh scripts](./zshrc) to `g2`'s `~/.zshrc`
4.  Copy folders to `g2`
    ```bash
    scp -r bin g2:~/
    scp -r lib g2:~/
    ```
## Usage
### `g2` side
| Command | Function |
| :---- | :---- |
| `cuda*` | switch cuda version |
| `g2top` | display gpu/cpu/mem availability |
| `allo [--cpu $Ncpus] [--gpu $Ngpus] [--mem $Ngb] [--time $Ndays] [--node $nodename] [--p $partition]` | submit new job |
| `sq` | display your jobs |
| `wn` | monitor gpu status |
| `kq` | show running jobs in `kilian` queue |
| `torchver` | display pytorch version |

### local side
| Command | Function |
| :---- | :---- |
| `g2pt $portnumber` | connect to jupyter notebook via g2 |
| `cpt [$portnumber]` | clear given port (or all ports by default) |
