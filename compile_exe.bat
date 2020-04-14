rem del "e:\sw\arch\war_magic_bot\war_magic\dist\war_magic" /S /F /Q
copy /Y war_magic.py WamyBoty.py
rem c:\Python37\Scripts\pyinstaller.exe --onefile WamyBoty.pyw -i "e:\sw\arch\war_magic_bot\war_magic\Bot.ico"
rem c:\Python37\Scripts\pyinstaller.exe  --noconsole --onefile WamyBoty.py -i "e:\sw\arch\war_magic_bot\war_magic\Bot.ico"
c:\Python37\Scripts\pyinstaller.exe  --onefile WamyBoty.py -i "e:\sw\arch\war_magic_bot\war_magic\Bot.ico"
copy /Y .\dist\WamyBoty.exe C:\wam\wamyboty.exe
start C:\wam\wamyboty.exe
rem copy /Y .\dist\war_magic.exe war_magic.exe
pause