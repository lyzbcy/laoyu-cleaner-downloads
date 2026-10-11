'use strict';
const {app,shell}=require('electron');const fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const [asar,report]=process.argv.slice(2);const {Engine}=require(path.join(asar,'src/engine.cjs'));const {rules}=require(path.join(asar,'src/policy.cjs'));
const execute=require('node:util').promisify(require('node:child_process').execFile);
const processes=async()=>{const {stdout}=await execute('/bin/ps',['-axo','comm='],{timeout:5000});return stdout.split('\n').map(n=>path.basename(n.trim())).filter(Boolean);};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
app.whenReady().then(async()=>{
 assert.equal(process.platform,'darwin');const home=await fs.mkdtemp(path.join(os.tmpdir(),'laoyu-mac-acceptance-'));const time=Date.now()+10*86400000;
 const cache=rules(home,'darwin').find(r=>r.id==='chrome').root;await fs.mkdir(cache,{recursive:true});const filename='laoyu-recycle-'+crypto.randomUUID()+'.tmp',file=path.join(cache,filename),content=Buffer.from('isolated real macOS recycle/restore fixture');await fs.writeFile(file,content);
 const doc=path.join(home,'Documents','personal.txt');await fs.mkdir(path.dirname(doc));await fs.writeFile(doc,'KEEP');
 const engine=new Engine({home,platform:'darwin',processes,now:()=>time,trash:f=>shell.trashItem(f)});const scan=await engine.scan();assert.equal(scan.cards.filter(c=>c.tier==='basic').length,0);assert.equal(scan.cards.find(c=>c.id==='chrome').eligibleCount,1);assert.equal(await fs.readFile(doc,'utf8'),'KEEP');assert.throws(()=>engine.preview(scan.id,['documents']));
 const result=await engine.clean(scan.id,['chrome']);assert.equal(result.moved,1);assert.equal(result.failed,0);await assert.rejects(fs.access(file));assert.equal(await fs.readFile(doc,'utf8'),'KEEP');
 // Only the exact unique file created above is addressed; no enumeration or trash emptying.
 const trashed=path.join(os.homedir(),'.Trash',filename);const s=await fs.lstat(trashed);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(hash(await fs.readFile(trashed)),hash(content));await fs.rename(trashed,file);assert.equal(hash(await fs.readFile(file)),hash(content));
 const npm=rules(home,'darwin').find(r=>r.id==='npm').root;await fs.mkdir(npm,{recursive:true});const blockedFile=path.join(npm,'blocked-'+crypto.randomUUID()+'.tmp');await fs.writeFile(blockedFile,'KEEP');
 const child=require('node:child_process').spawn('node',['-e','setTimeout(()=>{},30000)'],{stdio:'ignore'});
 try{await new Promise(r=>setTimeout(r,300));const again=await engine.scan();const blocked=await engine.clean(again.id,['npm']);assert.equal(blocked.moved,0);assert(blocked.reasons['app-running']>=1);assert.equal(await fs.readFile(blockedFile,'utf8'),'KEEP');}finally{child.kill();}
 await fs.writeFile(report,JSON.stringify({result:'PASS',platform:process.platform,arch:process.arch,home,createdOnlyFixture:true,moved:result.moved,restored:true,hash:hash(content),personalPreserved:true,processGuard:'actual ps + owned Node child'},null,2));console.log('MAC_RECYCLE=PASS; RESTORE=PASS; SHA256=MATCH; PERSONAL=KEEP; PROCESS_GUARD=PASS');app.exit(0);
}).catch(async e=>{await fs.writeFile(report,JSON.stringify({result:'FAIL',error:String(e.stack)},null,2));console.error(e);app.exit(1);});
