#!/usr/bin/env python3
"""Release the Kalil web app (html only) for both channels: Amir/brothers (root) and Dorin (dorin/).
usage: python3 tools/release.py "release notes in Hebrew"   (run from repo root)
Steps: bump APPV in src/index.html -> build index.html (+local fonts) and dorin/index.html -> node syntax check
-> commit -> write version.json + dorin/version.json pointing at that commit -> commit -> push."""
import re,sys,subprocess,json,os,tempfile
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));os.chdir(R)
notes=sys.argv[1] if len(sys.argv)>1 else 'עדכון'
def sh(*a):return subprocess.run(a,check=True,capture_output=True,text=True).stdout.strip()
src=open('src/index.html').read();m=re.search(r'const APPV=(\d+);',src);v=int(m.group(1))+1
src=src.replace(m.group(0),f'const APPV={v};',1);open('src/index.html','w').write(src)
FF=''.join(f"@font-face{{font-family:'{fam}';src:url(fonts/{f}-normal.woff2) format('woff2');font-weight:{w};font-display:swap}}" for fam,f,w in [('Rubik','rubik-hebrew-400','400 500'),('Rubik','rubik-latin-400','400 500'),('Rubik','rubik-hebrew-700','600 800'),('Rubik','rubik-latin-700','600 800'),('Secular One','secular-one-hebrew-400','400'),('Secular One','secular-one-latin-400','400')])
def fonts(s):
    s2=re.sub(r'<link rel="preconnect"[^>]*>\n<link href="https://fonts.googleapis.com[^>]*>','',s);assert s2!=s,'font links not found';return s2.replace('<style>','<style>'+FF,1)
open('index.html','w').write(fonts(src))
tmp=tempfile.mktemp(suffix='.html');subprocess.run([sys.executable,'tools/make_dorin.py','src/index.html',tmp],check=True,capture_output=True)
os.makedirs('dorin',exist_ok=True);open('dorin/index.html','w').write(fonts(open(tmp).read()))
node=next((p for p in ['node','/opt/node22/bin/node'] if subprocess.run(['which',p],capture_output=True).returncode==0 or os.path.exists(p)),None)
for f in ['index.html','dorin/index.html']:
    h=open(f).read();js='\n;\n'.join(x for x in re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>',h,re.S))
    t=tempfile.mktemp(suffix='.js');open(t,'w').write(js)
    if node:subprocess.run([node,'--check',t],check=True)
TR="\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\nClaude-Session: https://claude.ai/code/session_018M67D6NwC3LR71FEWNb9Gv"
sh('git','add','src/index.html','index.html','dorin/index.html');sh('git','commit','-m',f'html {v}: {notes[:60]}'+TR)
sha=sh('git','rev-parse','HEAD')
for vf,path in [('version.json','index.html'),('dorin/version.json','dorin/index.html')]:
    j=json.load(open(vf));j['html']=v;j['notes']=notes;j['url']=f'https://raw.githubusercontent.com/amirevgi32-cell/kalil-app/{sha}/{path}'
    open(vf,'w').write(json.dumps(j,ensure_ascii=False,indent=1)+'\n')
sh('git','add','version.json','dorin/version.json');sh('git','commit','-m',f'Release html {v} (+dorin)'+TR)
if '--no-push' not in sys.argv:subprocess.run(['git','-c','push.negotiate=true','push'],check=True)
print('released html',v,sha)
