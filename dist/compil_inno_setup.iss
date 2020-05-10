; -- Example1.iss --     ;;;;;;;;
;;;; SEE THE DOCUMENTATION FOR DETAILS ON CREATING .ISS SCRIPT FILES!

[Setup]
AppId={{9119A44D-E936-4BD3-B973-26333118776F}
VersionInfoCompany=Botovod
VersionInfoProductName=WamyBoty
VersionInfoVersion=0.28
AppVerName=WamyBoty 0.28
OutputBaseFilename=wamyboty_setup
AppName=WamyBoty
AppPublisher=Botovod
DefaultDirName=C:\wam
DefaultGroupName=WamyBoty
UninstallDisplayIcon={app}\WamyBoty.exe
Compression=lzma
SolidCompression=yes
LicenseFile=license-rus.txt

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
;Name: "autorrun"; Description: "{cm:users_autorun}"; GroupDescription: "{cm:AdditionalIcons}"

[Dirs]
Name: "{app}\stats"
Name: "{app}\twins"

[Files]
Source: "wamyboty.exe"; DestDir: "{app}"; Flags: ignoreversion restartreplace
Source: "accs_example.txt"; DestDir: "{app}"; Flags: ignoreversion restartreplace
Source: "..\images\*.png";       DestDir: "{app}\images"; Flags: ignoreversion restartreplace

;Name: "{app}\bin"
[Code]
var
  StaticText: TNewStaticText;
  isWin7Wista : bool;
  
function MyConst(Param: String): String;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  if Version.NTPlatform and (Version.Major = 6) then begin
  isWin7Wista:=true;
  Result := ExpandConstant('{sd}');
  end else begin
    isWin7Wista:=false;
    Result := ExpandConstant('{pf}');
  end;
end;

[Icons]
Name: "{group}\WamyBoty"; Filename: "{app}\WamyBoty.exe"
Name: "{group}\{cm:UninstallProgram,WamyBoty}"; Filename: "{uninstallexe}"
;Name: "{group}\UnInstall"; Filename: "{app}\uninstall.exe"
Name: "{userdesktop}\WamyBoty"; Filename: "{app}\WamyBoty.exe"; Tasks: desktopicon

[Run]
;Filename: "{app}\AutoClicker.exe"; Parameters: "/ASSOC"; StatusMsg: "{cm:AssocingFileExtension,AutoClickExtreme,.aip}"; Tasks: "fileassoc";MinVersion: 3.1,3.0;
Filename: "{app}\WamyBoty.exe"; Description: "Запустить программу сейчас"; Flags: postinstall nowait skipifsilent
;Filename: {app}\AutoClicker.exe; Parameters : -Register; Tasks: assoc
;[Tasks]
;Name: "fileassoc"; Description: "{cm:AssocFileExtension,AutoClickExtreme,.aip}";MinVersion: 3.1,3.0;
;Name: assoc; Description: Ассоциировать aip-файлы Записей с AutoClickExtreme




