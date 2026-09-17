param([switch]$Install, [switch]$Publish)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$scriptPath = Join-Path $PSScriptRoot 'daily.py'
if (-not $Install) {
  Write-Output 'Not installed. Add -Install to create the 08:00 and 18:00 local tasks.'
  Write-Output 'Add -Publish only after a GitHub remote named github is configured.'
  exit 0
}
$taskName = 'Pioter-Capital-Daily'
if ((Get-TimeZone).Id -ne 'Taipei Standard Time') {
  throw 'This schedule expects the Windows time zone to be Taipei Standard Time.'
}
$publishArgument = if ($Publish) { ' --publish' } else { '' }
$dailyArgs = '-X utf8 "{0}"{1}' -f $scriptPath, $publishArgument
$taskAction = New-ScheduledTaskAction -Execute $pythonPath -Argument $dailyArgs -WorkingDirectory $projectPath
$taskTriggers = @(
  (New-ScheduledTaskTrigger -Daily -At '08:00'),
  (New-ScheduledTaskTrigger -Daily -At '18:00')
)
$taskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $taskTriggers -Settings $taskSettings -Description 'Refresh official market data and validated vLLM analysis at 08:00 and 18:00 Asia/Taipei.' -Force | Select-Object TaskName, State
