import ctypes,json,subprocess
results={}
for name,command in [('adb',['tasklist.exe','/FI','IMAGENAME eq adb.exe','/FO','CSV']),('tcp',['netstat.exe','-ano','-p','tcp'])]:
 r=subprocess.run(command,capture_output=True,timeout=30);text=r.stdout.decode(errors='replace')
 results[name]=text if name=='adb' else [line.strip() for line in text.splitlines() if ':5037' in line]
 if name=='tcp':
  paths={}
  for line in results[name]:
   pid=int(line.split()[-1]);handle=ctypes.windll.kernel32.OpenProcess(0x1000,False,pid)
   if handle:
    size=ctypes.c_ulong(32768);buffer=ctypes.create_unicode_buffer(size.value)
    if ctypes.windll.kernel32.QueryFullProcessImageNameW(handle,0,buffer,ctypes.byref(size)):paths[pid]=buffer.value
    ctypes.windll.kernel32.CloseHandle(handle)
  results['listener_process_paths']=paths
print(json.dumps(results,indent=2))
