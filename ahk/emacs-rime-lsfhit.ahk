;; 在 Emacs 中，单独按下左 Shift 将触发 Ctrl+\，从而切换 emacs-rime 之中西文。

#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

SetTitleMatchMode, 1
#IfWinActive ahk_exe vcxsrv.exe
#IfWinActive WSL` Emacs
#IfWinActive ZyEmacs` on` WSL
Shift & AppsKey::Return
Shift::Send ^\