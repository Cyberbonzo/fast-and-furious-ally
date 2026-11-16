"""Suspend the adapted build and advance its virtual-clock pause offsets."""
import os,signal,struct,time,ctypes,mmap,json
from pathlib import Path
class Pause:
    def __init__(self):
        self.stopped={}
        self.symbols=json.loads((Path(__file__).resolve().parents[1]/'docs/widescreen-build.json').read_text())['symbols']
        self.code=mmap.mmap(-1,4096,prot=mmap.PROT_READ|mmap.PROT_WRITE|mmap.PROT_EXEC)
        self.code.write(bytes.fromhex('0faee80f3148c1e2204809d0c3'))
        self.tsc=ctypes.CFUNCTYPE(ctypes.c_uint64)(ctypes.addressof(ctypes.c_char.from_buffer(self.code)))
    def apply(self,pids,value):
        if value:
            for pid in pids:
                if pid in self.stopped:continue
                fd=os.open(f'/proc/{pid}/mem',os.O_RDWR)
                try:
                    if os.pread(fd,5,0x476e70)!=bytes.fromhex('83ec086888'):
                        raise RuntimeError('Unsupported game clock')
                    os.kill(pid,signal.SIGSTOP)
                    for _ in range(100):
                        if '\nState:\tT' in Path(f'/proc/{pid}/status').read_text():break
                        time.sleep(.001)
                    else:raise RuntimeError('Game did not stop')
                    self.stopped[pid]=(fd,time.monotonic_ns(),self.tsc())
                except BaseException:
                    os.kill(pid,signal.SIGCONT);os.close(fd);raise
        else:
            for pid,(fd,ns,tsc) in list(self.stopped.items()):
                try:
                    elapsed=time.monotonic_ns()-ns;cycles=self.tsc()-tsc
                    freq=struct.unpack('<Q',os.pread(fd,8,0x35d1fb0))[0]
                    for symbol,delta,fmt in [('pause_qpc',round(elapsed*freq/1e9),'Q'),('pause_cycles',cycles,'Q'),('pause_millis',round(elapsed/1e6),'I')]:
                        address=self.symbols[symbol];size=struct.calcsize(fmt)
                        old=struct.unpack('<'+fmt,os.pread(fd,size,address))[0]
                        os.pwrite(fd,struct.pack('<'+fmt,(old+delta)&((1<<(size*8))-1)),address)
                    print('Pause time excluded:',round(elapsed/1e9,3),'s',flush=True)
                finally:
                    try:os.kill(pid,signal.SIGCONT)
                    except ProcessLookupError:pass
                    os.close(fd);del self.stopped[pid]
