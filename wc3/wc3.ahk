;;;HOW TO SETUP;;; First download and install Autohotkey.com (very simple)
;;;;;Then Create New Autohotkey Script and copy this into the new .AHK file
;;;;;OR simply download this file, rename and erase .ahk.TXT to just .AHK
;;;;;Place in your WC3 folder and create shortcut on desktop
;;;;;Might require right-click and setting to Run as Admin
;;;;;In WC3 press NumLock to pause Script on/off for chat
;;;;;Now your Invetory hotkeys are switched to Alt + QWEASD
;;;;;Also disables WinKey or Alt+QQ from closing your game
;;;;;Any Hotkeys can be modified to your liking at the very bottom
;;;;;If mouse supports extra buttons can be remapped at bottom


#SingleInstance force		;force a single instance
#HotkeyInterval 0		;disable the warning dialog if a key is held down
#InstallKeybdHook		;Forces the unconditional installation of the keyboard hook
#UseHook On			;might increase responsiveness of hotkeys
#MaxThreads 20			;use 20 (the max) instead of 10 threads
SetBatchLines, -1		;makes the script run at max speed
SetKeyDelay , -1, -1		;faster response (might be better with -1, 0)
;Thread, Interrupt , -1, -1	;not sure what this does, could be bad for timers
SetTitleMatchMode Regex
SetDefaultMouseSpeed, 0 ;Move the mouse faster for mouse moving commands

IfExist, Warcraft III.exe
  menu, tray, Icon, Warcraft III.exe, 1, 1

;;;;; Variables ;;;;;
bInChatRoom := False
bHealthBarOn := False
Return ; End Auto-Execute Section

#ifWinActive ahk_class ((WarcraftIII)|(OsWindow)|(Qt5QWindowIcon))

;;;;; Enable/disable all hotkeys ;;;;;

;; Escape will cancel chatting, so turn the hotkeys back on
*NumLock::
*Insert::
Suspend, Permit
bInChatRoom := not bInChatRoom
if (bInChatRoom == True)
{
  Suspend, On
  SetNumLockState, Off
  SoundPlay,*64
}
else
{
  Suspend, Off
  SetNumLockState, On
  SoundPlay,*48
}
return


; Hotkeys Remapper:

; Disable Toggles
Lwin::return
<!r::return
<!t::return
<!f::return
;;to enable formation toggle add ;; to the line above

; Inventory Keys:
!q::SendInput, {Numpad7}
+!q::SendInput, +{Numpad7}
!w::SendInput, {Numpad8}
+!w::SendInput, +{Numpad8}
!a::SendInput, {Numpad4}
+!a::SendInput, +{Numpad4}
!s::SendInput, {Numpad5}
+!s::SendInput, +{Numpad5}
!z::SendInput, {Numpad1}
+!z::SendInput, +{Numpad1}
!e::SendInput, {Numpad2}
+!e::SendInput, +{Numpad2}

; User Specified Hotkeys:
t::6
g::7
b::SendInput, {Backspace}
y::9
h::0

;;LCtrl::Space
;;Space::LCtrl
;To swap the Ctrl key with the Spacebar just remove the ;; from the 2 lines above