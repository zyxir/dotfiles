$wslip = wsl bash -c "ip route show default" | %{ $_.Split(' ')[2]; }
wsl zsh -c "export DISPLAY=$wslip`:0.0 export LIBGL_ALWAYS_INDIRECT=1 && setsid emacs"