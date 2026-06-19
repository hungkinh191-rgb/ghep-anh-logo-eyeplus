; Inno Setup script - tao bo cai dat Windows cho "Video Factory"
; Bien dich tu dong tren GitHub Actions (xem .github/workflows/build-video-factory.yml)

#define AppName "Video Factory"
#define AppVersion "1.0"
#define ExeName "VideoFactory.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=EyePlus
DefaultDirName={autopf}\VideoFactory
DefaultGroupName=Video Factory
DisableProgramGroupPage=yes
OutputDir=..\installer_out
OutputBaseFilename=VideoFactory-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; Cho phep cai khong can quyen admin (cai vao thu muc nguoi dung)
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Tao bieu tuong tren man hinh Desktop"; Flags: unchecked

[Files]
; Lay toan bo thu muc PyInstaller build ra (che do --onedir)
Source: "..\dist\VideoFactory\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Video Factory"; Filename: "{app}\{#ExeName}"
Name: "{group}\Go cai dat Video Factory"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Video Factory"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "Mo ung dung ngay"; Flags: nowait postinstall skipifsilent
