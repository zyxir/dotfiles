$wslip = wsl bash -c "cat /etc/resolv.conf | grep -oP '(?<=nameserver\ ).*'"

wsl bash --login -c "export DISPLAY=$wslip`:0.0 export LIBGL_ALWAYS_INDIRECT=1 && setsid emacs"