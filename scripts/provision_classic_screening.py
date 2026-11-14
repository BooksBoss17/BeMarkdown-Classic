"""Install the complete frozen screening stack in isolated versioned environments."""
import argparse,json,os,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import install_semantic_retention as installer
ROOT=Path(__file__).resolve().parents[1]
def run(args):subprocess.run(list(map(str,args)),check=True)
def main():
    p=argparse.ArgumentParser();p.add_argument('--accept-external-licenses',action='store_true');p.add_argument('--model-cache',type=Path)
    a=p.parse_args()
    if not a.accept_external_licenses:p.error('Read docs/LICENSE_AUDIT.md and accept the external licenses first.')
    import shutil
    uv=shutil.which('uv')
    if not uv:raise RuntimeError('Install uv from https://docs.astral.sh/uv/getting-started/installation/ before provisioning the complete tool.')
    lock=installer.read(ROOT/'TOOLS/semantic_retention/PUBLIC_RUNTIME_LOCK.json')
    home=Path(os.environ['LOCALAPPDATA'])/'BeMarkdownClassic/runtimes'
    paths={}
    for role,key in [('inference','inference_versions'),('source','source_versions')]:
        version=lock['python_versions'][role]
        target=home/('screening-'+role+'-'+version);python=target/'Scripts/python.exe'
        if not python.exists():
            if target.exists():raise RuntimeError('Partial runtime exists; inspect before retry: '+str(target))
            run([uv,'venv','--python',version,'--seed',target])
        # A successful matching environment is reused; an unverified partial one is repaired using exact pins.
        try:current=installer.query(python,lock[key])
        except subprocess.CalledProcessError:current={}
        if current.get('version')!=version or current.get('versions')!=lock[key]:
            pins=dict(lock[key])
            if 'torch' in pins:run([python,'-m','pip','install','torch=='+pins.pop('torch'),'--index-url','https://download.pytorch.org/whl/cu130'])
            run([python,'-m','pip','install',*[k+'=='+v for k,v in pins.items()]])
        paths[role]=python
    cache=Path(os.environ['LOCALAPPDATA'])/'BeMarkdownClassic/downloads'
    models=installer.install_models(cache,a.model_cache,False)
    runtime=installer.register_runtime(paths['inference'],paths['source'],None,cache,True)
    installer.write(ROOT/'.local/classic-complete.json',{'status':'COMPLETE_STACK_INSTALLED','models':models,'runtime':runtime,'content_quality_certified':False})
    print(json.dumps(runtime,ensure_ascii=False))
if __name__=='__main__':main()
