"""Check the frozen conversion identities without starting model inference."""
import hashlib
import json
from pathlib import Path
import sys


def require_doctor_ready(doctor):
    failed = {name: item.get('reason', item.get('status'))
              for name, item in doctor.get('capabilities', {}).items()
              if item.get('status') != 'PASS'}
    if doctor.get('readiness') != 'READY_FULL' or failed:
        raise RuntimeError('Full GPU/model validation did not pass; incomplete conversion capabilities: ' + json.dumps(failed))


def verify():
    from bemarkdown.stage_forecasts import (
        FORECAST_PATH, dependency_identity, validate_source_bindings)
    from bemarkdown.pdf.qwen_stage import qwen_python
    manifest = json.loads(FORECAST_PATH.read_text(encoding='utf-8'))
    validate_source_bindings(manifest['source_bindings'])
    identities = {}
    for name, executable, paths in (
        ('paddle', Path(sys.executable), sys.path),
        ('qwen', Path(qwen_python()), [Path(qwen_python()).parent.parent / 'Lib/site-packages']),
    ):
        profile = manifest['dependency_profiles'][name]
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        if digest not in profile['executable_sha256']:
            raise RuntimeError('Frozen interpreter identity mismatch: ' + name)
        dependency_identity([p for p in paths if p], profile['distributions'])
        identities[name] = {'status': 'PASS', 'executable_sha256': digest,
                            'packages': sorted(profile['distributions'])}
    return {'status': 'PASS', 'profiles': identities, 'model_inference_started': False}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
