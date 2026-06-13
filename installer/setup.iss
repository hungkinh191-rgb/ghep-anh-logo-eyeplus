; Inno Setup script - tao bo cai dat Windows cho "Ghep Anh Logo EyePlus"
; Duoc bien dich tu dong tren GitHub Actions (xem .github/workflows/build-windows.yml)

#define AppName "Ghep Anh Logo EyePlus"
#define AppVersion "1.0"
#define ExeName "GhepAnhLogoEyePlus.exe"

[Setup]
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=EyePlus
DefaultDirName={autopf}\GhepAnhLogoEyePlus
DefaultGroupName=Ghep Anh Logo EyePlus
DisableProgramGroupPage=yes
OutputDir=..\installer_out
OutputBaseFilename=GhepAnhLogoEyePlus-Setup
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
Source: "..\dist\GhepAnhLogoEyePlus\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Ghep Anh Logo EyePlus"; Filename: "{app}\{#ExeName}"
Name: "{group}\Go cai dat Ghep Anh Logo EyePlus"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Ghep Anh Logo EyePlus"; Filename: "{app}\{#ExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#ExeName}"; Description: "Mo ung dung ngay"; Flags: nowait postinstall skipifsilent
