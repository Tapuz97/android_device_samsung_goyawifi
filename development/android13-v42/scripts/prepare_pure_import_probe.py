"""Separate the receiver from EGL-linked rendering code for a true import-only control."""
from pathlib import Path
p=Path(__file__).resolve().parents[1];g=p/'work/device/samsung/t110_bringup/graphics';f=g/'gpu_readback_probe.cpp';s=f.read_text()
start=s.index('static bool checkPixels');end=s.index('static int crossProcess',start)
header='''#pragma once
#include <ui/GraphicBuffer.h>
#include <hardware/gralloc.h>
#include <array>
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <sys/socket.h>
#include <unistd.h>
using namespace android;
'''+s[start:end].replace('static bool checkPixels','inline bool checkPixels').replace('static int receiveBuffer','inline int receiveBuffer')
(g/'GpuReadbackProtocol.h').write_text(header)
s=s[:start]+s[end:];s=s.replace('#include "T110EglWindow.h"','#include "T110EglWindow.h"\n#include "GpuReadbackProtocol.h"')
s=s.replace('static int crossProcess(const sp<GraphicBuffer>& target,const char* label) {','static int crossProcess(const sp<GraphicBuffer>& target,const char* label,bool worker) {')
s=s.replace('const_cast<char*>("/proc/self/exe"),const_cast<char*>("--receive")','const_cast<char*>("/data/local/tmp/t110-gpu-readback/t110_graphic_import_probe"),const_cast<char*>(worker?"--receive":"--receive-main")')
s=s.replace('execv("/proc/self/exe",args)','execv(args[0],args)')
s=s.replace('int imported=crossProcess(target,label);printf("%s imported_process_exit=%d\\n",label,imported);\n    return checkPixels(target,label)&&imported==0;','int worker=crossProcess(target,label,true),main=crossProcess(target,label,false);\n    printf("%s imported_worker_exit=%d imported_main_exit=%d\\n",label,worker,main);\n    return checkPixels(target,label)&&worker==0&&main==0;')
s=s.replace('int main(int argc,char** argv) {\n    if(argc==4&&!strcmp(argv[1],"--receive"))return receiveBuffer(atoi(argv[2]),argv[3]);','int main() {')
assert '/proc/self/exe' not in s and 'imported_worker_exit' in s
f.write_text(s)
