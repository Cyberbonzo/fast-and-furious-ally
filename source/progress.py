"""Local profile, native save requests and versioned progress backups."""
from pathlib import Path
import hashlib,json,os,secrets,struct,time

ROOT=Path(__file__).resolve().parents[1]
FILES=('money_players.pdt','cops2.hst','prefs','prefsbak','audits','auditsbak')
SIZES={'money_players.pdt':720008,'cops2.hst':2628,'prefs':4612,'prefsbak':4612,'audits':5476,'auditsbak':5476}

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(data);os.replace(tmp,path)

def backup():
    dest=ROOT/'saves';dest.mkdir(exist_ok=True)
    for name in FILES:
        src=ROOT/'game'/name
        if not src.exists():continue
        before=src.stat();data=src.read_bytes();after=src.stat()
        if len(data)!=SIZES[name] or before.st_mtime_ns!=after.st_mtime_ns:continue
        if src.read_bytes()!=data:continue
        digest=hashlib.sha256(data).hexdigest()
        current=dest/'latest'/name
        if current.exists() and current.read_bytes()==data:continue
        atomic(dest/'history'/name/(digest[:16]+'.bin'),data)
        atomic(current,data)
    # Keep at most 20 generations per file, only within this private backup tree.
    for name in FILES:
        history=dest/'history'/name
        if history.is_dir():
            for old in sorted(history.glob('*.bin'),key=lambda p:p.stat().st_mtime,reverse=True)[20:]:old.unlink()

def prepare():
    for name in FILES:
        dest=ROOT/'game'/name;latest=ROOT/'saves/latest'/name
        if not dest.exists() and latest.exists():atomic(dest,latest.read_bytes())
    backup()
    # Native preferences: KPH and difficulty 1 (easiest).
    for name in ('prefs','prefsbak'):
        p=ROOT/'game'/name
        if p.exists():
            data=bytearray(p.read_bytes())
            if len(data)!=4612 or data[:4]!=b'CFRP':raise RuntimeError('Unsupported preferences format')
            struct.pack_into('<I',data,4+0x4cfe90-0x4cf968,1)
            struct.pack_into('<I',data,4+0x4cff90-0x4cf968,1)
            atomic(p,data)
    path=ROOT/'state/profile.json'
    if not path.exists():
        atomic(path,json.dumps({'pin':str(secrets.randbelow(900000)+100000),'name':'ALLY','infinite_boost':False},indent=2).encode())
    profile=json.loads(path.read_text())
    if not profile['pin'].isdigit() or not 1<=len(profile['pin'])<=10:raise RuntimeError('Invalid local PIN')
    return profile

class Runtime:
    def __init__(self):
        self.profile=prepare();self.infinite=bool(self.profile.get('infinite_boost',False))
        self.symbols=json.loads((ROOT/'docs/widescreen-build.json').read_text())['symbols']
        self.fd=None;self.pid=None;self.last_probe=0;self.last_backup=0
        self.login_stage='idle';self.login_at=0;self.pin_index=0;self.logged=False
        self.stock=None;self.stock_player=None;self.last_save=0;self.last_record=None
        self.previous_phase=None;self.phase_at=0
    def close(self):
        if self.fd is not None:os.close(self.fd)
        self.fd=None;self.pid=None
    def u(self,a):return struct.unpack('<I',os.pread(self.fd,4,a))[0]
    def w(self,a,v):os.pwrite(self.fd,struct.pack('<I',v),a)
    def key(self,k):
        if self.u(0x35b6a9c):return False
        os.pwrite(self.fd,bytes([k]),0x35b6708);self.w(0x35b6a9c,1);return True
    def request_save(self):
        if self.fd is not None and self.logged:
            req=self.symbols['save_request'];done=self.symbols['save_done']
            if self.u(req)==self.u(done):self.w(req,(self.u(req)+1)&0xffffffff)
    def toggle(self):
        self.infinite=not self.infinite
        self.profile['infinite_boost']=self.infinite
        atomic(ROOT/'state/profile.json',json.dumps(self.profile,indent=2).encode())
    def tick(self,pids,paused):
        now=time.monotonic()
        if self.pid not in pids:
            self.close();self.logged=False;self.login_stage='idle';self.stock=None
            if pids:
                self.pid=pids[0];self.fd=os.open(f'/proc/{self.pid}/mem',os.O_RDWR)
        if self.fd is None:return
        if os.pread(self.fd,5,0x476e70)!=bytes.fromhex('83ec086888'):return
        mode=self.u(0x5ab0b0);phase=self.u(0x5ab0ac)
        if (mode,phase)!=self.previous_phase:self.previous_phase=(mode,phase);self.phase_at=now
        record=os.pread(self.fd,240,0x5b2ab8)
        pin=record[:11].split(b'\0')[0]
        if mode==1:self.login_stage='idle';self.logged=False
        if mode==3 and not paused:
            if self.login_stage=='typing' and phase in (4,5,6,7) and now-self.login_at>2:self.login_stage='idle'
            if self.login_stage=='idle' and phase in (4,5,6,7) and not pin and now-self.phase_at>1:
                first=self.profile['pin'][0]
                if self.key(10 if first=='0' else int(first)-1):
                    self.pin_index=1;self.login_stage='typing';self.login_at=now
            elif self.login_stage=='typing' and phase==8 and now-self.login_at>.3:
                if self.pin_index<len(self.profile['pin']):
                    digit=self.profile['pin'][self.pin_index]
                    if self.key(10 if digit=='0' else int(digit)-1):self.pin_index+=1;self.login_at=now
                elif self.key(11):self.login_stage='submitted';self.login_at=now
            elif self.login_stage=='submitted' and phase==9 and now-self.login_at>1:
                name=self.profile['name'].upper().encode('ascii')[:10]
                os.pwrite(self.fd,name+b'\0',0x5b2ac3)
                self.login_stage='named'
            if pin==self.profile['pin'].encode() and record[11]!=0 and phase not in (8,9):
                if not self.logged:print('Local profile loaded',flush=True)
                self.logged=True;self.login_stage='loaded'
            if self.logged and record!=self.last_record and now-self.last_save>3:
                self.request_save();self.last_record=record;self.last_save=now
        player=self.u(0x5aaf20)
        racing=mode==3 and phase==13 and 0x100000<=player<0x7ffff000
        if racing:
            current=self.u(player+0x1cc)
            if self.infinite:
                if self.stock_player!=player or self.stock is None:self.stock=current;self.stock_player=player
                if current<3:self.w(player+0x1cc,3)
            elif self.stock is not None and self.stock_player==player:
                self.w(player+0x1cc,self.stock);self.stock=None
        else:self.stock=None;self.stock_player=None
        if now-self.last_backup>10:
            backup();self.last_backup=now
