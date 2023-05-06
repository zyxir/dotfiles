# Enable UTF-8.
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

# Use Emacs style shortcuts.
Import-Module PSReadLine
Set-PSReadLineOption -EditMode Emacs
