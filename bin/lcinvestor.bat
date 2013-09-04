@echo off
set SCRIPT_PATH=%~dp0
set PYSCRIPT="%SCRIPT_PATH%lcinvestor"
call python %PYSCRIPT% %*