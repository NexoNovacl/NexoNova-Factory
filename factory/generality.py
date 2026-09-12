"""Read-only cross-product evidence; literal leakage checks are not secret detection."""
import json,re
from .generation import byte_hash

def audit_generalization(files, template, own_config, other_config, private_paths):
    """Check actual generated source bytes, with narrow, reported template exceptions."""
    issues=[];exceptions=[]
    other_text=[*other_config['hero'].values(),*other_config['about'].values(),
        *[p['price'] for p in other_config['plans']],
        *[s['description'] for s in other_config['services']],
        *[v for q in other_config['faq'] for v in q.values()]]
    for rel,data in files.items():
        text=data.decode('utf8');lower=text.lower()
        if any(p in text for p in private_paths) or 'nexonova-prototype' in lower or 'nexonova-website' in lower:
            issues.append({'path':rel,'kind':'private-or-other-product-reference'})
        # Schema namespace is factory provenance, not the client brand.
        cleaned=text
        if rel=='.nexonova/project.json':
            for token in ('nexonova.project.v1','nexonova.baseline.v1','nexonova.corporate-site.v0.1.0'):
                cleaned=cleaned.replace(token,'')
        if re.search(r'nexonova',cleaned,re.I):issues.append({'path':rel,'kind':'other-brand'})
        if any(value and value.casefold() in lower for value in other_text):issues.append({'path':rel,'kind':'other-editorial-or-price'})
        colors=[c for k,c in other_config['brand'].items() if k!='name' and c.lower() in lower]
        if colors:
            if rel.endswith('.css') and template.get(rel)==data:
                exceptions.append({'path':rel,'kind':'unchanged-shared-template-css','colors':colors,'sha256':byte_hash(data)})
            else:issues.append({'path':rel,'kind':'other-brand-token'})
    if json.loads(files['src/content/site.json'])!=own_config:issues.append({'path':'src/content/site.json','kind':'wrong-public-config'})
    return {'status':'complete' if not issues else 'fail','issues':issues,'legitimate_shared_exceptions':exceptions,
            'scope':'Generated source only. Public configuration exact; factory schema namespaces legitimate; shared CSS exceptions require exact template bytes. Runtime checks recorded separately.'}

def compare_products(first,second):
    result=[]
    for path in sorted(set(first)|set(second)):
        equal=first.get(path)==second.get(path)
        category=('metadata' if path=='.nexonova/project.json' else 'configuration' if path in {'src/content/site.json','package.json','package-lock.json'} else 'shared-template')
        result.append({'path':path,'category':category,'identical':equal,'first':byte_hash(first[path]) if path in first else None,'second':byte_hash(second[path]) if path in second else None})
    return result
