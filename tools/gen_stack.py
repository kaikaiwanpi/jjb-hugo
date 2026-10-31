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
BOOKRE = re.compile(r'^《(.+?)》(.*?)作者[：:]\s*(.+?)\s*(?:百度云|txt|TXT|$)')
SIZERE = re.compile(r'【TXT大小】[：:]\s*([0-9.]+\s*[MKG]B)', re.I)


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

    m = BOOKRE.match(title)
    if m:
        book, edition, author = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        short_title = '《%s》%s' % (book, edition)
    else:
        book, author, short_title = title, '', title
    size_m = SIZERE.search(desc or '')
    size = size_m.group(1) if size_m else ''
    intro = re.sub(r'^【TXT大小】[^【]*', '', desc or '')
    intro = re.sub(r'^【内容简介】[：:]\s*', '', intro).strip()
    subtitle = ' · '.join(x for x in ['作者：' + author if author else '', size, intro[:38]] if x)

    d = os.path.join(OUT, pid)
    os.makedirs(d, exist_ok=True)
    image_line = ''
    if cover:
        src = os.path.join(MEDIA, cover[len('/media/'):].replace('/', os.sep))
        if os.path.exists(src):
            ext = os.path.splitext(src)[1].lower()
            shutil.copy2(src, os.path.join(d, 'cover' + ext))
            image_line = 'image: cover%s' % ext

    # 正文：去掉正文里的封面图（卡片和详情页已有封面），下载按钮放在最前面
    body_html = re.sub(r'<img[^>]*>', '', body)
    body_html = re.sub(r'^\s*【TXT大小】[^\n]*\n+', '', body_html)   # 已在标题下的信息行里
    body_html = re.sub(r'\n{3,}', '\n\n', body_html).lstrip()
    cta = ''
    if dl:
        cta = ('<div class="dl-cta"><a class="dl-btn" href="%s" target="_blank" rel="nofollow noopener">'
               '去下载 TXT</a></div>\n\n' % dl)

    fm_lines = ['---',
                'title: "%s"' % short_title.replace('"', '\\"'),
                'fullTitle: "%s"' % title.replace('"', '\\"'),
                'book: "%s"' % book.replace('"', '\\"'),
                'author: "%s"' % author.replace('"', '\\"'),
                'date: %s' % date,
                'url: "/%s.html"' % pid,
                'slug: "%s"' % pid,
                'description: "%s"' % subtitle.replace('"', '\\"'),
                'categories: [' + ', '.join('"%s"' % c for c in cats) + ']',
                'tags: [' + ', '.join('"%s"' % t for t in tags) + ']',
                'views: %s' % (views or 0),
                'download: "%s"' % dl]
    if image_line:
        fm_lines.append(image_line)
    fm_lines += ['---', '']

    io.open(os.path.join(d, 'index.md'), 'w', encoding='utf-8').write(
        '\n'.join(fm_lines) + cta + body_html)
    made += 1

print('生成 %d 篇 page bundle -> %s' % (made, OUT))
print('封面文件: %d' % sum(1 for b, _, fs in os.walk(OUT) for x in fs if x.startswith('cover')))
