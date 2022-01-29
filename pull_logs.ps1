Param (
    [parameter(mandatory=$True)] $Date,
    $Time,
    $Dir = (Join-Path $PSScriptRoot 'raw/')
)

$strs = adb shell ls '/sdcard/hasclogs/' | Select-String -Pattern "$Date.*-.*$Time.*.log"

foreach ($s in $strs) {
    adb pull "/sdcard/hasclogs/$($s.Line)" $Dir
}
