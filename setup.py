import sys
import os
import shutil
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {"packages": ["os"], "excludes": ["tkinter","mybacklog"],
                     "include_msvcr":True,
                     }

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

if os.path.exists("build/exe.win32-3.3"):
    shutil.rmtree("build/exe.win32-3.3")
setup(name = "mybacklog",
        version = "0.5",
        description = "MyBacklog game database",
        options = {"build_exe": build_exe_options},
        executables = [Executable("runit.py", base=base)])

shutil.copy("mybacklog.py","build/exe.win32-3.3")
shutil.copytree("code","build/exe.win32-3.3/code")
shutil.copytree("icons","build/exe.win32-3.3/icons")
shutil.copytree("tools","build/exe.win32-3.3/tools")
shutil.copytree("build/requests","build/exe.win32-3.3/requests")
shutil.copytree("build/PyQt5","build/exe.win32-3.3/PyQt5")
shutil.copytree("build/Crypto","build/exe.win32-3.3/Crypto")