@ECHO OFF
SETLOCAL EnableDelayedExpansion
:START
CLS
SET n=0
FOR /F "tokens=*" %%A IN (C:\Windows\BC_Model.txt) DO (
SET /A n=n+1
SET _fav!n!=%%A
ECHO !n! %%A
)
ECHO.
SET /P MODEL=Choose BC MODEL Name (%M%:%MODEL%): 
FOR /L %%f IN (1,1,!n!) DO (
IF /I '%MODEL%'=='%%f' SET M=%%f
)
SET n=0
FOR /F "tokens=*" %%A IN (C:\Windows\BC_Model.txt) DO (
SET /A n=n+1
IF !n!==%M% SET MODEL=%%A
)
ECHO.
SET /P MODE=EXIT(2) - BC-SL-R(1) - BC-SL(0)(ENTER)(%MODE%): 
IF "%MODE%"=="" GOTO BC-SL
IF "%MODE%"=="0" GOTO BC-SL
IF "%MODE%"=="1" GOTO BC-SL-R
IF "%MODE%"=="2" GOTO EXIT
ECHO.
:BC-SL
SET MODELNAME=%MODEL% #######################################
SET _MODEL_=%MODELNAME:~0,33%
ECHO.
CLS && ECHO ###################################################
ECHO ### BC-SL ####### R E C O R D I N G ###############
ECHO ################# %_MODEL_%
ECHO ###################################################
ECHO.
COLOR 0F
cd/
cd Python27
STREAMLINK "https://en.bongacams.com/%MODEL%/"
ECHO.
PAUSE
GOTO START
:BC-SL-R
SET MODELNAME=%MODEL% #######################################
SET _MODEL_=%MODELNAME:~0,33%
ECHO.
CLS && ECHO ###################################################
ECHO ### BC-SL-R ##### R E C O R D I N G ###### 24/7 ###
ECHO ################# %_MODEL_%
ECHO ###################################################
ECHO.
COLOR 0F
cd/
cd Python27
STREAMLINK "https://en.bongacams.com/%MODEL%/"
TIMEOUT 30
GOTO BC-SL-R
:EXIT
GOTO :EOF
ENDLOCAL
