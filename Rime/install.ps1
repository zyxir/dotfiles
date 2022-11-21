$scriptPath = $MyInvocation.MyCommand.Path
$dir = Split-Path $scriptPath
Push-Location $dir

$rimeDir = "$Env:USERPROFILE\AppData\Roaming\Rime"
$srcList = @(
    "cangjie5\*"
    "cangjie6\*"
    "double_pinyin\*"
    "luna_pinyin\*"
    "default.custom.yaml"
    "weasel.custom.yaml"
)
foreach ($src in $srcList) {
    Copy-Item -Path $src -Destination $rimeDir -Verbose
}
Copy-Item -Path "$rimeDir\cangjie6_dl.schema.yaml" -Destination "$rimeDir\cangjie6.schema.yaml" -Verbose -Force

Pop-Location