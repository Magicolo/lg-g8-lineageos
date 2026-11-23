param(
    [Parameter(Mandatory)][string]$Adb,
    [Parameter(Mandatory)][string]$Phase,
    [string]$Serial
)
$ErrorActionPreference = 'Stop'
$selector = @()
if ($Serial) { $selector = @('-s', $Serial) }
$target = & $Adb @selector shell getprop ro.product.device
if ($LASTEXITCODE -ne 0 -or "$target".Trim() -ne 'alphaplus_lao_com') {
    throw 'Connect the Canadian LG G8 before recording a battery sample.'
}
$collector = @'
printf "build="
getprop ro.build.version.incremental
printf "slot="
getprop ro.boot.slot_suffix
printf "uptime_seconds="
cut -d " " -f 1 /proc/uptime
printf "cpu_idle_override="
tr " " "\n" < /proc/cmdline | grep "^lpm_levels.sleep_disabled=" || true
dumpsys battery | grep -E "powered:|Charge counter:|health:|level:|temperature:|voltage:|capacity:|IsStatusOverride:"
dumpsys thermalservice | grep -E "Thermal Status:|HAL Ready:"
dumpsys power | grep -E "mWakefulness=|mStayOn=|mScreenOffTimeoutSetting="
dumpsys deviceidle | grep -E "mLightEnabled=|mState=.*mLightState=|mCharging="
for state in /sys/devices/system/cpu/cpu[0-7]/cpuidle/state[0-9]; do
    [ -r "$state/time" ] || continue
    printf "%s name=%s count=%s time_us=%s\n" "$state" \
      "$(tr -d "\r\n" < "$state/name")" "$(cat "$state/usage")" "$(cat "$state/time")"
done
dumpsys batterystats --charged |
    grep -E "Time on battery:|Screen on:|Estimated battery capacity:|Last learned battery capacity:"
'@
$phaseLabel = $Phase -replace '[\r\n]', ' '
'{0} phase={1}' -f (Get-Date -Format o), $phaseLabel
$collector.Replace("`r`n", "`n") | & $Adb @selector shell sh -s
if ($LASTEXITCODE -ne 0) {
    throw 'The handset battery sample failed.'
}
