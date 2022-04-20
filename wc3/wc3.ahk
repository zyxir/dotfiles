#NoEnv  ; Recommended for performance and compatibility with future AutoHotkey releases.
; #Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input  ; Recommended for new scripts due to its superior speed and reliability.
SetWorkingDir %A_ScriptDir%  ; Ensures a consistent starting directory.

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Copied from https://pastebin.com/21gXFsXJ
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;;;;; Enable/disable using NUMLOCK ;;;;;
~*Enter::
~*NumpadEnter::
Suspend, Permit
if (bInChatRoom == True)
  return
Suspend
if (A_IsSuspended == true)
{
  SetNumLockState, Off
}
else
{
  SetNumLockState, On
  SoundPlay,*48
}
return
 
;; Escape will cancel chatting, so turn the hotkeys back on
~*Esc::
Suspend, Permit
if (bInChatRoom == True)
  return
Suspend, Off
SetNumLockState, On
return
 
*NumLock::
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
 
; Disable Windows Key and AltQQ GG
Lwin::return
<!q::return
 
; Mini-Map Toggles
<!g::<!g
<!r::return
<!t::return
<!a::return
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
CapsLock::Send, {Backspace}
+CapsLock::Send, +{Backspace}
 
; Xbutton1::F1
; Xbutton2::Numpad7
; Mbutton::Tab
; these^ are middle mouse and extra mouse buttons
 
;;LCtrl::Space
;;Space::LCtrl
;To swap the Ctrl key with the Spacebar just remove the ;; from the 2 lines above

;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; Written by Zyxir.
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

;; 