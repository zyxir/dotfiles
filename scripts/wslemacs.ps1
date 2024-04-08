# Create a shortcut of this script with this Target:
#   powershell.exe -ExecutionPolicy Bypass -File "/path/to/this/script"

# In order to run this correctly, the wslemacs script should be installed inside
# the WSL, which should be done by running the install.py script inside the WSL.

# Start Emacs client.
$processOptions = @{
    FilePath = "wslg.exe"
    ArgumentList = @("--user", "zyxir", "emacs")
}
Start-Process @processOptions
