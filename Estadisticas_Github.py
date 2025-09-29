# Software para sacar una lista de datos de una cuenta github 
# Con esos datos generar una imagen svg que se puede mostrar en 
# El readme.md de una cuenta de github
# pip install requests


import requests
import math
import random
from datetime import datetime
from collections import defaultdict

# ========== CONFIGURA TU TOKEN Y USUARIO ==========

GITHUB_TOKEN = "TOKEN"
USERNAME = "Usuario_Github"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

API_URL = "https://api.github.com"

COLORS = [
    "#f1e05a", "#3572A5", "#4F5D95", "#563d7c", "#701516", "#e34c26", "#2b7489",
    "#f34b7d", "#cc0000", "#00ADD8", "#b07219", "#555555", "#f0db4f", "#89e051",
    "#1e4aec", "#c6538c", "#29bcb1", "#b83998", "#e44b23", "#ff9900"
]

# ========== FUNCIONES DE GITHUB API ==========

def get_user():
    return requests.get(f"{API_URL}/users/{USERNAME}", headers=HEADERS).json()

def get_repos():
    repos = []
    page = 1
    while True:
        res = requests.get(f"{API_URL}/users/{USERNAME}/repos?per_page=100&page={page}", headers=HEADERS)
        if res.status_code != 200:
            break
        data = res.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_languages_percentages(repos):
    language_count = defaultdict(int)
    total = 0
    for repo in repos:
        if repo["fork"]:
            continue
        langs = requests.get(repo["languages_url"], headers=HEADERS).json()
        for lang, count in langs.items():
            language_count[lang] += count
            total += count
    return {
        lang: round((count / total) * 100, 2)
        for lang, count in sorted(language_count.items(), key=lambda x: x[1], reverse=True)
    }

def get_commit_count_current_year(repos):
    year = datetime.now().year
    total_commits = 0
    for repo in repos:
        if repo["fork"]:
            continue
        commits_url = f"{API_URL}/repos/{USERNAME}/{repo['name']}/commits"
        params = {
            "author": USERNAME,
            "since": f"{year}-01-01T00:00:00Z"
        }
        res = requests.get(commits_url, headers=HEADERS, params=params)
        if res.status_code == 200:
            total_commits += len(res.json())
    return total_commits

# ========== FUNCIONES SVG ==========

def draw_pie_chart(data, cx, cy, r):
    svg = []
    legend = []
    total_angle = 0
    colors = list(COLORS)
    random.shuffle(colors)

    for i, (lang, pct) in enumerate(data.items()):
        angle = pct * 3.6
        large_arc = 1 if angle > 180 else 0

        start_x = cx + r * math.cos(math.radians(total_angle))
        start_y = cy + r * math.sin(math.radians(total_angle))
        total_angle += angle
        end_x = cx + r * math.cos(math.radians(total_angle))
        end_y = cy + r * math.sin(math.radians(total_angle))
        color = colors[i % len(colors)]

        path = f'<path d="M{cx},{cy} L{start_x},{start_y} A{r},{r} 0 {large_arc},1 {end_x},{end_y} Z" fill="{color}" />'
        svg.append(path)
        legend.append((lang, pct, color))
    return "\n".join(svg), legend

def generate_svg(data):
    now = datetime.now().strftime("%d %b %Y")

    pie_svg, legend = draw_pie_chart(data["languages"], 600, 150, 80)

    legend_svg = ""
    for i, (lang, pct, color) in enumerate(legend):
        y = 320 + i * 20
        legend_svg += f'<circle cx="30" cy="{y}" r="5" fill="{color}" />'
        legend_svg += f'<text x="45" y="{y + 5}" class="value">{lang} ({pct}%)</text>\n'

    height = 400 + len(legend) * 22

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}">
    <style>
        .title {{ font: bold 24px sans-serif; fill: #24292e; }}
        .label {{ font: 14px sans-serif; fill: #57606a; }}
        .value {{ font: bold 14px sans-serif; fill: #0366d6; }}
        .small {{ font: 12px sans-serif; fill: #57606a; }}
    </style>

    <text x="30" y="40" class="title">📊 GitHub Stats — @{USERNAME}</text>

    <text x="30" y="80" class="label">📅 Última actualización:</text>
    <text x="260" y="80" class="value">{now}</text>

    <text x="30" y="110" class="label">📌 Repositorio destacado:</text>
    <text x="260" y="110" class="value">{data['featured_repo']}</text>

    <text x="30" y="140" class="label">📈 Contribuciones (último año):</text>
    <text x="260" y="140" class="value">{data['contributions']}</text>

    <text x="30" y="170" class="label">📧 Correo público:</text>
    <text x="260" y="170" class="value">{data['email']}</text>

    <text x="30" y="200" class="label">📁 Repositorios públicos:</text>
    <text x="260" y="200" class="value">{data['public_repos']}</text>

    <text x="30" y="230" class="label">⭐ Total de estrellas:</text>
    <text x="260" y="230" class="value">{data['stars']}</text>

    <text x="30" y="260" class="label">👥 Seguidores / Siguiendo:</text>
    <text x="260" y="260" class="value">{data['followers']} / {data['following']}</text>

    <text x="30" y="290" class="label">📝 Commits en {datetime.now().year}:</text>
    <text x="260" y="290" class="value">{data['commits']}</text>

    <!-- Pie chart -->
    <g>{pie_svg}</g>

    <!-- Lengenda de lenguajes -->
    {legend_svg}

    <text x="30" y="{height - 20}" class="small">Generado automáticamente con la API de GitHub</text>
</svg>'''

    with open("Estadisticas_Github.svg", "w", encoding="utf-8") as f:
        f.write(svg)

    print("✅ SVG generado: Estadisticas_Github.svg")

# ========== MAIN ==========

def main():
    user = get_user()
    repos = get_repos()
    if not repos:
        print("❌ No se encontraron repos o hubo un error.")
        return

    data = {
        "email": user.get("email", "No público"),
        "public_repos": user.get("public_repos", 0),
        "followers": user.get("followers", 0),
        "following": user.get("following", 0),
        "languages": get_languages_percentages(repos),
        "stars": sum(repo["stargazers_count"] for repo in repos),
        "featured_repo": max(repos, key=lambda r: r["stargazers_count"])["full_name"] if repos else "N/A",
        "contributions": "Ver en el perfil (no disponible por API REST)",
        "commits": get_commit_count_current_year(repos),
    }

    generate_svg(data)

if __name__ == "__main__":
    main()

