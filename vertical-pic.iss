#define MyAppName "Vertical PIC"
#define MyAppVersion "3.0.0"
#define MyAppExeName "VerticalPIC.exe"
#define MyAppPublisher "Industrias PICO"

[Setup]
AppId={{B91C8E21-D503-4F2A-B6A9-6A2B8B15D6F2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={commonpf64}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=.
OutputBaseFilename=Installer_{#MyAppName}
Compression=lzma
SolidCompression=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
; Ejecutable principal
Source: "dist\VerticalPic\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Archivos PyInstaller (--onedir) en subcarpeta _internal
Source: "dist\VerticalPic\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Opciones adicionales:"; Flags: checkedonce
Name: "autorun"; Description: "Iniciar {#MyAppName} al arrancar Windows"; GroupDescription: "Opciones adicionales:"; Flags: checkedonce

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
ValueName: "{#MyAppName}"; ValueType: string; \
ValueData: """{app}\{#MyAppExeName}"""; Tasks: autorun

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Iniciar {#MyAppName}"; Flags: nowait postinstall skipifsilent
