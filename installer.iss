[Setup]
AppName=Kanji Writer
AppVersion=1.0
AppPublisher=Kanji Writer
DefaultDirName={autopf}\KanjiWriter
DefaultGroupName=Kanji Writer
OutputDir=release
OutputBaseFilename=KanjiWriter-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
SetupIconFile=assets\logo.ico
UninstallDisplayIcon={app}\KanjiWriter.exe

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "dist\KanjiWriter.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Kanji Writer"; Filename: "{app}\KanjiWriter.exe"
Name: "{autodesktop}\Kanji Writer"; Filename: "{app}\KanjiWriter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\KanjiWriter.exe"; Description: "Launch Kanji Writer"; Flags: nowait postinstall skipifsilent
