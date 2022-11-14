@REM 此腳本用於啓動 WSL (Ubuntu-20.04) 中的 Emacs。

start "" wsl -d Ubuntu bash -c "export DISPLAY=127.0.0.1:0.0 && export LIBGL_ALWAYS_INDIRECT=1 && setsid emacsclient -c -a emacs"
