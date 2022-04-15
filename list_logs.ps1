Param (
    $Date,
    $Time
)

$strs = adb shell run-as 'jp.uclab.hasc.android.logger' ls 'app_hasclogs/' | Select-String -Pattern "$Date.*-.*$Time.*.log"

"-- internal --"
foreach ($s in $strs) {
    $s.Line
}

""

$strs = adb shell ls '/sdcard/hasclogs/' | Select-String -Pattern "$Date.*-.*$Time.*.log"

"-- external --"
foreach ($s in $strs) {
    $s.Line
}
