@echo off
REM 国元证券 OA新闻 → 门户 同步脚本
REM 用于 Windows 计划任务
cd /d "%~dp0"
C:\Users\11039\.workbuddy\binaries\python\envs\xlsx\Scripts\python.exe sp2portal_sync.py
