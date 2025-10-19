<#
This is the CurrentUserCurrentHost PowerShell profile, usually placed at:
$HOME\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
#>

# Enable UTF-8
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

# Use Emacs style shortcuts
Import-Module PSReadLine
Set-PSReadLineOption -EditMode Emacs
