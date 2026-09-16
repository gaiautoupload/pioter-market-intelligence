param([switch]$Install)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$scriptPath = Join-Path $PSScriptRoot 'daily.py'
if (-not $Install) {
  Write-Output '尚未安裝排程。加入 -Install 才會建立本機每日 07:30、18:30 工作。'
  Write-Output '電腦需開機、有網路，且使用者需登入。排程只更新本地資料與分析，不會自動發布網站。'
  exit 0
}
$taskName = 'Pioter-Capital-Daily'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
  throw '已有同名排程；為避免覆寫，請先檢視原排程。'
}
if ((Get-TimeZone).Id -ne 'Taipei Standard Time') { throw '此腳本使用台北時間，請先確認 Windows 時區。' }
$taskAction = New-ScheduledTaskAction -Execute $pythonPath -Argument ('-X utf8 "{0}"' -f $scriptPath) -WorkingDirectory $projectPath
$taskTriggers = @((New-ScheduledTaskTrigger -Daily -At '07:30'),(New-ScheduledTaskTrigger -Daily -At '18:30'))
$taskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $taskTriggers -Settings $taskSettings -Description '擷取官方行情、匯出研究包、查詢當下 vLLM 模型後分析' | Select-Object TaskName,State
