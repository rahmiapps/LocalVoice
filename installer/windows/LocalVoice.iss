#define MyAppName "LocalVoice"
#define MyAppVersion "2.1.1"
#define MyAppPublisher "Rahmi Apps"
#define MyAppExeName "LocalVoice.exe"

[Setup]
AppId={{4A1D8D84-4F6B-4A5C-A228-7B70A841CC01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=LocalVoice-Setup-Windows-x64
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
SetupIconFile=..\..\resources\localvoice.ico
WizardImageFile=..\..\resources\installer-wizard.bmp
WizardSmallImageFile=..\..\resources\installer-small.bmp
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\LocalVoice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\LocalVoice - Sprache auswählen - Choose language"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--choose-language"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent


[CustomMessages]
german.RemoveUserDataPrompt=Möchtest du zusätzlich alle LocalVoice-Einstellungen, Modelle, Verläufe, Wörterbücher und Aufnahmen dieses Windows-Benutzers löschen? Wähle Nein, um deine Daten für eine spätere Neuinstallation zu behalten.
english.RemoveUserDataPrompt=Do you also want to delete all LocalVoice settings, models, history, dictionaries and recordings for this Windows user? Choose No to keep your data for a later reinstall.

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if MsgBox(ExpandConstant('{cm:RemoveUserDataPrompt}'), mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree(ExpandConstant('{userappdata}\Rahmi Apps\LocalVoice'), True, True, True);
      DelTree(ExpandConstant('{localappdata}\Rahmi Apps\LocalVoice'), True, True, True);
      DelTree(ExpandConstant('{userappdata}\LocalVoice'), True, True, True);
      DelTree(ExpandConstant('{localappdata}\LocalVoice'), True, True, True);
    end;
  end;
end;
