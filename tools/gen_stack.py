"""把精校吧的 md 灌进 Stack 主题：取最近 N 篇，做 page bundle（含封面）。

来源：~/sites/jingjiaoba-static/content/books/*.md（已含 seo_title/description/cover/download/views）
产物：content/books/{id}/index.md + cover.<ext>
"""
import io, os, re, shutil, sys

SRC = os.path.expanduser('~/sites/jingjiaoba-static/content/books')
MEDIA = os.path.expanduser('~/jjb-assets/media')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'content', 'books')
N = int(sys.argv[1]) if len(sys.argv) > 1 else 300

SITE = '精校吧 - 免费精校小说-校对全本TXT小说下载网'


def fm_get(fm, key):
    m = re.search(r'^%s:\s*(.+)$' % key, fm, re.M)
    return m.group(1).strip().strip('"') if m else ''


def fm_list(fm, key):
    m = re.search(r'^%s:\s*\[(.*?)\]' % key, fm, re.M)
    if not m:
        return []
    return [x.strip().strip('"') for x in m.group(1).split(',') if x.strip()]


files = sorted((f for f in os.listdir(SRC) if f.endswith('.md') and f[:-3].isdigit()),
               key=lambda f: -int(f[:-3]))[:N]

shutil.rmtree(OUT, ignore_errors=True)
made = 0
for f in files:
    pid = f[:-3]
    txt = io.open(os.path.join(SRC, f), encoding='utf-8').read()
    parts = txt.split('---', 2)
    fm, body = parts[1], parts[2].strip()
    title = fm_get(fm, 'title')
    date = fm_get(fm, 'date')
    cover = fm_get(fm, 'cover')
    desc = fm_get(fm, 'description')
    dl = fm_get(fm, 'download')
    views = fm_get(fm, 'views')
    cats = fm_list(fm, 'categories')
    tags = [x.split('name:')[-1].strip().strip('"').strip('}')
            for x in re.findall(r'\{name: "([^"]+)"', fm)]

    d = os.path.join(OUT, pid)
    os.makedirs(d, exist_ok=True)
    image_line = ''
    if cover:
        src = os.path.join(MEDIA, cover[len('/media/'):].replace('/', os.sep))
        if os.path.exists(src):
            ext = os.path.splitext(src)[1].lower()
            shutil.copy2(src, os.path.join(d, 'cover' + ext))
            image_line = 'image: cover%s' % ext

    # 正文：简介 + 下载按钮（Stack 正文区）
    body_html = body
    cta = ''
    if dl:
        cta = ('\n\n<div class="dl-cta"><a class="dl-btn" href="%s" target="_blank" rel="nofollow noopener">'
               '去下载 TXT</a></div>\n' % dl)

    fm_lines = ['---',
                'title: "%s"' % title.replace('"', '\\"'),
                'date: %s' % date,
                'url: "/%s.html"' % pid,
                'slug: "%s"' % pid,
                'description: "%s"' % (desc or title).replace('"', '\\"'),
                'categories: [' + ', '.join('"%s"' % c for c in cats) + ']',
                'tags: [' + ', '.join('"%s"' % t for t in tags) + ']',
                'views: %s' % (views or 0),
                'download: "%s"' % dl]
    if image_line:
        fm_lines.append(image_line)
    fm_lines += ['---', '']

    io.open(os.path.join(d, 'index.md'), 'w', encoding='utf-8').write(
        '\n'.join(fm_lines) + body_html + cta)
    made += 1

print('生成 %d 篇 page bundle -> %s' % (made, OUT))
print('封面文件: %d' % sum(1 for b, _, fs in os.walk(OUT) for x in fs if x.startswith('cover')))
