"""Build own freestanding hooks and adapt the user's supported executable.

Python standard library + existing GCC/binutils on Linux. No game data is
downloaded. The original executable is hash checked and never overwritten.
"""
from pathlib import Path
import hashlib,json,os,struct,subprocess,tempfile

ROOT=Path(__file__).resolve().parent
ORIGINAL_SHA='16663d2e79b21de16901082929512ecc8af6ec3a13db9b6650c3d7abfd41ade6'
BASE=0x400000
HOOK=0x3652000
RDTSC=[0x431454,0x46e240,0x46e3d0,0x476d83,0x476e23,0x476f0e,
       0x4770e3,0x477135,0x479957,0x479b0f,0x479b51,0x479bb1,
       0x479c18,0x479c4c,0x48d8f1,0x48d9a4,0x4a938a,0x4a9532,
       0x4a957e,0x4a95da,0x4a97cd,0x4a9811]
UP=[0x47a17f,0x4842dd,0x48e578,0x48e5f2,0x48e8ea,0x48e947]
INDEXED=[0x445902,0x44598d,0x455151,0x47b173,0x47b1da,0x47c6d5,
         0x47c713,0x484c4c,0x489949,0x48bf56,0x492bb8,0x4931bf]

def align(v,n):return (v+n-1)//n*n

def main():
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            if (proc/'comm').read_text().strip() in ('sdaemon.exe','fnf-ally.exe'):
                raise SystemExit('Close the game before building.')
        except (FileNotFoundError,PermissionError):pass
    original=ROOT/'game/sdaemon.exe';output=ROOT/'game/fnf-ally.exe'
    data=bytearray(original.read_bytes())
    if hashlib.sha256(data).hexdigest()!=ORIGINAL_SHA:
        raise SystemExit('Unsupported original executable; no files changed.')
    def u16(o):return struct.unpack_from('<H',data,o)[0]
    def u32(o):return struct.unpack_from('<I',data,o)[0]
    pe=u32(0x3c);optional=pe+24;section_table=optional+u16(pe+20)
    section_count=u16(pe+6)
    sections=[struct.unpack_from('<8s6I2HI',data,section_table+40*i) for i in range(section_count)]
    assert u16(optional)==0x10b and u32(optional+28)==BASE
    assert u32(optional+56)==HOOK-BASE
    def offset(va):
        rva=va-BASE
        for s in sections:
            if s[2]<=rva<s[2]+s[3]:return s[4]+rva-s[2]
        raise ValueError(f'Address outside file: {va:x}')
    # Each supported RDTSC is followed by a non-relative LEA ECX instruction.
    # Copy the user's displaced bytes only into their private build output.
    asm=['.text']
    clock_lengths={}
    for a in RDTSC:
        o=offset(a);assert data[o:o+3]==bytes.fromhex('0f318d')
        length=9 if data[o+3:o+5]==bytes.fromhex('8c24') else 8
        if length==8:assert data[o+3]==0x0d
        clock_lengths[a]=length
        asm.extend([f'.global clock_{a:x}',f'clock_{a:x}:','rdtsc','pushfl',
                    'subl pause_cycles,%eax','sbbl pause_cycles+4,%edx','popfl',
                    '.byte '+','.join(str(x) for x in data[o+2:o+length]),
                    f'jmp {a+length}'])
    with tempfile.TemporaryDirectory(prefix='fnf-hooks-') as temp:
        t=Path(temp);(t/'clocks.S').write_text('\n'.join(asm)+'\n')
        subprocess.run(['gcc','-m32','-Os','-ffreestanding','-fno-pic','-fno-pie',
                        '-fno-stack-protector','-fno-asynchronous-unwind-tables','-nostdlib',
                        '-c',str(ROOT/'patch/widescreen.c'),'-o',str(t/'wide.o')],check=True)
        subprocess.run(['gcc','-m32','-c',str(t/'clocks.S'),'-o',str(t/'clocks.o')],check=True)
        subprocess.run(['ld','-m','elf_i386','-T',str(ROOT/'patch/link.ld'),str(t/'wide.o'),str(t/'clocks.o'),'-o',str(t/'hooks.elf')],check=True)
        subprocess.run(['objcopy','-O','binary',str(t/'hooks.elf'),str(t/'hooks.bin')],check=True)
        symbols={}
        for line in subprocess.check_output(['nm',str(t/'hooks.elf')],text=True).splitlines():
            fields=line.split()
            if len(fields)==3:symbols[fields[2]]=int(fields[0],16)
        code=(t/'hooks.bin').read_bytes()
    raw=align(len(data),u32(optional+36));raw_size=align(len(code),u32(optional+36))
    virtual_size=align(symbols['_end']-HOOK,u32(optional+32))
    header=section_table+section_count*40
    assert data[header:header+40]==bytes(40) and header+40<=u32(optional+60)
    data[header:header+40]=struct.pack('<8s6I2HI',b'.ally',virtual_size,HOOK-BASE,raw_size,raw,0,0,0,0,0xe0000060)
    struct.pack_into('<H',data,pe+6,section_count+1)
    struct.pack_into('<I',data,optional+56,HOOK-BASE+virtual_size)
    data.extend(bytes(raw-len(data)));data.extend(code);data.extend(bytes(raw_size-len(code)))
    patches=[]
    def patch(a,target,size=6,jump=False):
        o=offset(a);old=bytes(data[o:o+size])
        opcode=b'\xe9' if jump else b'\xe8'
        data[o:o+size]=opcode+struct.pack('<i',symbols[target]-a-5)+b'\x90'*(size-5)
        patches.append({'address':hex(a),'original':old.hex(),'target':target})
    for a,target in [(0x484ddb,'projection'),(0x479e47,'viewport')]+[(a,'draw_up') for a in UP]+[(a,'draw_indexed') for a in INDEXED]+[(a,'query_counter') for a in [0x476d95,0x476e78]]+[(a,'tick_count') for a in [0x495207,0x495401]]:
        assert data[offset(a)]==0xff
        patch(a,target)
    for a,target in [(0x4797d4,'create_primary'),(0x4798c7,'create_retry')]:
        assert data[offset(a):offset(a)+5]==bytes.fromhex('ff523c8bf0')
        patch(a,target,5,True)
    for a,length in clock_lengths.items():patch(a,f'clock_{a:x}',length,True)
    tmp=output.with_suffix('.building');tmp.write_bytes(data);os.replace(tmp,output)
    (ROOT/'docs').mkdir(exist_ok=True)
    report={'original_sha256':ORIGINAL_SHA,'sha256':hashlib.sha256(data).hexdigest(),
            'resolution':[1920,1080],'logical_ui':[640,480],'symbols':symbols,'patches':patches}
    (ROOT/'docs/widescreen-build.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built 1920x1080 adaptation:',report['sha256'])

if __name__=='__main__':main()
