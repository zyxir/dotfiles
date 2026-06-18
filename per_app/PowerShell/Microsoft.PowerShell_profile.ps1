<#
This is the CurrentUserCurrentHost PowerShell profile, usually placed at:
$HOME\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1
#>

# Enable UTF-8
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding

# Use Emacs style shortcuts
Import-Module PSReadLine
Set-PSReadLineOption -EditMode Emacs
if ((Get-Module PSReadLine).Version -ge [Version]"2.2.0") {
    Set-PSReadLineOption -PredictionSource History
    Set-PSReadLineOption -Colors @{ InlinePrediction = '#666666' }
}

# Set up proxy if the proxy port is listening
$proxyPort = 7897
$proxyAvailable = $false
try {
    $client = New-Object System.Net.Sockets.TcpClient("127.0.0.1", $proxyPort)
    $client.Close()
    $proxyAvailable = $true
} catch {
    $proxyAvailable = $false
}

if ($proxyAvailable) {
    $env:http_proxy = "http://127.0.0.1:${proxyPort}"
    $env:https_proxy = "http://127.0.0.1:${proxyPort}"
    $env:no_proxy = "localhost,127.0.0.1,::1"
    $env:HTTP_PROXY = "http://127.0.0.1:${proxyPort}"
    $env:HTTPS_PROXY = "http://127.0.0.1:${proxyPort}"
    $env:NO_PROXY = "localhost,127.0.0.1,::1"
}
