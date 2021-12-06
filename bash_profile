preferred_shell=
if [ -x /usr/bin/zsh ]; then
  preferred_shell=/usr/bin/zsh
fi

if [ -n "$preferred_shell" ]; then
  case $- in
    *i*) SHELL=$preferred_shell; export SHELL; exec "$preferred_shell";;
  esac
fi
