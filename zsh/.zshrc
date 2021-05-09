if [[ ! -s "${ZDOTDIR:-$HOME}/.zgenom/zgenom.zsh" ]]; then
  echo "Cloning zgenom"
  git clone --depth 1 https://github.com/jandamm/zgenom.git "${ZDOTDIR:-$HOME}/.zgenom"	
fi

export ZGEN_RESET_ON_CHANGE=(${ZDOTDIR:-$HOME}/.zshrc)
source "${ZDOTDIR:-$HOME}/.zgenom/zgenom.zsh"

if ! zgen saved; then
  echo "Creating a zgen save"

  # prezto configuration, see https://github.com/sorin-ionescu/prezto/blob/master/runcoms/zpreztorc
  zgen prezto '*:*' color 'yes'
  zgen prezto editor key-bindings 'emacs'
  zgen prezto prompt theme 'pure'

  # load prezto
  zgen prezto
  zgen prezto history-substring-search
  zgen prezto syntax-highlighting

  # load other stuff
  zgen load junegunn/fzf shell
  zgen load tarruda/zsh-autosuggestions

  # save
  zgen save
fi
