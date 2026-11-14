"""Repeatable host regressions against the current Android13 callback source."""
from pathlib import Path
import argparse,subprocess,tempfile
parser=argparse.ArgumentParser()
parser.add_argument('--platform-root',type=Path,default=Path('/root/t110-android13-audit/platform'))
parser.add_argument('--tests',type=Path,default=Path('/root/t110-android13-audit/device/development/android13-audit-20261114/tests'))
args=parser.parse_args()
def function(text,signature):
    start=text.index(signature);brace=text.index('{',start);depth=1;end=brace+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return start,end,text[start:end]
cases=[('dequeue_callback_test.cpp','frameworks/native/libs/gui/Surface.cpp','int Surface::hook_dequeueBuffer_DEPRECATED('),
       ('framebuffer_resume_test.cpp','hardware/interfaces/graphics/composer/2.1/default/T110Framebuffer.cpp','int enableScreen(')]
with tempfile.TemporaryDirectory(prefix='t110-offline-') as temp:
    for name,relative,signature in cases:
        current=function((args.platform_root/relative).read_text(),signature)[2]
        fixture=(args.tests/name).read_text()
        start,end,_=function(fixture,signature)
        p=Path(temp)/name;p.write_text(fixture[:start]+current+fixture[end:])
        binary=p.with_suffix('')
        command=['g++','-std=c++17','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                 '-I'+str(args.platform_root/'hardware/interfaces/graphics/composer/2.1/default'),str(p),'-o',str(binary)]
        subprocess.run(command,check=True)
        subprocess.run([str(binary)],check=True)
print('Both current-source host regressions passed. No ARM/platform/hardware qualification implied.')
