; Instalador Vertical PIC - Instalación completa con Python portable y servicios

#define MyAppName "Vertical PIC"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "Industrias PICO"
#define MyAppURL "https://www.industriaspico.com/"

[Setup]
AppId={{B91C8E21-D503-4F2A-B6A9-6A2B8B15D6F2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={commonpf64}\VerticalPIC
DefaultGroupName={#MyAppName}
OutputDir=.
OutputBaseFilename=Installer_VerticalPIC
SetupIconFile=assets\favicon.ico
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64os
ArchitecturesAllowed=x64os
WizardStyle=modern
; Usar imágenes por defecto de Inno Setup
;WizardImageFile=assets\logo.png
;WizardSmallImageFile=assets\logo.png

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "installbackend"; Description: "Instalar servicio Backend (recomendado)"; GroupDescription: "Servicios Windows:"; Flags: checkedonce
Name: "installwebapp"; Description: "Instalar servicio Web App"; GroupDescription: "Servicios Windows:"; Flags: unchecked

[Files]
; Archivos principales del proyecto
Source: "main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "web_remote_control.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "api.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "wsgi.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "plc_cache.py"; DestDir: "{app}"; Flags: ignoreversion

; Carpetas del proyecto
Source: "commons\*"; DestDir: "{app}\commons"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "controllers\*"; DestDir: "{app}\controllers"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "models\*"; DestDir: "{app}\models"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "gui\*"; DestDir: "{app}\gui"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Python portable y herramientas
Source: "python_portable\*"; DestDir: "{app}\python_portable"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "tools\*"; DestDir: "{app}\tools"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentación
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\python_portable\python.exe"; Parameters: """{app}\main.py"""; WorkingDir: "{app}"
Name: "{group}\Documentación"; Filename: "{app}\docs"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\python_portable\python.exe"; Parameters: """{app}\main.py"""; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Instalar servicios si fueron seleccionados
Filename: "{app}\tools\install_backend_service.bat"; Description: "Instalar servicio Backend"; Flags: postinstall runascurrentuser shellexec; Tasks: installbackend
Filename: "{app}\tools\install_webapp_service.bat"; Description: "Instalar servicio Web App"; Flags: postinstall runascurrentuser shellexec; Tasks: installwebapp

[UninstallRun]
; Desinstalar servicios
Filename: "{app}\tools\uninstall_backend_service.bat"; Flags: runhidden waituntilterminated
Filename: "{app}\tools\uninstall_webapp_service.bat"; Flags: runhidden waituntilterminated

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
var
  ResultCode: Integer;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Iniciar el servicio después de la instalación
    Exec(ExpandConstant('{sys}\net.exe'), 'start VerticalPIC_Backend', '', SW_HIDE, ewWaitUntilIdle, ResultCode);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    // Detener el servicio antes de desinstalar
    Exec(ExpandConstant('{sys}\net.exe'), 'stop VerticalPIC_Backend', '', SW_HIDE, ewWaitUntilIdle, ResultCode);
    Exec(ExpandConstant('{sys}\net.exe'), 'stop VerticalPIC_WebApp', '', SW_HIDE, ewWaitUntilIdle, ResultCode);
  end;
end;
