from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'site'))
from notes import POSTS, render_markdown

assert len(POSTS) >= 2
assert all(p['slug'] and p['title'] and p['date'] and p['desc'] and p['body'] for p in POSTS)
assert any('<table>' in p['body'] for p in POSTS), 'pipe table should render'
assert '<script>' not in render_markdown('<script>alert(1)</script>')
assert '<code>i = 0;</code>' in render_markdown('`i = 0;`')
assert 'class="inline-equation"' in render_markdown('The output is $V_{out}$.')
assert 'class="equation-block"' in render_markdown('$$\nI = C dV/dt\n$$')
assert '<img src="/assets/plot.png" alt="test plot"' in render_markdown('![test plot](/assets/plot.png)')
assert '<img' not in render_markdown('![bad](javascript:alert(1))')
print('PASS: Markdown notes load, metadata validates, tables render, and raw HTML is escaped')
