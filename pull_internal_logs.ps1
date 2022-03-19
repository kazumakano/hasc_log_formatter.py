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

$strs = adb shell run-as 'jp.uclab.hasc.android.logger' ls 'app_hasclogs/' | Select-String -Pattern "$Date.*-.*$Time.*.log"

foreach ($s in $strs) {
    $bytes = ((adb shell run-as 'jp.uclab.hasc.android.logger' wc -c "app_hasclogs/$($s.Line)") -Split ' ')[0]
    "app_hasclogs/$($s.Line) ($bytes bytes)"
    adb shell run-as 'jp.uclab.hasc.android.logger' cat "app_hasclogs/$($s.Line)" > (Join-Path $Dir $s.Line)
}
