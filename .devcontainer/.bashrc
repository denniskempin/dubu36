export LS_OPTIONS='-F --color=auto'
alias ls='ls $LS_OPTIONS'
if [ -z "${WORKSPACE_DIR:-}" ]; then
  if [ "${CODESPACES:-}" = "true" ]; then
    export WORKSPACE_DIR="$HOME/workspace/zmk"
  elif [ -d /workspace ]; then
    export WORKSPACE_DIR="/workspace"
  else
    export WORKSPACE_DIR="$(pwd)"
  fi
fi
if [ -f "$WORKSPACE_DIR/.zmk-workspace/zephyr/zephyr-env.sh" ]; then
  source "$WORKSPACE_DIR/.zmk-workspace/zephyr/zephyr-env.sh"
fi

