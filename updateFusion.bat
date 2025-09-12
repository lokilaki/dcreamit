@echo on

set "StreamerDir=c:\Program Files\Autodesk\webdeploy\meta\streamer" 

setlocal
FOR /F %%i IN ('dir /A:D /B /oN "%StreamerDir%"') DO (
      SET a=%%i 
) 

endlocal & set StreamerVer=%a%

"%StreamerDir%\%StreamerVer%\streamer.exe" --globalinstall --process update --quiet

del C:\Users\SENAI\Desktop\atualizadorFusion.bat

shutdown -s -t 60
