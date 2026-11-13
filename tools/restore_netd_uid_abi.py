"""Match Nougat netd UID policy messages to our preserved Android13 kernel ABI."""
from pathlib import Path
p = Path('/root/t110-lineage14/android/system/netd/server/RouteController.cpp')
s = p.read_text()
old='''const uint16_t FRA_UID_START = 18;
const uint16_t FRA_UID_END   = 19;'''
new='''const uint16_t FRA_UID_START = 18;
#ifndef T110_MRVL_LEGACY
const uint16_t FRA_UID_END   = 19;
#endif'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
old='''rtattr FRATTR_UID_START = { U16_RTA_LENGTH(sizeof(uid_t)),    FRA_UID_START };
rtattr FRATTR_UID_END   = { U16_RTA_LENGTH(sizeof(uid_t)),    FRA_UID_END };'''
new='''#ifdef T110_MRVL_LEGACY
// Our retained kernel implements modern FRA_UID_RANGE (20), not the old
// Android attributes 18/19. 19 is L3MDEV there and is correctly rejected.
// Preserve the UID restriction; never drop selectors to make a rule succeed.
struct T110UidRange { uint32_t start; uint32_t end; };
static_assert(sizeof(T110UidRange) == 8, "Kernel UID range ABI");
rtattr FRATTR_UID_RANGE = { U16_RTA_LENGTH(sizeof(T110UidRange)), 20 };
#else
rtattr FRATTR_UID_START = { U16_RTA_LENGTH(sizeof(uid_t)),    FRA_UID_START };
rtattr FRATTR_UID_END   = { U16_RTA_LENGTH(sizeof(uid_t)),    FRA_UID_END };
#endif'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
old='''    rtattr fraOifName = { U16_RTA_LENGTH(oifLength), FRA_OIFNAME };

    iovec iov[] = {'''
new='''    rtattr fraOifName = { U16_RTA_LENGTH(oifLength), FRA_OIFNAME };
#ifdef T110_MRVL_LEGACY
    T110UidRange uidRange = { uidStart, uidEnd };
#endif

    iovec iov[] = {'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
old='''        { &FRATTR_UID_START, isUidRule ? sizeof(FRATTR_UID_START) : 0 },
        { &uidStart,         isUidRule ? sizeof(uidStart) : 0 },
        { &FRATTR_UID_END,   isUidRule ? sizeof(FRATTR_UID_END) : 0 },
        { &uidEnd,           isUidRule ? sizeof(uidEnd) : 0 },'''
new='''#ifdef T110_MRVL_LEGACY
        { &FRATTR_UID_RANGE, isUidRule ? sizeof(FRATTR_UID_RANGE) : 0 },
        { &uidRange,        isUidRule ? sizeof(uidRange) : 0 },
#else
        { &FRATTR_UID_START, isUidRule ? sizeof(FRATTR_UID_START) : 0 },
        { &uidStart,         isUidRule ? sizeof(uidStart) : 0 },
        { &FRATTR_UID_END,   isUidRule ? sizeof(FRATTR_UID_END) : 0 },
        { &uidEnd,           isUidRule ? sizeof(uidEnd) : 0 },
#endif'''
if new not in s:
    assert s.count(old)==1
    s=s.replace(old,new)
p.write_text(s)
print('Nougat netd now emits the retained kernel modern UID range attribute.')
