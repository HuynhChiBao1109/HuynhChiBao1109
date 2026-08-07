import json
import os
import urllib.request
import urllib.parse
from collections import defaultdict

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ.get("GITHUB_TOKEN")

API = "https://api.github.com"

headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

if TOKEN:
    headers["Authorization"] = f"Bearer {TOKEN}"


def github_get(url):
    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())


def get_repositories():
    repositories = []
    page = 1

    while True:
        url = (
            f"{API}/users/{urllib.parse.quote(USERNAME)}"
            f"/repos?per_page=100&page={page}&type=owner"
        )

        data = github_get(url)

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


def get_languages(repo):
    owner = repo["owner"]["login"]
    name = repo["name"]

    url = f"{API}/repos/{owner}/{name}/languages"

    try:
        return github_get(url)
    except Exception as error:
        print(f"Failed: {owner}/{name}: {error}")
        return {}


def escape_svg(value):
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


repositories = get_repositories()

print(f"Found {len(repositories)} repositories")

languages = defaultdict(int)

for repo in repositories:
    if repo.get("fork"):
        continue

    print(f"Scanning: {repo['full_name']}")

    repo_languages = get_languages(repo)

    for language, bytes_count in repo_languages.items():
        languages[language] += bytes_count


if not languages:
    raise RuntimeError("No language data found")


total_bytes = sum(languages.values())

language_data = sorted(
    [
        {
            "name": language,
            "bytes": bytes_count,
            "percentage": bytes_count / total_bytes * 100,
        }
        for language, bytes_count in languages.items()
    ],
    key=lambda item: item["bytes"],
    reverse=True,
)


# ---------------------------------------------------------
# SVG
# ---------------------------------------------------------

WIDTH = 900
ROW_HEIGHT = 52
HEADER_HEIGHT = 90
PADDING = 40

HEIGHT = HEADER_HEIGHT + len(language_data) * ROW_HEIGHT + PADDING

SVG = f'''<svg
  width="{WIDTH}"
  height="{HEIGHT}"
  viewBox="0 0 {WIDTH} {HEIGHT}"
  xmlns="http://www.w3.org/2000/svg"
>
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0d1117"/>
      <stop offset="100%" stop-color="#161b22"/>
    </linearGradient>

    <linearGradient id="bar" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#a855f7"/>
      <stop offset="50%" stop-color="#ec4899"/>
      <stop offset="100%" stop-color="#6366f1"/>
    </linearGradient>

    <filter id="shadow">
      <feDropShadow
        dx="0"
        dy="3"
        stdDeviation="4"
        flood-opacity="0.35"
      />
    </filter>
  </defs>

  <rect
    width="{WIDTH}"
    height="{HEIGHT}"
    rx="20"
    fill="url(#bg)"
  />

  <text
    x="{PADDING}"
    y="48"
    fill="#ffffff"
    font-size="26"
    font-family="Arial, Helvetica, sans-serif"
    font-weight="700"
  >
    💻 Languages &amp; Technologies
  </text>

  <text
    x="{PADDING}"
    y="72"
    fill="#8b949e"
    font-size="13"
    font-family="Arial, Helvetica, sans-serif"
  >
    Based on code across {len(repositories)} repositories
  </text>
'''

BAR_X = 190
BAR_WIDTH = 520
PERCENT_X = 750

colors = [
    "#f7df1e",
    "#3178c6",
    "#e34c26",
    "#563d7c",
    "#41b883",
    "#00add8",
    "#178600",
    "#dea584",
    "#89e051",
    "#3572A5",
    "#701516",
    "#012456",
]

for index, language in enumerate(language_data):
    y = HEADER_HEIGHT + index * ROW_HEIGHT

    name = escape_svg(language["name"])
    percentage = language["percentage"]

    bar_width = max((percentage / 100) * BAR_WIDTH, 4)

    language_color = colors[index % len(colors)]

    SVG += f'''
    <text
      x="40"
      y="{y + 27}"
      fill="#f0f6fc"
      font-size="15"
      font-family="Arial, Helvetica, sans-serif"
      font-weight="600"
    >
      {name}
    </text>

    <rect
      x="{BAR_X}"
      y="{y + 10}"
      width="{BAR_WIDTH}"
      height="18"
      rx="9"
      fill="#21262d"
    />

    <rect
      x="{BAR_X}"
      y="{y + 10}"
      width="{bar_width:.2f}"
      height="18"
      rx="9"
      fill="url(#bar)"
    />

    <circle
      cx="{BAR_X + bar_width:.2f}"
      cy="{y + 19}"
      r="5"
      fill="{language_color}"
      filter="url(#shadow)"
    />

    <text
      x="{PERCENT_X}"
      y="{y + 27}"
      fill="#ffffff"
      font-size="15"
      font-family="Arial, Helvetica, sans-serif"
      font-weight="700"
    >
      {percentage:.2f}%
    </text>
    '''

SVG += """
</svg>
"""

os.makedirs("assets", exist_ok=True)

with open("assets/languages.svg", "w", encoding="utf-8") as file:
    file.write(SVG)

print("Generated assets/languages.svg")
