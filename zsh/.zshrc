if [[ ! -s "${ZDOTDIR:-$HOME}/.zgenom/zgenom.zsh" ]]; then
  echo "Cloning zgenom"
  git clone --depth 1 https://github.com/jandamm/zgenom.git "${ZDOTDIR:-$HOME}/.zgenom"	
fi

export ZGEN_RESET_ON_CHANGE=(${ZDOTDIR:-$HOME}/.zshrc)
source "${ZDOTDIR:-$HOME}/.zgenom/zgenom.zsh"

if ! zgenom saved; then
  echo "Creating a zgenom save"

  # prezto configuration, see https://github.com/sorin-ionescu/prezto/blob/master/runcoms/zpreztorc
  zgenom prezto '*:*' color 'yes'
  zgenom prezto editor key-bindings 'emacs'
  zgenom prezto prompt theme 'pure'

  # load prezto
  # default modules: 'environment' 'terminal' 'editor' 'history' 'directory' 'spectrum' 'utility' 'completion' 'prompt'
  # from: https://github.com/jandamm/zgenom/blob/6ff785d403dd3f0d3b739c9c2d3508f49003441f/zgen.zsh#L750
  zgenom prezto
  zgenom prezto syntax-highlighting
  zgenom prezto history-substring-search
  zgenom prezto autosuggestions 

  # load other stuff
  zgenom load junegunn/fzf shell
  zgenom load mattmc3/zshrc.d

  # save
  zgenom save
fi
