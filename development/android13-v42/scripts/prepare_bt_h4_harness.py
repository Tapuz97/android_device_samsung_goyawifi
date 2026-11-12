"""Register H4 receive expectations before delivery and bound notification waits."""
from pathlib import Path
import difflib,hashlib,json,os,re
assert os.environ.get('WSL_DISTRO_NAME')=='T110Build'
p=Path('/mnt/c/Users/Gal/Documents/ChatGPT/Electronic Repair/SM-T110');root=Path('/root/t110-build/lineage20/hardware/interfaces');e=p/'evidence/hardware-bt-sd'
name='bluetooth/1.0/default/test/h4_protocol_unittest.cc';f=root/name;receipt=e/'h4-harness-source.json';ledger_path=e/'h4-production-source.json'
sha=lambda data:hashlib.sha256(data).hexdigest()
ledger=json.loads(ledger_path.read_text())
if receipt.exists():
 saved=json.loads(receipt.read_text());assert sha(f.read_bytes())==saved['after_sha256']==ledger['files'][name]
 print('H4_RECEIVE_HARNESS_ALREADY_FIXED');raise SystemExit(0)
before=f.read_text();assert sha(before.encode())==ledger['files'][name]
after=before.replace('ACTION_P2(Notify, mutex, condition)', 'ACTION_P3(Notify, mutex, condition, received)')
assert after!=before;after=after.replace('  condition->notify_one();','  *received = true;\n  condition->notify_one();',1)
pattern=r'  void WriteAndExpectInbound(?:AclData|ScoData|Event|IsoData)\(char\* payload\) \{.*?\n  \}'
matches=list(re.finditer(pattern,after,re.S));assert len(matches)==4
for match in reversed(matches):
 block=match[0];begin=block.index('    ALOGD("%s writing"');end=block.index('    ALOGD("%s waiting"',begin)
 writes=block[begin:end];block=block[:begin]+block[end:]
 block=block.replace('    std::condition_variable done;','    std::condition_variable done;\n    bool received = false;')
 old='        .WillOnce(Notify(&mutex, &done));';assert block.count(old)==1
 block=block.replace(old,'        .WillOnce(Notify(&mutex, &done, &received));\n\n'+writes.rstrip())
 block=block.replace('''    // Fail if it takes longer than 100 ms.
    auto timeout_time =
        std::chrono::steady_clock::now() + std::chrono::milliseconds(100);
''','')
 block=block.replace('    {\n      std::unique_lock<std::mutex> lock(mutex);','    bool completed = false;\n    {\n      std::unique_lock<std::mutex> lock(mutex);')
 wait='completed = done.wait_for(lock, std::chrono::seconds(2), [&]() { return received; });'
 block=block.replace('done.wait_until(lock, timeout_time);',wait).replace('done.wait(lock);',wait)
 end=block.rfind('\n  }');block=block[:end]+'''\n    if (!completed) fd_watcher_.StopWatchingFileDescriptors();
    EXPECT_TRUE(completed);'''+block[end:]
 assert block.index('EXPECT_CALL')<block.index('write(fake_uart_') and 'done.wait(lock)' not in block
 after=after[:match.start()]+block+after[match.end():]
patch=p/'patches/0103-bluetooth-h4-register-test-receivers-before-write.patch';assert not patch.exists()
patch.write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),'a/'+name,'b/'+name)))
f.write_text(after);record=dict(before_sha256=sha(before.encode()),after_sha256=sha(after.encode()),patch_sha256=sha(patch.read_bytes()),
 root_cause='Actual SCO/event payload callbacks arrived before EXPECT_CALL; event test then waited indefinitely. Trace and gmock warnings saved locally.',
 exact_payload_assertions_retained=True,receive_cases=4,wait_seconds=2)
receipt.write_text(json.dumps(record,indent=2)+'\n');ledger['files'][name]=record['after_sha256'];ledger['additional_test_patch_sha256']=record['patch_sha256']
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n');print('H4_RECEIVE_HARNESS_FIXED_ALL_ASSERTIONS_RETAINED')
