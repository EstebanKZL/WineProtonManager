from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QLabel, QCheckBox, QDialog, QDialogButtonBox,
    QMessageBox, QGroupBox, QComboBox, QLineEdit, QFileDialog,
    QTabWidget, QFormLayout, QScrollArea, QListWidgetItem, QAction,
    QMenu, QMenuBar, QTableWidget, QTableWidgetItem, QHeaderView, 
    QTreeWidget, QTreeWidgetItem, QProgressDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDir, QSize, QUrl
from PyQt5.QtGui import QIcon, QPalette, QColor, QFont, QDesktopServices
from styles import STEAM_DECK_STYLE

class SelectGroupsDialog(QDialog):
    def __init__(self, component_groups, parent=None):
        super().__init__(parent)
        self.component_groups = component_groups
        self.setWindowTitle("Seleccionar Componentes")
        self.setMinimumSize(450, 350)
        self.setup_ui()
        self.apply_steamdeck_style()

    def apply_steamdeck_style(self):
        self.setFont(STEAM_DECK_STYLE["font"])
        
        # Estilo único para ambos temas (fondo blanco, texto negro)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #ffffff;
                color: black;
            }
        """)

        for widget in self.findChildren(QWidget):
            if isinstance(widget, (QPushButton, QLabel, QComboBox, QLineEdit)):
                widget.setFont(STEAM_DECK_STYLE["font"])
            if isinstance(widget, QGroupBox):
                widget.setFont(STEAM_DECK_STYLE["title_font"])
            if isinstance(widget, QPushButton):
                widget.setStyleSheet(STEAM_DECK_STYLE["button_style"])
                
    def setup_ui(self):
        layout = QVBoxLayout()
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Componente", "Descripción"])
        self.tree.setColumnCount(2)
        self.tree.setSelectionMode(QTreeWidget.MultiSelection)
        
        self.component_descriptions = {
            # Bibliotecas Visual Basic
            "vb2run": "Runtime de Visual Basic 2.0",
            "vb3run": "Runtime de Visual Basic 3.0",
            "vb4run": "Runtime de Visual Basic 4.0",
            "vb5run": "Runtime de Visual Basic 5.0",
            "vb6run": "Runtime de Visual Basic 6.0",

            # Visual C++ Runtime
            "vcrun6": "Runtime Visual C++ 6.0",
            "vcrun6sp6": "Runtime Visual C++ 6.0 SP6",
            "vcrun2003": "Runtime Visual C++ 2003",
            "vcrun2005": "Runtime Visual C++ 2005",
            "vcrun2008": "Runtime Visual C++ 2008",
            "vcrun2010": "Runtime Visual C++ 2010",
            "vcrun2012": "Runtime Visual C++ 2012",
            "vcrun2013": "Runtime Visual C++ 2013",
            "vcrun2015": "Runtime Visual C++ 2015",
            "vcrun2017": "Runtime Visual C++ 2017",
            "vcrun2019": "Runtime Visual C++ 2015-2019",
            "vcrun2022": "Runtime Visual C++ 2015-2022",

            # .NET Framework
            "dotnet11": ".NET Framework 1.1",
            "dotnet11sp1": ".NET Framework 1.1 SP1",
            "dotnet20": ".NET Framework 2.0",
            "dotnet20sp1": ".NET Framework 2.0 SP1",
            "dotnet20sp2": ".NET Framework 2.0 SP2",
            "dotnet30": ".NET Framework 3.0",
            "dotnet30sp1": ".NET Framework 3.0 SP1",
            "dotnet35": ".NET Framework 3.5",
            "dotnet35sp1": ".NET Framework 3.5 SP1",
            "dotnet40": ".NET Framework 4.0",
            "dotnet40_kb2468871": "Actualización KB2468871 para .NET 4.0",
            "dotnet45": ".NET Framework 4.5",
            "dotnet452": ".NET Framework 4.5.2",
            "dotnet46": ".NET Framework 4.6",
            "dotnet461": ".NET Framework 4.6.1",
            "dotnet462": ".NET Framework 4.6.2",
            "dotnet471": ".NET Framework 4.7.1",
            "dotnet472": ".NET Framework 4.7.2",
            "dotnet48": ".NET Framework 4.8",
            "dotnet6": ".NET Runtime 6.0",
            "dotnet7": ".NET Runtime 7.0",
            "dotnet8": ".NET Runtime 8.0",
            "dotnet9": ".NET Runtime 9.0",
            "dotnetcore2": ".NET Core Runtime 2.1",
            "dotnetcore3": ".NET Core Runtime 3.1",
            "dotnetcoredesktop3": ".NET Core Desktop Runtime 3.1",
            "dotnetdesktop6": ".NET Desktop Runtime 6.0",
            "dotnetdesktop7": ".NET Desktop Runtime 7.0",
            "dotnetdesktop8": ".NET Desktop Runtime 8.0",
            "dotnetdesktop9": ".NET Desktop Runtime 9.0",

            # DirectX y Multimedia
            "d3dcompiler_42": "Compilador D3D (versión 42)",
            "d3dcompiler_43": "Compilador D3D (versión 43)",
            "d3dcompiler_46": "Compilador D3D (versión 46)",
            "d3dcompiler_47": "Compilador D3D (versión 47)",
            "d3dx9": "Librerías D3DX9",
            "d3dx9_24": "D3DX9 (versión 24)",
            "d3dx9_25": "D3DX9 (versión 25)",
            "d3dx9_26": "D3DX9 (versión 26)",
            "d3dx9_27": "D3DX9 (versión 27)",
            "d3dx9_28": "D3DX9 (versión 28)",
            "d3dx9_29": "D3DX9 (versión 29)",
            "d3dx9_30": "D3DX9 (versión 30)",
            "d3dx9_31": "D3DX9 (versión 31)",
            "d3dx9_32": "D3DX9 (versión 32)",
            "d3dx9_33": "D3DX9 (versión 33)",
            "d3dx9_34": "D3DX9 (versión 34)",
            "d3dx9_35": "D3DX9 (versión 35)",
            "d3dx9_36": "D3DX9 (versión 36)",
            "d3dx9_37": "D3DX9 (versión 37)",
            "d3dx9_38": "D3DX9 (versión 38)",
            "d3dx9_39": "D3DX9 (versión 39)",
            "d3dx9_40": "D3DX9 (versión 40)",
            "d3dx9_41": "D3DX9 (versión 41)",
            "d3dx9_42": "D3DX9 (versión 42)",
            "d3dx9_43": "D3DX9 (versión 43)",
            "d3dx10": "Librerías D3DX10",
            "d3dx10_43": "D3DX10 (versión 43)",
            "d3dx11_42": "D3DX11 (versión 42)",
            "d3dx11_43": "D3DX11 (versión 43)",
            "d3dxof": "Librería DirectX Object Framework",
            "devenum": "Enumerador de dispositivos DirectShow",
            "dinput": "DirectInput (entrada de dispositivos)",
            "dinput8": "DirectInput 8",
            "directmusic": "DirectMusic",
            "directplay": "DirectPlay",
            "directshow": "Runtime DirectShow",
            "directx9": "DirectX 9 (obsoleto)",
            "dmband": "DirectMusic Band",
            "dmcompos": "DirectMusic Composer",
            "dmime": "DirectMusic Interactive Engine",
            "dmloader": "DirectMusic Loader",
            "dmscript": "DirectMusic Script",
            "dmstyle": "DirectMusic Style",
            "dmsynth": "DirectMusic Synthesizer",
            "dmusic": "DirectMusic Core",
            "dmusic32": "DirectMusic (32-bit)",
            "dx8vb": "DirectX 8 para Visual Basic",
            "dxdiag": "Herramienta de diagnóstico DirectX",
            "dxdiagn": "Biblioteca de diagnóstico DirectX",
            "dxdiagn_feb2010": "Biblioteca de diagnóstico DirectX (2010)",
            "dxtrans": "Transforms DirectX",
            "xact": "XACT Engine (32-bit)",
            "xact_x64": "XACT Engine (64-bit)",
            "xaudio29": "XAudio2 Redistributable",
            "xinput": "Soporte para controles de Xbox",
            "xna31": "XNA Framework 3.1",
            "xna40": "XNA Framework 4.0",

            # DXVK y VKD3D
            "dxvk": "Implementación Vulkan para D3D (última)",
            "dxvk1000": "DXVK 1.0",
            "dxvk1001": "DXVK 1.0.1",
            "dxvk1002": "DXVK 1.0.2",
            "dxvk1003": "DXVK 1.0.3",
            "dxvk1011": "DXVK 1.1.1",
            "dxvk1020": "DXVK 1.2",
            "dxvk1021": "DXVK 1.2.1",
            "dxvk1022": "DXVK 1.2.2",
            "dxvk1023": "DXVK 1.2.3",
            "dxvk1030": "DXVK 1.3",
            "dxvk1031": "DXVK 1.3.1",
            "dxvk1032": "DXVK 1.3.2",
            "dxvk1033": "DXVK 1.3.3",
            "dxvk1034": "DXVK 1.3.4",
            "dxvk1040": "DXVK 1.4",
            "dxvk1041": "DXVK 1.4.1",
            "dxvk1042": "DXVK 1.4.2",
            "dxvk1043": "DXVK 1.4.3",
            "dxvk1044": "DXVK 1.4.4",
            "dxvk1045": "DXVK 1.4.5",
            "dxvk1046": "DXVK 1.4.6",
            "dxvk1050": "DXVK 1.5",
            "dxvk1051": "DXVK 1.5.1",
            "dxvk1052": "DXVK 1.5.2",
            "dxvk1053": "DXVK 1.5.3",
            "dxvk1054": "DXVK 1.5.4",
            "dxvk1055": "DXVK 1.5.5",
            "dxvk1060": "DXVK 1.6",
            "dxvk1061": "DXVK 1.6.1",
            "dxvk1070": "DXVK 1.7",
            "dxvk1071": "DXVK 1.7.1",
            "dxvk1072": "DXVK 1.7.2",
            "dxvk1073": "DXVK 1.7.3",
            "dxvk1080": "DXVK 1.8",
            "dxvk1081": "DXVK 1.8.1",
            "dxvk1090": "DXVK 1.9",
            "dxvk1091": "DXVK 1.9.1",
            "dxvk1092": "DXVK 1.9.2",
            "dxvk1093": "DXVK 1.9.3",
            "dxvk1094": "DXVK 1.9.4",
            "dxvk1100": "DXVK 1.10",
            "dxvk1101": "DXVK 1.10.1",
            "dxvk1102": "DXVK 1.10.2",
            "dxvk1103": "DXVK 1.10.3",
            "dxvk2000": "DXVK 2.0",
            "dxvk2010": "DXVK 2.1",
            "dxvk2020": "DXVK 2.2",
            "dxvk2030": "DXVK 2.3",
            "dxvk2040": "DXVK 2.4",
            "dxvk2041": "DXVK 2.4.1",
            "dxvk2050": "DXVK 2.5",
            "dxvk2051": "DXVK 2.5.1",
            "dxvk2052": "DXVK 2.5.2",
            "dxvk2053": "DXVK 2.5.3",
            "dxvk2060": "DXVK 2.6",
            "dxvk2061": "DXVK 2.6.1",
            "dxvk2062": "DXVK 2.6.2",
            "vkd3d": "Implementación Vulkan para D3D12",

            # Codecs Multimedia
            "allcodecs": "Paquete completo de codecs",
            "avifil32": "Codec AVI",
            "binkw32": "Codec Bink Video",
            "cinepak": "Codec Cinepak",
            "dirac": "Codec Dirac",
            "ffdshow": "Codecs FFDShow",
            "icodecs": "Codecs Indeo",
            "l3codecx": "Codec MP3",
            "lavfilters": "Filtros LAV",
            "lavfilters702": "Filtros LAV 0.70.2",
            "ogg": "Codecs Ogg (Vorbis, Theora)",
            "qasf": "Soporte ASF",
            "qcap": "Captura DirectShow",
            "qdvd": "Soporte DVD",
            "qedit": "Edición DirectShow",
            "quartz": "Renderizador DirectShow",
            "quartz_feb2010": "Renderizador DirectShow (2010)",
            "quicktime72": "QuickTime 7.2",
            "quicktime76": "QuickTime 7.6",
            "wmp9": "Windows Media Player 9",
            "wmp10": "Windows Media Player 10",
            "wmp11": "Windows Media Player 11",
            "wmv9vcm": "Codec Windows Media Video 9",
            "xvid": "Codec Xvid",

            # Componentes de Sistema
            "amstream": "Soporte multimedia",
            "atmlib": "Adobe Type Manager",
            "cabinet": "Soporte CAB",
            "cmd": "Símbolo del sistema",
            "comctl32": "Controles comunes",
            "comctl32ocx": "Controles comunes (OCX)",
            "comdlg32ocx": "Cuadros de diálogo comunes",
            "crypt32": "API de criptografía",
            "crypt32_winxp": "API de criptografía (WinXP)",
            "dbghelp": "Herramientas de depuración",
            "esent": "Motor de almacenamiento",
            "filever": "Información de versiones",
            "gdiplus": "GDI+",
            "gdiplus_winxp": "GDI+ (WinXP)",
            "glidewrapper": "Wrapper Glide",
            "glut": "Librería OpenGL Utility",
            "gmdls": "Colección MIDI DLS",
            "hid": "Soporte HID",
            "jet40": "Motor de base de datos Jet",
            "mdac27": "Componentes de acceso a datos 2.7",
            "mdac28": "Componentes de acceso a datos 2.8",
            "msaa": "Accesibilidad",
            "msacm32": "Administrador de compresión de audio",
            "msasn1": "Soporte ASN.1",
            "msctf": "Servicios de texto",
            "msdelta": "Compresión diferencial",
            "msdxmocx": "Control ActiveX WMP",
            "msflxgrd": "Control FlexGrid",
            "msftedit": "Control RichEdit",
            "mshflxgd": "Control Hierarchical FlexGrid",
            "msls31": "Servicios de línea",
            "msmask": "Control Masked Edit",
            "mspatcha": "Aplicador de parches",
            "msscript": "Control de scripts",
            "msvcirt": "Runtime C++ (legado)",
            "msvcrt40": "Runtime C++ 4.0",
            "msxml3": "MSXML 3.0",
            "msxml4": "MSXML 4.0",
            "msxml6": "MSXML 6.0",
            "ole32": "OLE 2.0",
            "oleaut32": "OLE Automation",
            "pdh": "Ayudante de datos de rendimiento",
            "pdh_nt4": "Ayudante de datos de rendimiento (NT4)",
            "peverify": "Verificador .NET",
            "pngfilt": "Filtro PNG",
            "prntvpt": "Impresión",
            "python26": "Python 2.6",
            "python27": "Python 2.7",
            "riched20": "RichEdit 2.0",
            "riched30": "RichEdit 3.0",
            "richtx32": "Control RichTextBox",
            "sapi": "API de voz",
            "sdl": "Simple DirectMedia Layer",
            "secur32": "Seguridad",
            "setupapi": "API de instalación",
            "shockwave": "Shockwave Player",
            "speechsdk": "SDK de voz",
            "tabctl32": "Control de pestañas",
            "ucrtbase2019": "Runtime C universal (2019)",
            "uiribbon": "Interfaz Ribbon",
            "updspapi": "API de actualizaciones",
            "urlmon": "Moniker de URL",
            "usp10": "Uniscribe",
            "webio": "E/S web",
            "windowscodes": "Componentes de imagen",
            "winhttp": "Servicios HTTP",
            "wininet": "API de Internet",
            "wininet_win2k": "API de Internet (Win2k)",
            "wmi": "Instrumentación de administración",
            "wsh57": "Windows Script Host 5.7",
            "xmllite": "Lector XML ligero",

            # Controladores y Utilidades
            "art2k7min": "Runtime Access 2007",
            "art2kmin": "Runtime Access 2000",
            "cnc_ddraw": "Wrapper ddraw para juegos CnC",
            "d2gl": "Wrapper Glide para Diablo 2",
            "d3drm": "Direct3D Retained Mode",
            "dpvoice": "Voz DirectPlay",
            "dsdmo": "Efectos DMO",
            "dsound": "DirectSound",
            "dswave": "Onda DirectSound",
            "faudio": "Implementación FAudio",
            "faudio1901": "FAudio 19.01",
            "faudio1902": "FAudio 19.02",
            "faudio1903": "FAudio 19.03",
            "faudio1904": "FAudio 19.04",
            "faudio1905": "FAudio 19.05",
            "faudio1906": "FAudio 19.06",
            "faudio190607": "FAudio 19.06.07",
            "galliumnine": "Gallium Nine (último)",
            "galliumnine02": "Gallium Nine 0.2",
            "galliumnine03": "Gallium Nine 0.3",
            "galliumnine04": "Gallium Nine 0.4",
            "galliumnine05": "Gallium Nine 0.5",
            "galliumnine06": "Gallium Nine 0.6",
            "galliumnine07": "Gallium Nine 0.7",
            "galliumnine08": "Gallium Nine 0.8",
            "galliumnine09": "Gallium Nine 0.9",
            "gfw": "Games for Windows Live",
            "ie6": "Internet Explorer 6",
            "ie7": "Internet Explorer 7",
            "ie8": "Internet Explorer 8",
            "ie8_kb2936068": "Actualización IE8 KB2936068",
            "ie8_tls12": "Soporte TLS 1.2 para IE8",
            "iertutil": "Utilidades IE",
            "itircl": "Librería ITIRCL",
            "itss": "Servicios de almacenamiento IT",
            "mdx": "Managed DirectX",
            "mf": "Media Foundation",
            "mfc40": "MFC 4.0",
            "mfc42": "MFC 4.2",
            "mfc70": "MFC 7.0",
            "mfc71": "MFC 7.1",
            "mfc80": "MFC 8.0",
            "mfc90": "MFC 9.0",
            "mfc100": "MFC 10.0",
            "mfc110": "MFC 11.0",
            "mfc120": "MFC 12.0",
            "mfc140": "MFC 14.0",
            "nuget": "Gestor de paquetes NuGet",
            "openal": "OpenAL Runtime",
            "otvdm": "Emulador Win16 (otvdm)",
            "otvdm090": "Emulador Win16 (otvdm 0.9.0)",
            "physx": "PhysX",
            "powershell": "PowerShell para Wine",
            "powershell_core": "PowerShell Core"
        }
        
        for group_name, components in self.component_groups.items():
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, group_name)
            group_item.setFlags(group_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            
            for comp in components:
                child_item = QTreeWidgetItem(group_item)
                child_item.setText(0, comp)
                child_item.setFlags(child_item.flags() | Qt.ItemIsUserCheckable)
                child_item.setCheckState(0, Qt.Unchecked)
                
                description = self.component_descriptions.get(comp, "Componente Winetricks estándar")
                child_item.setText(1, description)
        
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

    def get_selected_components(self):
        selected = []
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            group_item = root.child(i)
            for j in range(group_item.childCount()):
                child_item = group_item.child(j)
                if child_item.checkState(0) == Qt.Checked:
                    selected.append(child_item.text(0))
        return selected
