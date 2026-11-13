"""Exercise the real Recorder converter with a final partial PCM buffer."""
from pathlib import Path
import subprocess,tempfile,shutil
source=Path('/root/t110-lineage14/android/packages/apps/Recorder/app/src/main/java/org/lineageos/recorder/sounds/PcmConverter.java')
with tempfile.TemporaryDirectory(prefix='t110-recorder-wav-') as name:
    root=Path(name)
    files={
      'android/util/Log.java':'package android.util; public class Log { public static int d(String a,String b){return 0;} public static int e(String a,String b){return 0;} }',
      'org/lineageos/recorder/utils/Utils.java':'package org.lineageos.recorder.utils; import java.io.*; public class Utils { public static void closeQuietly(Closeable c){try{if(c!=null)c.close();}catch(IOException e){}} }',
      'org/lineageos/recorder/sounds/SoundRecorderService.java':'package org.lineageos.recorder.sounds; public class SoundRecorderService { static final String EXTENSION=".pcm"; }',
      'org/lineageos/recorder/sounds/ConverterTest.java':'''package org.lineageos.recorder.sounds;
import java.nio.*; import java.nio.file.*; import java.util.*;
public class ConverterTest { public static void main(String[] args) throws Exception {
 Path p=Paths.get(args[0],"test.pcm"); byte[] data={0,1,2,3,4,5,6,7,8,9}; Files.write(p,data);
 String wave=p.toString().replace(".pcm",".wav"); PcmConverter.convertToWave(wave,8);
 byte[] bytes=Files.readAllBytes(Paths.get(wave)); ByteBuffer h=ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN);
 if(bytes.length!=54 || h.getInt(4)!=46 || h.getInt(40)!=10 || h.getInt(24)!=44100 || h.getInt(28)!=88200 || h.getShort(32)!=2 || !Arrays.equals(data,Arrays.copyOfRange(bytes,44,54))) throw new AssertionError("WAV header or partial-buffer corruption");
 System.out.println("PASS: exact PCM length, partial final buffer, mono block alignment and byte rate");
}}'''}
    for name,text in files.items():
        p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    shutil.copy2(source,root/'org/lineageos/recorder/sounds/PcmConverter.java')
    java='/usr/lib/jvm/java-8-openjdk-amd64/bin/'
    subprocess.run([java+'javac','-d',str(root)]+[str(p) for p in root.rglob('*.java')],check=True)
    subprocess.run([java+'java','-cp',str(root),'org.lineageos.recorder.sounds.ConverterTest',str(root)],check=True)
