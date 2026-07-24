#!/usr/bin/env python3
# Génère un aperçu portable (CSS intégré, liens relatifs) à partir des templates Eleventy.
import json, re, os, pathlib, shutil
from jinja2 import Environment, FileSystemLoader

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
INC = SRC / "_includes"
DATA = SRC / "_data"
OUT = ROOT / "preview"
OUT.mkdir(exist_ok=True)

# Données globales (clé = nom de fichier)
globals_data = {}
for f in DATA.glob("*.json"):
    globals_data[f.stem] = json.loads(f.read_text(encoding="utf-8"))

env = Environment(loader=FileSystemLoader([str(INC), str(SRC)]), autoescape=True)
env.filters["dump"] = lambda v: json.dumps(v, ensure_ascii=False)

def split_front_matter(text):
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        import yaml
        return yaml.safe_load(fm) or {}, body
    return {}, text

routes = {
    "/": "index.html", "/concept/": "concept.html", "/seances/": "seances.html",
    "/coachs/": "coachs.html", "/tarifs/": "tarifs.html", "/studios/": "studios.html",
    "/franchises/": "franchises.html", "/faq/": "faq.html",
}

css = (SRC / "assets/css/style.css").read_text(encoding="utf-8")

def portablize(html):
    # CSS en ligne
    html = html.replace(
        '<link rel="stylesheet" href="/assets/css/style.css">',
        "<style>\n" + css + "\n</style>",
    )
    # Liens absolus -> fichiers relatifs (href et tokens JSON)
    for path, fname in routes.items():
        if path == "/":
            continue
        html = html.replace('"%s"' % path, '"%s"' % fname).replace("'%s'" % path, "'%s'" % fname)
    html = html.replace('href="/"', 'href="index.html"')
    # chemins d'assets absolus -> relatifs pour l'aperçu portable
    html = html.replace('="/assets/', '="assets/')
    return html

pages = [p for p in SRC.glob("*.njk")]
base = env.get_template("base.njk")
count = 0
for p in pages:
    fm, body = split_front_matter(p.read_text(encoding="utf-8"))
    permalink = fm.get("permalink", "/" + p.stem + "/")
    ctx = dict(globals_data)
    ctx.update({k: v for k, v in fm.items()})
    ctx["page"] = {"url": permalink}
    content = env.from_string(body).render(**ctx)
    full = base.render(content=content, **ctx)
    out_name = routes.get(permalink, p.stem + ".html")
    (OUT / out_name).write_text(portablize(full), encoding="utf-8")
    count += 1
    print("  ✓", out_name)

# Copie des assets (images, etc.) pour l'aperçu portable
assets_src = SRC / "assets"
assets_dst = OUT / "assets"
if assets_dst.exists():
    shutil.rmtree(assets_dst)
shutil.copytree(assets_src, assets_dst)
print("Assets copiés dans", assets_dst)

print("Aperçu généré :", count, "pages dans", OUT)
