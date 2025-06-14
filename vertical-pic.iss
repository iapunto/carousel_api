; Instalador Vertical PIC - Solo archivos esenciales, sin privilegios de admin

[Setup]
AppName=Vertical PIC
AppVersion=2.5.36
DefaultDirName={userpf}\Vertical PIC
DefaultGroupName=Vertical PIC
OutputDir=.
OutputBaseFilename=Installer_VericalPIC
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
SetupIconFile="assets\favicon.ico"
LicenseFile=LICENSE
AppPublisher=Industrias Pico
AppPublisherURL=https://www.industriaspico.com
AppSupportURL=https://iapunto.com
AppUpdatesURL=https://iapunto.com
AppContact=desarollo@iapunto.com
AppCopyright=© 2025 Industrias Pico & IA Punto
AppComments=Sistema desarrollado por IA Punto Soluciones Tecnológicas

[Files]
Source: "dist\VerticalPIC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Vertical PIC"; Filename: "{app}\VerticalPIC.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\Vertical PIC"; Filename: "{app}\VerticalPIC.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Opciones adicionales:"

[Run]
Filename: "{app}\VerticalPIC.exe"; Description: "Iniciar Vertical PIC"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\assets"
Type: files; Name: "{app}\VerticalPIC.exe"
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\LICENSE"
Type: files; Name: "{app}\README.md"

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "VerticalPIC"; ValueData: "{app}\VerticalPIC.exe"; Flags: uninsdeletevalue
