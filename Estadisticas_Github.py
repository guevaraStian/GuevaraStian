# Software para sacar una lista de datos de una cuenta github 
# Con esos datos generar una imagen svg que se puede mostrar en 
# El readme.md de una cuenta de github
# pip install requests

import requests
import math
from collections import defaultdict
from datetime import datetime

# ========== CONFIGURA TU TOKEN Y USUARIO ==========
TOKEN = "TOKEN_GITHUB"
USER = "Usuario_Github"


HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

API_BASE = "https://api.github.com"

COLORS = [
    "#f1e05a", "#3572A5", "#4F5D95",
    "#563d7c", "#701516", "#e34c26",
    "#2b7489"
]

# --- Funciones API ---

def get_user():
    res = requests.get(f"{API_BASE}/users/{USER}", headers=HEADERS)
    res.raise_for_status()
    return res.json()

def get_repos():
    repos = []
    page = 1
    while True:
        res = requests.get(f"{API_BASE}/users/{USER}/repos", headers=HEADERS, params={"per_page": 100, "page": page})
        res.raise_for_status()
        data = res.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_languages_percentages(repos, top_n=7):
    lang_bytes = defaultdict(int)
    total_bytes = 0
    for repo in repos:
        if repo["fork"]:
            continue
        langs = requests.get(repo["languages_url"], headers=HEADERS).json()
        for lang, size in langs.items():
            lang_bytes[lang] += size
            total_bytes += size
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:top_n]
    total_top = sum([size for _, size in sorted_langs])
    return {lang: round((size / total_top) * 100, 2) for lang, size in sorted_langs}

def get_commit_count_year(repos):
    year = datetime.now().year
    total_commits = 0
    for repo in repos:
        if repo["fork"]:
            continue
        url = f"{API_BASE}/repos/{USER}/{repo['name']}/commits"
        params = {"author": USER, "since": f"{year}-01-01T00:00:00Z"}
        res = requests.get(url, headers=HEADERS, params=params)
        if res.status_code == 200:
            total_commits += len(res.json())
    return total_commits

# --- SVG Helpers ---

def draw_pie_chart(data, cx, cy, r):
    paths = []
    angle_start = 0
    legend = []
    for i, (lang, pct) in enumerate(data.items()):
        angle = pct * 3.6
        angle_end = angle_start + angle

        large_arc_flag = 1 if angle > 180 else 0
        start_x = cx + r * math.cos(math.radians(angle_start))
        start_y = cy + r * math.sin(math.radians(angle_start))
        end_x = cx + r * math.cos(math.radians(angle_end))
        end_y = cy + r * math.sin(math.radians(angle_end))

        color = COLORS[i % len(COLORS)]

        path = f'<path d="M{cx},{cy} L{start_x},{start_y} A{r},{r} 0 {large_arc_flag},1 {end_x},{end_y} Z" fill="{color}" />'
        paths.append(path)

        legend.append((lang, pct, color))

        angle_start = angle_end
    return "\n".join(paths), legend

def generate_svg(data):
    now_str = datetime.now().strftime("%d %b %Y")
    pie_svg, legend = draw_pie_chart(data["languages"], 200, 180, 120)

    legend_svg = ""
    for i, (lang, pct, color) in enumerate(legend):
        y = 70 + i * 30
        # Punto color
        legend_svg += f'<circle cx="420" cy="{y}" r="7" fill="{color}" />'
        # Texto lenguaje + %
        legend_svg += f'<text x="440" y="{y+5}" class="legend-text">{lang} ({pct}%)</text>\n'

    height_svg = max(420, 70 + len(legend) * 30 + 20)

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height_svg}">
    <style>
        .title {{ font: bold 26px sans-serif; fill: #24292e; }}
        .label {{ font: 16px sans-serif; fill: #57606a; }}
        .value {{ font: bold 16px sans-serif; fill: #0366d6; }}
        .legend-text {{ font: 15px sans-serif; fill: #24292e; }}
        .footer {{ font: 12px sans-serif; fill: #999999; }}
    </style>

    <!-- Título -->
    <text x="30" y="40" class="title">📊 Estadísticas GitHub - @{USER}</text>

    <!-- Pie chart -->
    <g>{pie_svg}</g>

    <!-- Leyenda -->
    <g>{legend_svg}</g>

    <!-- Datos clave -->
    <text x="30" y="320" class="label">📅 Última actualización:</text>
    <text x="260" y="320" class="value">{now_str}</text>

    <text x="30" y="350" class="label">📌 Repositorio destacado:</text>
    <text x="260" y="350" class="value">{data['featured_repo']}</text>

    <text x="30" y="380" class="label">📈 Contribuciones (último año):</text>
    <text x="260" y="380" class="value">{data['contributions']}</text>

    <text x="30" y="410" class="label">📧 Correo público:</text>
    <text x="260" y="410" class="value">{data['email']}</text>

    <text x="30" y="440" class="label">📁 Repositorios públicos:</text>
    <text x="260" y="440" class="value">{data['public_repos']}</text>

    <text x="30" y="470" class="label">⭐ Total estrellas:</text>
    <text x="260" y="470" class="value">{data['stars']}</text>

    <text x="30" y="500" class="label">👥 Seguidores / Siguiendo:</text>
    <text x="260" y="500" class="value">{data['followers']} / {data['following']}</text>

    <text x="30" y="530" class="label">📝 Commits en {datetime.now().year}:</text>
    <text x="260" y="530" class="value">{data['commits']}</text>

    <text x="30" y="{height_svg - 10}" class="footer">Generado automáticamente con la API de GitHub</text>
</svg>'''

    with open("Estadisticas_Github.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

    print("✅ Archivo SVG creado: Estadisticas_Github.svg")

# --- MAIN ---
def main():
    user = get_user()
    repos = get_repos()
    if not repos:
        print("❌ No se encontraron repositorios")
        return

    data = {
        "email": user.get("email") or "No público",
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "languages": get_languages_percentages(repos, 7),
        "stars": sum(repo["stargazers_count"] for repo in repos),
        "featured_repo": max(repos, key=lambda r: r["stargazers_count"])["full_name"] if repos else "N/A",
        "contributions": "Ver perfil (API REST no provee exacto)",
        "commits": get_commit_count_year(repos),
    }

    generate_svg(data)

if __name__ == "__main__":
    main()
