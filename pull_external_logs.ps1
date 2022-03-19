Param (
    [parameter(mandatory=$True)] $Date,
    $Time,
    $Dir = (Join-Path $PSScriptRoot 'raw/')
)

if (!(Test-Path $Dir)) {
    "$Dir was not found"
    exit
}

if (!(Get-Item $Dir).PSIsContainer) {
    "$Dir is not directory"
    exit
}

$strs = adb shell ls '/sdcard/hasclogs/' | Select-String -Pattern "$Date.*-.*$Time.*.log"

foreach ($s in $strs) {
    adb pull "/sdcard/hasclogs/$($s.Line)" $Dir
}
