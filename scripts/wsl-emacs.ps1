# Create a shortcut of this script with this Target:
#   powershell.exe -ExecutionPolicy Bypass -File "/path/to/this/script"

# Wait until the Emacs service is ready.
# while ($true) {
#     $output = wsl systemctl --user show --property=ActiveState emacs
#     if ($output -eq "ActiveState=active") {
#         break
#     }
#     Start-Sleep -Seconds 0.2
# }

# The above snippet does work, but it was deleted because it causes too much
# delay and always print "Failed to connect to bus: No such file or directory".
# I didn't delve too deep into this problem, so I decided to manually start
# WSL before running this script.

# Start Emacs client.
$processOptions = @{
    FilePath = "wslg.exe"
    ArgumentList = "emacsclient --create-frame"
}
Start-Process @processOptions