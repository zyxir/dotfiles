$scriptPath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptPath
Push-Location $dir

$rimeDir = "$Env:USERPROFILE\AppData\Roaming\Rime"
$srcList = @(
    "cangjie5\*"
    "cangjie6\*"
    "double_pinyin\*"
    "default.custom.yaml"
    "weasel.custom.yaml"
)
foreach ($src in $srcList) {
    Copy-Item -Path $src -Destination $rimeDir -Verbose
}

Pop-Location