"""Inspect task-owned stalled tool wrappers without touching other work."""
import base64,csv,io,subprocess,ctypes,re
try:import psutil
except ImportError:psutil=None
print('psutil_available',bool(psutil),flush=True)
if psutil:
    markers=['addInterfaceToPhysicalNetwork','boot39-app-network-nondebug',
        'wsl.exe --terminate T110Build','config NETFILTER_XT_MARK',
        'Get-Process -Name wsl,wslhost,VmmemWSL','Id=51,129,153']
    for proc in psutil.process_iter(['pid','name']):
        if proc.info['name'].lower() not in ('pwsh.exe','powershell.exe'):continue
        try:
            args=proc.cmdline();command=' '.join(args)
            for flag in ('-EncodedCommand','-encodedcommand','-enc'):
                if flag in args:
                    command=base64.b64decode(args[args.index(flag)+1]).decode('utf-16le');break
            matches=[m for m in markers if m in command]
            if matches:
                print('task_wrapper',proc.pid,matches,flush=True)
                # Cancel only these obsolete task requests, including the queued
                # stop request, before starting a new build through another shell.
                for child in proc.children(recursive=True):child.terminate()
                proc.terminate()
        except (psutil.NoSuchProcess,psutil.AccessDenied):pass
else:
    data=subprocess.check_output(['tasklist','/FO','CSV','/NH'],timeout=10).decode(errors='replace')
    for row in csv.reader(io.StringIO(data)):
        if row and row[0].lower() in ('pwsh.exe','powershell.exe','wsl.exe','vmmemwsl'):
            print(row[:2],flush=True)
            if row[0].lower() not in ('pwsh.exe','wsl.exe'):continue
            from ctypes import wintypes as W
            k=ctypes.WinDLL('kernel32',use_last_error=True);nt=ctypes.WinDLL('ntdll')
            k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];k.OpenProcess.restype=W.HANDLE
            k.CloseHandle.argtypes=[W.HANDLE]
            nt.NtQueryInformationProcess.argtypes=[W.HANDLE,W.ULONG,ctypes.c_void_p,W.ULONG,ctypes.POINTER(W.ULONG)]
            nt.NtQueryInformationProcess.restype=W.LONG
            class UnicodeString(ctypes.Structure):
                _fields_=[('Length',W.USHORT),('MaximumLength',W.USHORT),('Buffer',ctypes.c_void_p)]
            handle=k.OpenProcess(0x1000,False,int(row[1]))
            if not handle:continue
            try:
                needed=W.ULONG();nt.NtQueryInformationProcess(handle,60,None,0,ctypes.byref(needed))
                if not 0<needed.value<131072:continue
                buffer=ctypes.create_string_buffer(needed.value)
                if nt.NtQueryInformationProcess(handle,60,buffer,needed,ctypes.byref(needed))!=0:continue
                value=UnicodeString.from_buffer(buffer);command=ctypes.wstring_at(value.Buffer,value.Length//2)
                encoded=re.search(r'-(?:EncodedCommand|enc)\s+(\S+)',command,re.I)
                if encoded:command=base64.b64decode(encoded[1].strip('"')).decode('utf-16le')
                markers=['addInterfaceToPhysicalNetwork','boot39-app-network-nondebug','wsl.exe --terminate T110Build',
                         'config NETFILTER_XT_MARK','Get-Process -Name wsl,wslhost,VmmemWSL','Id=51,129,153']
                matches=[m for m in markers if m in command]
                print('task_matches',row[1],matches,flush=True)
                if matches:
                    terminate=k.OpenProcess(1,False,int(row[1]))
                    if terminate:
                        try:
                            k.TerminateProcess.argtypes=[W.HANDLE,W.UINT]
                            print('cancelled_obsolete_task_wrapper',row[1],bool(k.TerminateProcess(terminate,1)),flush=True)
                        finally:k.CloseHandle(terminate)
            finally:k.CloseHandle(handle)
