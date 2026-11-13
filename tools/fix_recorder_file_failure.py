"""Keep the normal Lineage Recorder from sharing a failed/missing recording."""
from pathlib import Path
base=Path('/root/t110-lineage14/android/packages/apps/Recorder/app/src/main')
p=base/'java/org/lineageos/recorder/sounds/SoundRecorderService.java'
s=p.read_text()
if 'Cannot create recording directory' not in s:
    s=s.replace('import android.util.Log;', 'import android.util.Log;\nimport android.widget.Toast;')
    s=s.replace('private RecorderStatus mStatus', 'private volatile RecorderStatus mStatus')
    s=s.replace('        mElapsedTime = 0;', '        mElapsedTime = 0;\n        mOutFilePath = null;')
    s=s.replace('''        if (file == null) {
            return;
        }''','''        if (file == null) {
            Utils.setStatus(this, Utils.UiStatus.NOTHING);
            Toast.makeText(this, R.string.sound_file_error, Toast.LENGTH_LONG).show();
            return;
        }''')
    s=s.replace('''            mStatus = RecorderStatus.STOPPED;
            mStatus = RecorderStatus.STOPPED;
            mRecord.stop();
            mRecord.release();''','''            mStatus = RecorderStatus.STOPPED;
            mRecord.stop();
            // Flush and close the PCM writer before conversion or deletion.
            if (mRecordThread != null) {
                try {
                    mRecordThread.join(2000);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                if (mRecordThread.isAlive()) {
                    Log.e(TAG, "Recording writer did not stop; preserving PCM");
                    mFilePath = null;
                }
            }
            mRecord.release();''')
    s=s.replace('''        File tmpFile = new File(mFilePath);''','''        stopForeground(true);
        Utils.setStatus(this, Utils.UiStatus.NOTHING);
        if (mFilePath == null) return;
        File tmpFile = new File(mFilePath);''')
    s=s.replace('''        if (!RECORDINGS_DIR.exists()) {
            //noinspection ResultOfMethodCallIgnored
            RECORDINGS_DIR.mkdirs();
        }
        return file;''','''        if (!RECORDINGS_DIR.isDirectory() && !RECORDINGS_DIR.mkdirs()) {
            Log.e(TAG, "Cannot create recording directory");
            return null;
        }
        // Verify storage access before starting the microphone or its worker.
        try (FileOutputStream output = new FileOutputStream(file)) {
            return file;
        } catch (IOException e) {
            Log.e(TAG, "Cannot create recording file", e);
            return null;
        }''')
    s=s.replace('''                    int mStatus = mRecord.read(mData, 0, mData.length);
                    if (mStatus == AudioRecord.ERROR_INVALID_OPERATION ||
                            mStatus == AudioRecord.ERROR_BAD_VALUE) {''','''                    int count = mRecord.read(mData, 0, mData.length);
                    if (count < 0) {''')
    s=s.replace('out.write(mData, 0, BUFFER_SIZE);', 'out.write(mData, 0, count);')
    s=s.replace('''    public void createShareNotification() {
        Intent''','''    public void createShareNotification() {
        if (mOutFilePath == null || !new File(mOutFilePath).isFile()) return;
        Intent''')
    p.write_text(s)
p=base/'java/org/lineageos/recorder/RecorderActivity.java';s=p.read_text()
s=s.replace('''                mSoundService.setAudioListener(mRecordingVisualizer);
            }''','''                mSoundService.setAudioListener(mRecordingVisualizer);
                if (Utils.isSoundRecording(RecorderActivity.this) &&
                        !mSoundService.isRecording()) {
                    Utils.setStatus(RecorderActivity.this, Utils.UiStatus.NOTHING);
                    refresh();
                }
            }''')
s=s.replace('''            Utils.setStatus(this, Utils.UiStatus.SOUND);''','''            Utils.setStatus(this, mSoundService.isRecording()
                    ? Utils.UiStatus.SOUND : Utils.UiStatus.NOTHING);''')
p.write_text(s)
p=base/'java/org/lineageos/recorder/sounds/PcmConverter.java';s=p.read_text()
s=s.replace('16 * 441000 * CHANNELS / 8', '16 * SAMPLE_RATE * CHANNELS / 8')
s=s.replace('RECORDER_BPP * 441000 * CHANNELS / 8', 'RECORDER_BPP * SAMPLE_RATE * CHANNELS / 8')
s=s.replace('''            while (input.read(data) != -1) {
                output.write(data);
            }''','''            int count;
            while ((count = input.read(data)) != -1) {
                output.write(data, 0, count);
            }''')
s=s.replace('(byte) (2 * 16 / 8);  // block align', '(byte) (CHANNELS * RECORDER_BPP / 8);  // block align')
p.write_text(s)
p=base/'res/values/strings.xml';s=p.read_text()
if 'name="sound_file_error"' not in s:
    s=s.replace('</resources>', '    <string name="sound_file_error">Unable to save a recording. Check storage access and try again.</string>\n</resources>')
p.write_text(s)
print('Guarded Recorder file creation/sharing and corrected PCM write/WAV lengths.')
