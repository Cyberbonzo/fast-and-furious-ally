from pathlib import Path
import os,json,subprocess,hashlib
from progress import prepare,backup
r=Path(__file__).resolve().parents[1]
if hashlib.sha256((r/'game/sdaemon.exe').read_bytes()).hexdigest()!='16663d2e79b21de16901082929512ecc8af6ec3a13db9b6650c3d7abfd41ade6':raise SystemExit('Unsupported sdaemon.exe revision')
manifest=json.loads((r/'docs/widescreen-build.json').read_text())
if hashlib.sha256((r/'game/fnf-ally.exe').read_bytes()).hexdigest()!=manifest['sha256']:raise SystemExit('Adapted executable does not match its build manifest. Run build.py again.')
prepare()
env=os.environ.copy();env.update(json.loads((r/'source/runtime-env.json').read_text()))
env.update(STEAM_COMPAT_CLIENT_INSTALL_PATH=str(Path.home()/'.local/share/Steam'),STEAM_COMPAT_DATA_PATH=str(r/'compatdata'),PROTON_LOG='0',WINEDEBUG='-all',WAL_LOG='Z:'+str(r/'logs/payload.log').replace('/','\\'))
env.pop('LD_PRELOAD',None)
for d in ['logs','compatdata']:(r/d).mkdir(exist_ok=True)
with (r/'logs/controls.log').open('a') as log:
 helper=subprocess.Popen(['python3',str(r/'source/controls.py')],env=env,stdout=log,stderr=subprocess.STDOUT)
 try:
  with (r/'logs/session.log').open('a') as out:
   subprocess.run([str(Path.home()/'.local/share/Steam/steamapps/common/Proton 11.0/proton'),'waitforexitandrun',str(r/'dependencias/wal-loader.exe'),str(r/'dependencias/wal_rawthrills.dll'),str(r/'game/fnf-ally.exe')],cwd=r/'game',env=env,stdout=out,stderr=subprocess.STDOUT)
 finally:
  helper.terminate();helper.wait(timeout=8);backup()
