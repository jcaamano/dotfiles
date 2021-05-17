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
  # default modules: 'environment' 'terminal' 'editor' 'history' 'directory' 'spectrum' 'utility' 'completion' 'prompt'
  # from: https://github.com/jandamm/zgenom/blob/6ff785d403dd3f0d3b739c9c2d3508f49003441f/zgen.zsh#L750
  zgen prezto
  zgen prezto syntax-highlighting
  zgen prezto history-substring-search
  zgen prezto autosuggestions 

  # load other stuff
  zgen load junegunn/fzf shell

  # save
  zgen save
fi
