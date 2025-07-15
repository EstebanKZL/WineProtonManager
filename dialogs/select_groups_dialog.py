from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                             QHeaderView, QDialogButtonBox, QWidget )
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from styles import STYLE_BREEZE
from config_manager import ConfigManager

class SelectGroupsDialog(QDialog):
    def __init__(self, component_groups: dict[str, list[str]], config_manager: ConfigManager, parent: QWidget | None = None):
        super().__init__(parent)
        self.component_groups = component_groups
        self.config_manager = config_manager
        self.setWindowTitle("Seleccionar Componentes de Winetricks")
        self.setMinimumSize(600, 550)
        self.setup_ui()
        self.config_manager.apply_breeze_style_to_widget(self)

    def setup_ui(self):
        layout = QVBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Componente", "Descripción"])
        self.tree.setColumnCount(2)
        self.tree.setSelectionMode(QTreeWidget.NoSelection) 
        self.tree.itemChanged.connect(self._handle_item_change) 

        self.component_descriptions = {
            # Bibliotecas Visual Basic
            "vb2run": "Runtime de Visual Basic 2.0 (1992)",
            "vb3run": "Runtime de Visual Basic 3.0 (1993)",
            "vb4run": "Runtime de Visual Basic 4.0 (1995)",
            "vb5run": "Runtime de Visual Basic 5.0 (1997)",
            "vb6run": "Runtime de Visual Basic 6.0 (1998)",

            # Visual C++ Runtime
            "vcrun6": "Runtime Visual C++ 6.0 (1998)",
            "vcrun6sp6": "Runtime Visual C++ 6.0 SP6 (2004)",
            "vcrun2003": "Runtime Visual C++ 2003 (7.1) (2003)",
            "vcrun2005": "Runtime Visual C++ 2005 (8.0) (2005)",
            "vcrun2008": "Runtime Visual C++ 2008 (9.0) (2007)",
            "vcrun2010": "Runtime Visual C++ 2010 (10.0) (2010)",
            "vcrun2012": "Runtime Visual C++ 2012 (11.0) (2012)",
            "vcrun2013": "Runtime Visual C++ 2013 (12.0) (2013)",
            "vcrun2015": "Runtime Visual C++ 2015 (14.0) (2015)",
            "vcrun2017": "Runtime Visual C++ 2017 (14.1) (2017)",
            "vcrun2019": "Runtime Visual C++ 2015-2019 (14.2) (2019)",
            "vcrun2022": "Runtime Visual C++ 2015-2022 (14.3) (2022)",

            # .NET Framework
            "dotnet11": ".NET Framework 1.1 (2003)",
            "dotnet11sp1": ".NET Framework 1.1 SP1 (2004)",
            "dotnet20": ".NET Framework 2.0 (2005)",
            "dotnet20sp1": ".NET Framework 2.0 SP1 (2008)",
            "dotnet20sp2": ".NET Framework 2.0 SP2 (2009)",
            "dotnet30": ".NET Framework 3.0 (2006)",
            "dotnet30sp1": ".NET Framework 3.0 SP1 (2007)",
            "dotnet35": ".NET Framework 3.5 (2007)",
            "dotnet35sp1": ".NET Framework 3.5 SP1 (2008)",
            "dotnet40": ".NET Framework 4.0 (2010)",
            "dotnet40_kb2468871": "Actualización KB2468871 para .NET 4.0 (2011)",
            "dotnet45": ".NET Framework 4.5 (2012)",
            "dotnet452": ".NET Framework 4.5.2 (2014)",
            "dotnet46": ".NET Framework 4.6 (2015)",
            "dotnet461": ".NET Framework 4.6.1 (2015)",
            "dotnet462": ".NET Framework 4.6.2 (2016)",
            "dotnet471": ".NET Framework 4.7.1 (2017)",
            "dotnet472": ".NET Framework 4.7.2 (2018)",
            "dotnet48": ".NET Framework 4.8 (2019)",
            "dotnet6": ".NET Runtime 6.0 (2021)",
            "dotnet7": ".NET Runtime 7.0 (2022)",
            "dotnet8": ".NET Runtime 8.0 (2023)",
            "dotnet9": ".NET Runtime 9.0 (2024)",
            "dotnetcore2": ".NET Core Runtime 2.1 (2018)",
            "dotnetcore3": ".NET Core Runtime 3.1 (2019)",
            "dotnetcoredesktop3": ".NET Core Desktop Runtime 3.1 (2019)",
            "dotnetdesktop6": ".NET Desktop Runtime 6.0 (2021)",
            "dotnetdesktop7": ".NET Desktop Runtime 7.0 (2022)",
            "dotnetdesktop8": ".NET Desktop Runtime 8.0 (2023)",
            "dotnetdesktop9": ".NET Desktop Runtime 9.0 (2024)",
            "dotnet_verifier": "Herramienta de verificación .NET",
            "vjrun20": "Runtime Visual J# 2.0 (2005)",

            # DirectX y Multimedia
            "d3dcompiler_42": "Compilador D3D (versión 42) (DirectX 2010)",
            "d3dcompiler_43": "Compilador D3D (versión 43) (DirectX 2010)",
            "d3dcompiler_46": "Compilador D3D (versión 46) (DirectX 2010)",
            "d3dcompiler_47": "Compilador D3D (versión 47) (DirectX 2015)",
            "d3dx9": "Librerías D3DX9 (DirectX 9)",
            "d3dx9_24": "D3DX9 (versión 24) (2004)",
            "d3dx9_25": "D3DX9 (versión 25) (2004)",
            "d3dx9_26": "D3DX9 (versión 26) (2004)",
            "d3dx9_27": "D3DX9 (versión 27) (2005)",
            "d3dx9_28": "D3DX9 (versión 28) (2005)",
            "d3dx9_29": "D3DX9 (versión 29) (2005)",
            "d3dx9_30": "D3DX9 (versión 30) (2006)",
            "d3dx9_31": "D3DX9 (versión 31) (2006)",
            "d3dx9_32": "D3DX9 (versión 32) (2006)",
            "d3dx9_33": "D3DX9 (versión 33) (2006)",
            "d3dx9_34": "D3DX9 (versión 34) (2007)",
            "d3dx9_35": "D3DX9 (versión 35) (2007)",
            "d3dx9_36": "D3DX9 (versión 36) (2007)",
            "d3dx9_37": "D3DX9 (versión 37) (2008)",
            "d3dx9_38": "D3DX9 (versión 38) (2008)",
            "d3dx9_39": "D3DX9 (versión 39) (2008)",
            "d3dx9_40": "D3DX9 (versión 40) (2009)",
            "d3dx9_41": "D3DX9 (versión 41) (2009)",
            "d3dx9_42": "D3DX9 (versión 42) (2009)",
            "d3dx9_43": "D3DX9 (versión 43) (2010)",
            "d3dx10": "Librerías D3DX10 (DirectX 10)",
            "d3dx10_43": "D3DX10 (versión 43) (2010)",
            "d3dx11_42": "D3DX11 (versión 42) (2010)",
            "d3dx11_43": "D3DX11 (versión 43) (2010)",
            "d3dxof": "Librería DirectX Object Framework (1996)",
            "devenum": "Enumerador de dispositivos DirectShow",
            "dinput": "DirectInput (entrada de dispositivos) (1996)",
            "dinput8": "DirectInput 8 (2000)",
            "directmusic": "DirectMusic (1999)",
            "directplay": "DirectPlay (redes) (1996)",
            "directshow": "Runtime DirectShow (multimedia) (1996)",
            "directx9": "DirectX 9 (obsoleto) (2002)",
            "dmband": "DirectMusic Band",
            "dmcompos": "DirectMusic Composer",
            "dmime": "DirectMusic Interactive Engine",
            "dmloader": "DirectMusic Loader",
            "dmscript": "DirectMusic Script",
            "dmstyle": "DirectMusic Style",
            "dmsynth": "DirectMusic Synthesizer",
            "dmusic": "DirectMusic Core",
            "dmusic32": "DirectMusic (32-bit)",
            "dx8vb": "DirectX 8 para Visual Basic (2000)",
            "dxdiag": "Herramienta de diagnóstico DirectX",
            "dxdiagn": "Biblioteca de diagnóstico DirectX",
            "dxdiagn_feb2010": "Biblioteca de diagnóstico DirectX (2010)",
            "dxtrans": "Transforms DirectX",
            "xact": "XACT Engine (32-bit) (2006)",
            "xact_x64": "XACT Engine (64-bit) (2006)",
            "xaudio29": "XAudio2 Redistributable (2010)",
            "xinput": "Soporte para controles de Xbox (2005)",
            "xna31": "XNA Framework 3.1 (2009)",
            "xna40": "XNA Framework 4.0 (2010)",

            # DXVK y VKD3D
            "dxvk": "Implementación Vulkan para D3D (última versión)",
            "dxvk1000": "DXVK 1.0 (2018)",
            "dxvk1001": "DXVK 1.0.1 (2018)",
            "dxvk1002": "DXVK 1.0.2 (2018)",
            "dxvk1003": "DXVK 1.0.3 (2018)",
            "dxvk1011": "DXVK 1.1.1 (2018)",
            "dxvk1020": "DXVK 1.2 (2019)",
            "dxvk1021": "DXVK 1.2.1 (2019)",
            "dxvk1022": "DXVK 1.2.2 (2019)",
            "dxvk1023": "DXVK 1.2.3 (2019)",
            "dxvk1030": "DXVK 1.3 (2019)",
            "dxvk1031": "DXVK 1.3.1 (2019)",
            "dxvk1032": "DXVK 1.3.2 (2019)",
            "dxvk1033": "DXVK 1.3.3 (2019)",
            "dxvk1034": "DXVK 1.3.4 (2020)",
            "dxvk1040": "DXVK 1.4 (2020)",
            "dxvk1041": "DXVK 1.4.1 (2020)",
            "dxvk1042": "DXVK 1.4.2 (2020)",
            "dxvk1043": "DXVK 1.4.3 (2020)",
            "dxvk1044": "DXVK 1.4.4 (2020)",
            "dxvk1045": "DXVK 1.4.5 (2020)",
            "dxvk1046": "DXVK 1.4.6 (2020)",
            "dxvk1050": "DXVK 1.5 (2020)",
            "dxvk1051": "DXVK 1.5.1 (2020)",
            "dxvk1052": "DXVK 1.5.2 (2020)",
            "dxvk1053": "DXVK 1.5.3 (2020)",
            "dxvk1054": "DXVK 1.5.4 (2020)",
            "dxvk1055": "DXVK 1.5.5 (2020)",
            "dxvk1060": "DXVK 1.6 (2020)",
            "dxvk1061": "DXVK 1.6.1 (2020)",
            "dxvk1070": "DXVK 1.7 (2021)",
            "dxvk1071": "DXVK 1.7.1 (2021)",
            "dxvk1072": "DXVK 1.7.2 (2021)",
            "dxvk1073": "DXVK 1.7.3 (2021)",
            "dxvk1080": "DXVK 1.8 (2021)",
            "dxvk1081": "DXVK 1.8.1 (2021)",
            "dxvk1090": "DXVK 1.9 (2021)",
            "dxvk1091": "DXVK 1.9.1 (2021)",
            "dxvk1092": "DXVK 1.9.2 (2021)",
            "dxvk1093": "DXVK 1.9.3 (2021)",
            "dxvk1094": "DXVK 1.9.4 (2021)",
            "dxvk1100": "DXVK 1.10 (2022)",
            "dxvk1101": "DXVK 1.10.1 (2022)",
            "dxvk1102": "DXVK 1.10.2 (2022)",
            "dxvk1103": "DXVK 1.10.3 (2022)",
            "dxvk2000": "DXVK 2.0 (2022)",
            "dxvk2010": "DXVK 2.1 (2022)",
            "dxvk2020": "DXVK 2.2 (2022)",
            "dxvk2030": "DXVK 2.3 (2023)",
            "dxvk2040": "DXVK 2.4 (2023)",
            "dxvk2041": "DXVK 2.4.1 (2023)",
            "dxvk2050": "DXVK 2.5 (2023)",
            "dxvk2051": "DXVK 2.5.1 (2023)",
            "dxvk2052": "DXVK 2.5.2 (2023)",
            "dxvk2053": "DXVK 2.5.3 (2023)",
            "dxvk2060": "DXVK 2.6 (2023)",
            "dxvk2061": "DXVK 2.6.1 (2023)",
            "dxvk2062": "DXVK 2.6.2 (2023)",
            "dxvk2070": "DXVK 2.7 (2024)",
            "vkd3d": "Implementación Vulkan para D3D12 (última versión)",
            "dxvk_nvapi0061": "NVAPI para DXVK (2023)",

            # Codecs Multimedia
            "allcodecs": "Paquete completo de codecs",
            "avifil32": "Codec AVI (1992)",
            "binkw32": "Codec Bink Video (1999)",
            "cinepak": "Codec Cinepak (1991)",
            "dirac": "Codec Dirac (2008)",
            "ffdshow": "Codecs FFDShow (2004)",
            "icodecs": "Codecs Indeo (1992)",
            "l3codecx": "Codec MP3 (1996)",
            "lavfilters": "Filtros LAV (2012)",
            "lavfilters702": "Filtros LAV 0.70.2 (2019)",
            "ogg": "Codecs Ogg (Vorbis, Theora) (2002)",
            "qasf": "Soporte ASF (Windows Media) (1999)",
            "qcap": "Captura DirectShow",
            "qdvd": "Soporte DVD (1999)",
            "qedit": "Edición DirectShow",
            "quartz": "Renderizador DirectShow",
            "quartz_feb2010": "Renderizador DirectShow (2010)",
            "quicktime72": "QuickTime 7.2 (2007)",
            "quicktime76": "QuickTime 7.6 (2009)",
            "wmp9": "Windows Media Player 9 (2003)",
            "wmp10": "Windows Media Player 10 (2006)",
            "wmp11": "Windows Media Player 11 (2006)",
            "wmv9vcm": "Codec Windows Media Video 9 (2003)",
            "xvid": "Codec Xvid (2001)",

            # Componentes de Sistema
            "amstream": "Soporte multimedia (DirectShow)",
            "atmlib": "Adobe Type Manager (fuentes PostScript)",
            "cabinet": "Soporte CAB (compresión)",
            "cmd": "Símbolo del sistema (Command Prompt)",
            "comctl32": "Controles comunes (UI)",
            "comctl32ocx": "Controles comunes (OCX)",
            "comdlg32ocx": "Cuadros de diálogo comunes",
            "crypt32": "API de criptografía",
            "crypt32_winxp": "API de criptografía (WinXP)",
            "dbghelp": "Herramientas de depuración",
            "esent": "Motor de almacenamiento (ESE)",
            "filever": "Información de versiones",
            "gdiplus": "GDI+ (gráficos 2D)",
            "gdiplus_winxp": "GDI+ (WinXP)",
            "glidewrapper": "Wrapper Glide para 3dfx",
            "glut": "Librería OpenGL Utility Toolkit (1994)",
            "gmdls": "Colección MIDI DLS",
            "hid": "Soporte HID (dispositivos humanos)",
            "jet40": "Motor de base de datos Jet 4.0 (2000)",
            "mdac27": "Componentes de acceso a datos 2.7 (2000)",
            "mdac28": "Componentes de acceso a datos 2.8 (2001)",
            "msaa": "Accesibilidad (Microsoft Active Accessibility)",
            "msacm32": "Administrador de compresión de audio",
            "msasn1": "Soporte ASN.1 (criptografía)",
            "msctf": "Servicios de texto (TSF)",
            "msdelta": "Compresión diferencial",
            "msdxmocx": "Control ActiveX WMP",
            "msflxgrd": "Control FlexGrid",
            "msftedit": "Control RichEdit avanzado",
            "mshflxgd": "Control Hierarchical FlexGrid",
            "msls31": "Servicios de línea (TCP/IP)",
            "msmask": "Control Masked Edit",
            "mspatcha": "Aplicador de parches",
            "msscript": "Control de scripts (Windows Script)",
            "msvcirt": "Runtime C++ (legado)",
            "msvcrt40": "Runtime C++ 4.0 (1996)",
            "msxml3": "MSXML 3.0 (2001)",
            "msxml4": "MSXML 4.0 (2003)",
            "msxml6": "MSXML 6.0 (2006)",
            "ole32": "OLE 2.0 (1993)",
            "oleaut32": "OLE Automation",
            "pdh": "Ayudante de datos de rendimiento",
            "pdh_nt4": "Ayudante de datos de rendimiento (NT4)",
            "peverify": "Verificador .NET",
            "pngfilt": "Filtro PNG (imágenes)",
            "prntvpt": "Impresión (API)",
            "python26": "Python 2.6 (2008)",
            "python27": "Python 2.7 (2010)",
            "riched20": "RichEdit 2.0",
            "riched30": "RichEdit 3.0",
            "richtx32": "Control RichTextBox",
            "sapi": "API de voz (SAPI)",
            "sdl": "Simple DirectMedia Layer (multiplataforma)",
            "secur32": "Seguridad (autenticación)",
            "setupapi": "API de instalación",
            "shockwave": "Shockwave Player (1995)",
            "speechsdk": "SDK de voz (Microsoft Speech)",
            "tabctl32": "Control de pestañas",
            "ucrtbase2019": "Runtime C universal (2019)",
            "uiribbon": "Interfaz Ribbon (Office 2007)",
            "updspapi": "API de actualizaciones",
            "urlmon": "Moniker de URL",
            "usp10": "Uniscribe (texto complejo)",
            "webio": "E/S web",
            "windowscodecs": "Componentes de imagen (WIC)",
            "winhttp": "Servicios HTTP",
            "wininet": "API de Internet",
            "wininet_win2k": "API de Internet (Win2k)",
            "wmi": "Instrumentación de administración",
            "wsh57": "Windows Script Host 5.7 (2006)",
            "xmllite": "Lector XML ligero (2006)",

            # Controladores y Utilidades
            "art2k7min": "Runtime Access 2007 (2007)",
            "art2kmin": "Runtime Access 2000 (2000)",
            "cnc_ddraw": "Wrapper ddraw para juegos CnC",
            "d2gl": "Wrapper Glide para Diablo 2",
            "d3drm": "Direct3D Retained Mode (1996)",
            "dpvoice": "Voz DirectPlay (1999)",
            "dsdmo": "Efectos DMO (DirectX Media Objects)",
            "dsound": "DirectSound (audio) (1995)",
            "dswave": "Onda DirectSound",
            "faudio": "Implementación FAudio (XAudio2 compatible)",
            "faudio1901": "FAudio 19.01 (2019)",
            "faudio1902": "FAudio 19.02 (2019)",
            "faudio1903": "FAudio 19.03 (2019)",
            "faudio1904": "FAudio 19.04 (2019)",
            "faudio1905": "FAudio 19.05 (2019)",
            "faudio1906": "FAudio 19.06 (2019)",
            "faudio190607": "FAudio 19.06.07 (2019)",
            "galliumnine": "Gallium Nine (última versión) (Direct3D 9 nativo)",
            "galliumnine02": "Gallium Nine 0.2 (2015)",
            "galliumnine03": "Gallium Nine 0.3 (2016)",
            "galliumnine04": "Gallium Nine 0.4 (2017)",
            "galliumnine05": "Gallium Nine 0.5 (2018)",
            "galliumnine06": "Gallium Nine 0.6 (2018)",
            "galliumnine07": "Gallium Nine 0.7 (2019)",
            "galliumnine08": "Gallium Nine 0.8 (2019)",
            "galliumnine09": "Gallium Nine 0.9 (2020)",
            "gfw": "Games for Windows Live (2007)",
            "ie6": "Internet Explorer 6 (2001)",
            "ie7": "Internet Explorer 7 (2006)",
            "ie8": "Internet Explorer 8 (2009)",
            "ie8_kb2936068": "Actualización IE8 KB2936068 (2014)",
            "ie8_tls12": "Soporte TLS 1.2 para IE8 (2016)",
            "iertutil": "Utilidades IE",
            "itircl": "Librería ITIRCL (MSN)",
            "itss": "Servicios de almacenamiento IT (MSN)",
            "mdx": "Managed DirectX (2004)",
            "mf": "Media Foundation (2007)",
            "mfc40": "MFC 4.0 (1996)",
            "mfc42": "MFC 4.2 (1997)",
            "mfc70": "MFC 7.0 (2002)",
            "mfc71": "MFC 7.1 (2003)",
            "mfc80": "MFC 8.0 (2005)",
            "mfc90": "MFC 9.0 (2008)",
            "mfc100": "MFC 10.0 (2010)",
            "mfc110": "MFC 11.0 (2012)",
            "mfc120": "MFC 12.0 (2013)",
            "mfc140": "MFC 14.0 (2015)",
            "nuget": "Gestor de paquetes NuGet (2010)",
            "openal": "OpenAL Runtime (audio 3D)",
            "otvdm": "Emulador Win16 (otvdm) (2020)",
            "otvdm090": "Emulador Win16 (otvdm 0.9.0) (2020)",
            "physx": "PhysX (NVIDIA Physics)",
            "powershell": "PowerShell para Wine",
            "powershell_core": "PowerShell Core (2016)",
            "protectionid": "Herramienta Protection ID",

            # Fuentes
            "allfonts": "Paquete completo de fuentes",
            "andale": "Fuente Andale Mono (1996)",
            "arial": "Fuente Arial (1982)",
            "baekmuk": "Fuentes coreanas Baekmuk (1990s)",
            "calibri": "Fuente Calibri (2007)",
            "cambria": "Fuente Cambria (2007)",
            "candara": "Fuente Candara (2007)",
            "cjkfonts": "Fuentes CJK (chino-japonés-coreano)",
            "comicsans": "Fuente Comic Sans MS (1994)",
            "consolas": "Fuente Consolas (2007)",
            "constantia": "Fuente Constantia (2007)",
            "corbel": "Fuente Corbel (2007)",
            "corefonts": "Fuentes básicas de Microsoft (1996-2002)",
            "courier": "Fuente Courier New (1982)",
            "droid": "Fuentes Droid (Android) (2007)",
            "eufonts": "Fuentes europeas adicionales",
            "fakechinese": "Fuentes chinas simuladas",
            "fakejapanese": "Fuentes japonesas simuladas",
            "fakejapanese_ipamona": "Fuente japonesa simulada IPAMona",
            "fakejapanese_vlgothic": "Fuente japonesa simulada VL Gothic",
            "fakekorean": "Fuentes coreanas simuladas",
            "georgia": "Fuente Georgia (1993)",
            "impact": "Fuente Impact (1992)",
            "ipamona": "Fuente japonesa IPAMona",
            "liberation": "Fuentes Liberation (alternativas open-source) (2007)",
            "lucida": "Fuente Lucida Console (1991)",
            "meiryo": "Fuente japonesa Meiryo (2006)",
            "micross": "Fuente Microsoft Sans Serif (1982)",
            "opensymbol": "Fuente OpenSymbol (2000)",
            "pptfonts": "Fuentes para presentaciones PowerPoint",
            "sourcehansans": "Fuente Source Han Sans (2014)",
            "tahoma": "Fuente Tahoma (1994)",
            "takao": "Fuente japonesa Takao (2006)",
            "times": "Fuente Times New Roman (1932)",
            "trebuchet": "Fuente Trebuchet MS (1996)",
            "uff": "Formato de fuente universal",
            "unifont": "Fuente Unifont (1998)",
            "verdana": "Fuente Verdana (1996)",
            "vlgothic": "Fuente japonesa VL Gothic (2003)",
            "webdings": "Fuente Webdings (1997)",
            "wenquanyi": "Fuente china WenQuanYi (2004)",
            "wenquanyizenhei": "Fuente china WenQuanYi Zen Hei (2007)",

            # Aplicaciones
            "3m_library": "Biblioteca 3M (Adobe)",
            "7zip": "7-Zip (compresión) (1999)",
            "adobe_diged": "Adobe Digital Editions (2005)",
            "adobe_diged4": "Adobe Digital Editions 4.0 (2015)",
            "autohotkey": "AutoHotkey (automatización) (2003)",
            "busybox": "BusyBox (herramientas Unix) (1999)",
            "cmake": "CMake (compilación) (2000)",
            "colorprofile": "Perfiles de color ICC",
            "controlpad": "ControlPad (ActiveX)",
            "controlspy": "ControlSpy (ActiveX)",
            "dbgview": "DebugView (depuración) (1996)",
            "depends": "Dependency Walker (2006)",
            "dotnet20sdk": ".NET Framework 2.0 SDK (2005)",
            "dxsdk_aug2006": "DirectX SDK (Agosto 2006)",
            "dxsdk_jun2010": "DirectX SDK (Junio 2010)",
            "dxwnd": "DXWnd (ventana DirectX) (2003)",
            "emu8086": "Emu8086 (emulador CPU) (2002)",
            "ev3": "LEGO MINDSTORMS EV3 (2013)",
            "firefox": "Mozilla Firefox (2004)",
            "fontxplorer": "FontXplorer (gestión de fuentes)",
            "foobar2000": "foobar2000 (reproductor audio) (2002)",
            "hhw": "HTML Help Workshop (1997)",
            "iceweasel": "Iceweasel (Firefox rebranded) (2006)",
            "irfanview": "IrfanView (visor imágenes) (1996)",
            "kindle": "Kindle for PC (2007)",
            "kobo": "Kobo Desktop (2010)",
            "mingw": "MinGW (GCC para Windows) (1998)",
            "mozillabuild": "Mozilla Build Tools (2006)",
            "mpc": "Media Player Classic (2003)",
            "mspaint": "Microsoft Paint (1985)",
            "mt4": "MetaTrader 4 (trading) (2005)",
            "njcwp_trial": "NJStar Chinese Word Processor (1990s)",
            "njjwp_trial": "NJStar Japanese Word Processor (1990s)",
            "nook": "Nook for PC (2009)",
            "npp": "Notepad++ (2003)",
            "ollydbg110": "OllyDbg 1.10 (debugger) (2004)",
            "ollydbg200": "OllyDbg 2.0 (2010)",
            "ollydbg201": "OllyDbg 2.0.1 (2013)",
            "openwatcom": "Open Watcom (compilador) (2003)",
            "origin": "Origin (plataforma EA) (2011)",
            "procexp": "Process Explorer (2001)",
            "psdk2003": "Platform SDK 2003",
            "psdkwin71": "Platform SDK Windows 7.1 (2009)",
            "safari": "Safari para Windows (2007-2012)",
            "sketchup": "SketchUp (3D modeling) (2000)",
            "steam": "Steam (plataforma Valve) (2003)",
            "ubisoftconnect": "Ubisoft Connect (2020)",
            "utorrent": "µTorrent (2005)",
            "utorrent3": "µTorrent 3.x (2011)",
            "vc2005express": "Visual C++ 2005 Express (2005)",
            "vc2005expresssp1": "Visual C++ 2005 Express SP1 (2006)",
            "vc2005trial": "Visual C++ 2005 Trial (2005)",
            "vc2008express": "Visual C++ 2008 Express (2007)",
            "vc2010express": "Visual C++ 2010 Express (2010)",
            "vstools2019": "Visual Studio Tools 2019",
            "winamp": "Winamp (reproductor multimedia) (1997)",
            "winrar": "WinRAR (compresión) (1995)",
            "wme9": "Windows Media Encoder 9 (2003)",

            # Benchmarks
            "3dmark03": "3DMark03 (benchmark gráfico) (2003)",
            "3dmark05": "3DMark05 (benchmark gráfico) (2005)",
            "3dmark06": "3DMark06 (benchmark gráfico) (2006)",
            "3dmark2000": "3DMark2000 (benchmark gráfico) (2000)",
            "3dmark2001": "3DMark2001 (benchmark gráfico) (2001)",
            "stalker_pripyat_bench": "STALKER: Call of Pripyat Benchmark (2009)",
            "unigine_heaven": "Unigine Heaven Benchmark (2009)",
            "wglgears": "GLGears (OpenGL benchmark) (1999)"
        }

        base_font = STYLE_BREEZE["font"]
        tree_font_size = base_font.pointSize() + 0
        font_for_tree = QFont(base_font.family(), tree_font_size)

        for group_name, components in self.component_groups.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, group_name)
            group_item.setFont(0, font_for_tree)
       
            group_item.setFlags(group_item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsTristate)
            group_item.setCheckState(0, Qt.PartiallyChecked) 

            for comp in components:
                child_item = QTreeWidgetItem(group_item)
                child_item.setText(0, comp)
                child_item.setFont(0, font_for_tree)
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked)

                description = self.component_descriptions.get(comp, "Componente estándar de Winetricks.")
                child_item.setText(1, description)
                child_item.setFont(1, font_for_tree) 

        self.tree.expandAll() 
       
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.tree)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setAutoDefault(False)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _handle_item_change(self, item: QTreeWidgetItem, column: int):
        """Maneja el estado de las casillas de verificación de los elementos del árbol (tres estados)."""
        try:
            self.tree.itemChanged.disconnect(self._handle_item_change)
        except TypeError: 
            pass

        if item.flags() & Qt.ItemIsTristate:
            if item.checkState(0) == Qt.Checked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, Qt.Checked)
            elif item.checkState(0) == Qt.Unchecked:
                for i in range(item.childCount()):
                    item.child(i).setCheckState(0, Qt.Unchecked)
        else: 
            parent = item.parent()
            if parent:
                checked_children = 0
                for i in range(parent.childCount()):
                    if parent.child(i).checkState(0) == Qt.Checked:
                        checked_children += 1

                if checked_children == 0:
                    parent.setCheckState(0, Qt.Unchecked)
                elif checked_children == parent.childCount():
                    parent.setCheckState(0, Qt.Checked)
                else:
                    parent.setCheckState(0, Qt.PartiallyChecked)

        self.tree.itemChanged.connect(self._handle_item_change)


    def get_selected_components(self) -> list[str]:
        """Devuelve una lista de los componentes de Winetricks seleccionados."""
        selected = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item.checkState(0) == Qt.Checked:
                    selected.append(child_item.text(0))
        return selected
