@echo off
REM ============================================================================
REM run_all.bat - run the full FINN Santa Catarina pipeline on Windows
REM ----------------------------------------------------------------------------
REM Usage (from the project root, in cmd.exe or PowerShell):
REM   run_all.bat r          run via the R route
REM   run_all.bat python     run via the Python route
REM   run_all.bat r stack    also run the optional step 03 (stack years)
REM   run_all.bat analysis   reproduce the manuscript/report results and run the tests
REM
REM Requires Rscript.exe and/or python.exe on your PATH. Parameters come from
REM config\config.yml. Override interpreters by setting RSCRIPT / PYTHON first:
REM   set PYTHON=py -3.11
REM ============================================================================
setlocal
cd /d "%~dp0"

if "%RSCRIPT%"=="" set "RSCRIPT=Rscript"
if "%PYTHON%"==""  set "PYTHON=python"

set "ROUTE=%~1"
set "STACK=%~2"

if /I "%ROUTE%"=="r" goto :run_r
if /I "%ROUTE%"=="python" goto :run_py
if /I "%ROUTE%"=="py" goto :run_py
if /I "%ROUTE%"=="analysis" goto :run_analysis
goto :usage

:run_r
echo === FINN SC pipeline - R route ===
call "%RSCRIPT%" R\00_download_finn.R || goto :fail
call "%RSCRIPT%" R\01_convert_units.R || goto :fail
call "%RSCRIPT%" R\02_clip_region.R || goto :fail
if /I "%STACK%"=="stack" call "%RSCRIPT%" R\03_stack_years.R || goto :fail
call "%RSCRIPT%" R\04_aggregate_region.R || goto :fail
call "%RSCRIPT%" R\05_descriptive_analysis.R || goto :fail
goto :done

:run_py
echo === FINN SC pipeline - Python route ===
call "%PYTHON%" python\00_download_finn.py || goto :fail
call "%PYTHON%" python\01_convert_units.py || goto :fail
call "%PYTHON%" python\02_clip_region.py || goto :fail
if /I "%STACK%"=="stack" call "%PYTHON%" python\03_stack_years.py || goto :fail
call "%PYTHON%" python\04_aggregate_region.py || goto :fail
call "%PYTHON%" python\05_descriptive_analysis.py || goto :fail
goto :done

:run_analysis
echo === FINN SC analysis layer (route B) ===
call "%PYTHON%" python\run_analysis.py || goto :fail
call "%PYTHON%" -m pytest -q tests || goto :fail
goto :done

:usage
echo Usage: run_all.bat {r^|python^|analysis} [stack]
echo   r        run the R route
echo   python   run the Python route (alias: py)
echo   analysis reproduce the manuscript/report results and run the tests
echo   stack    also run the optional stack-years step (03)
exit /b 1

:fail
echo.
echo *** A step failed. See the message above. ***
exit /b 1

:done
echo.
echo === Pipeline complete. Outputs are in data\output\. ===
endlocal
