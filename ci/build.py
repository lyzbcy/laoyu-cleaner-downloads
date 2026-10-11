"""Assemble and test pure-JS payload on a real macOS runner; no user cleanup."""
from pathlib import Path
import hashlib,json,os,platform,plistlib,shutil,subprocess,sys,urllib.request,zipfile
ROOT=Path.cwd(); OUT=ROOT/'out'; OUT.mkdir(exist_ok=True)
VERSION=os.environ['APP_VERSION']; WIN_HASH=os.environ['WINDOWS_SHA256']; ARCH=os.environ['APP_ARCH']; ELECTRON='44.7.0'
if sys.platform!='darwin': raise SystemExit('This gate requires actual macOS')
if platform.machine()!=({'x64':'x86_64','arm64':'arm64'}[ARCH]):raise SystemExit('Runner architecture mismatch')
def run(args,**kwargs):return subprocess.run([str(x) for x in args],check=True,**kwargs)
def download(url,file):
    request=urllib.request.Request(url,headers={'User-Agent':'LaoyuCleaner-build','Accept':'application/octet-stream'})
    with urllib.request.urlopen(request,timeout=60) as r,open(file,'wb') as f:shutil.copyfileobj(r,f)
def sha(file):
    h=hashlib.sha256()
    with open(file,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
win=ROOT/'windows.zip';download(f'https://github.com/lyzbcy/laoyu-cleaner-downloads/releases/download/v{VERSION}/LaoyuCleaner-Windows.zip',win)
if sha(win)!=WIN_HASH:raise SystemExit('Windows payload digest mismatch')
with zipfile.ZipFile(win) as z:
    (ROOT/'app.asar').write_bytes(z.read('resources/app.asar'))
electron_zip=ROOT/'electron-mac.zip';name=f'electron-v{ELECTRON}-darwin-{ARCH}.zip'
base=f'https://github.com/electron/electron/releases/download/v{ELECTRON}/'
download(base+'SHASUMS256.txt',ROOT/'electron-shasums.txt')
hashes={line.split()[1].lstrip('*'):line.split()[0] for line in (ROOT/'electron-shasums.txt').read_text().splitlines() if len(line.split())==2}
download(base+name,electron_zip)
if sha(electron_zip)!=hashes[name]:raise SystemExit('Official Electron digest mismatch')
runtime=ROOT/'runtime';runtime.mkdir();run(['/usr/bin/ditto','-x','-k',electron_zip,runtime])
stock=runtime/'Electron.app';exe=stock/'Contents/MacOS/Electron'
run([exe,ROOT/'ci/acceptance.cjs',ROOT/'app.asar',OUT/'recycle-restore.json'],timeout=120)
app=ROOT/'捞鱼 C 盘清理.app';run(['/usr/bin/ditto',stock,app])
resources=app/'Contents/Resources';shutil.copy2(ROOT/'app.asar',resources/'app.asar');(resources/'default_app.asar').unlink(missing_ok=True)
info=app/'Contents/Info.plist'
with open(info,'rb') as f:pl=plistlib.load(f)
pl.update(CFBundleIdentifier='com.laoyu.c-drive-cleaner',CFBundleName='捞鱼 C 盘清理',CFBundleDisplayName='捞鱼 C 盘清理',CFBundleShortVersionString=VERSION,CFBundleVersion=VERSION,CFBundleExecutable='LaoyuCleaner',NSHighResolutionCapable=True)
with open(info,'wb') as f:plistlib.dump(pl,f)
(app/'Contents/MacOS/Electron').rename(app/'Contents/MacOS/LaoyuCleaner')
run(['npm','exec','--yes','--package=@electron/asar@3.4.1','--','asar','extract',ROOT/'app.asar',ROOT/'payload'],timeout=180)
iconset=ROOT/'cleaner.iconset';iconset.mkdir()
for n in [16,32,128,256,512]:
    for scale in [1,2]:
        target=iconset/(f'icon_{n}x{n}'+('@2x' if scale==2 else '')+'.png')
        run(['/usr/bin/sips','-z',n*scale,n*scale,ROOT/'payload/assets/icon.png','--out',target],stdout=subprocess.DEVNULL)
run(['/usr/bin/iconutil','-c','icns',iconset,'-o',resources/'electron.icns'])
run(['/usr/bin/codesign','--force','--deep','--sign','-',app]);run(['/usr/bin/codesign','--verify','--deep','--strict',app])
binary=app/'Contents/MacOS/LaoyuCleaner';architecture=run(['/usr/bin/lipo','-archs',binary],capture_output=True,text=True).stdout.strip()
if architecture!=({'x64':'x86_64','arm64':'arm64'}[ARCH]):raise SystemExit('Application architecture mismatch')
smoke=subprocess.run([str(binary),'--smoke','--disable-gpu','--in-process-gpu'],capture_output=True,text=True,timeout=180,env={**os.environ,'LAOYU_CI':'1'})
(OUT/'ui-smoke.log').write_text(smoke.stdout+'\n'+smoke.stderr)
if smoke.returncode!=0:
    # Diagnostic copy only. Never package or publish altered application bytes.
    import tempfile
    for log in Path(tempfile.gettempdir()).glob('laoyu-cleaner-smoke-*/logs/startup-error.json'):
        shutil.copy2(log,OUT/(log.parent.parent.name+'-startup.json'))
    main=ROOT/'payload/src/main.cjs';original=main.read_text()
    main.write_text(original.replace("}).catch(async e=>{try{", "}).catch(async e=>{console.error('DIAGNOSTIC_ONLY',e.stack);try{"))
    run(['npm','exec','--yes','--package=@electron/asar@3.4.1','--','asar','pack',ROOT/'payload',ROOT/'diagnostic.asar'],timeout=180)
    shutil.copy2(ROOT/'diagnostic.asar',resources/'app.asar')
    run(['/usr/bin/codesign','--force','--deep','--sign','-',app])
    diagnostic=subprocess.run([str(binary),'--smoke','--disable-gpu','--in-process-gpu'],capture_output=True,text=True,timeout=180,env={**os.environ,'LAOYU_CI':'1'})
    (OUT/'diagnostic-only.log').write_text(diagnostic.stdout+'\n'+diagnostic.stderr)
    shutil.copy2(ROOT/'app.asar',resources/'app.asar');main.write_text(original)
    raise SystemExit(f'Unmodified packaged UI exited {smoke.returncode}; diagnostic-only log collected; no Mac ZIP published')
receipt_path=next((line.split('=',1)[1] for line in smoke.stdout.splitlines() if line.startswith('SMOKE_OUTPUT=')),None)
if not receipt_path:raise SystemExit('Missing actual packaged UI receipt')
receipt=json.loads((Path(receipt_path)/'ui-smoke.json').read_text())
if receipt.get('result')!='PASS' or receipt.get('version')!=VERSION:raise SystemExit('UI acceptance failed')
for p in Path(receipt_path).iterdir():
    if p.suffix in ['.json','.png']:shutil.copy2(p,OUT/p.name)
dest=OUT/f'LaoyuCleaner-macOS-{ARCH}.zip';run(['/usr/bin/ditto','-c','-k','--sequesterRsrc','--keepParent',app,dest])
report={'version':VERSION,'arch':ARCH,'runnerOS':platform.platform(),'runnerMachine':platform.machine(),'appArchitecture':architecture,'windowsPayloadSha256':WIN_HASH,'electronSha256':sha(electron_zip),'asarSha256':sha(ROOT/'app.asar'),'name':dest.name,'sha256':sha(dest),'sizeBytes':dest.stat().st_size,'ui':'PASS','recycleRestore':'PASS','signing':'ad-hoc; not Developer ID notarized'}
(OUT/'macos-receipt.json').write_text(json.dumps(report,indent=2));(OUT/f'SHA256SUMS-macOS-{ARCH}.txt').write_text(f'{report["sha256"]}  {dest.name}\n')
print(json.dumps(report))
