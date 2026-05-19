@echo off
echo 正在创建 Hotspot Agent 计划任务（每天 09:00 运行）...
powershell -Command "$action = New-ScheduledTaskAction -Execute 'E:\conda_envs\hotspot-agent\python' -Argument 'E:\hotspot-agent\main.py'; $trigger = New-ScheduledTaskTrigger -Daily -At 9:00AM; $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive; Register-ScheduledTask -TaskName 'HotspotAgent' -Action $action -Trigger $trigger -Principal $principal -Force; Write-Host '完成！任务 HotspotAgent 已注册'"
pause
