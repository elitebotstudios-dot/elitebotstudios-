"""Dependency-free Markdown reader for the public engineering notebook.

Supports front matter, headings, paragraphs, lists, quotes, fenced code,
inline code/links/emphasis, equations, images, horizontal rules, and pipe tables.
Raw HTML is escaped; links and image URLs are protocol-checked.
"""
from pathlib import Path
from html import escape, unescape
import re

ROOT=Path(__file__).resolve().parents[2]/'content'/'lab-notes'
KEYWORDS={'const','static','void','int','float','double','uint8_t','uint16_t','uint32_t','if','else','for','while','return','true','false','def','class','let','var','function','import','from','as'}
TOKEN_RE=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\b[A-Za-z_]\w*\b|\b\d+(?:\.\d+)?\b')

def inline(text):
    text=escape(text,quote=False)
    def image(m):
        alt,url=unescape(m.group(1)),unescape(m.group(2))
        if not (url.startswith('/assets/') or url.startswith('https://')): return escape(alt)
        return '<img src="%s" alt="%s" loading="lazy" decoding="async">'%(escape(url,quote=True),escape(alt,quote=True))
    text=re.sub(r'!\[([^\]]*)\]\(([^\s)]+)\)',image,text)
    text=re.sub(r'`([^`]+)`',r'<code>\1</code>',text)
    text=re.sub(r'\\\((.+?)\\\)',r'<span class="inline-equation">\1</span>',text)
    text=re.sub(r'\$([^$]+)\$',r'<span class="inline-equation">\1</span>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)',r'<em>\1</em>',text)
    def link(m):
        label,url=m.group(1),unescape(m.group(2))
        if not (url.startswith(('https://','http://','/','#'))): return label
        ext=' rel="noopener noreferrer"' if url.startswith(('https://','http://')) else ''
        return '<a href="%s"%s>%s</a>'%(escape(url,quote=True),ext,label)
    return re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',link,text)

def code_html(lines,language=''):
    raw='\n'.join(lines)
    tokens=[]; pos=0
    if language in ('c','cpp','c++','js','javascript','python','py'):
        for m in TOKEN_RE.finditer(raw):
            tokens.append(escape(raw[pos:m.start()])); token=m.group(0); pos=m.end()
            if token.startswith(('//','/*')): cls='tok-comment'
            elif token.startswith(('"',"'")): cls='tok-string'
            elif token in KEYWORDS: cls='tok-keyword'
            elif re.fullmatch(r'\d+(?:\.\d+)?',token): cls='tok-number'
            else: cls='tok-ident'
            tokens.append('<span class="%s">%s</span>'%(cls,escape(token)))
        tokens.append(escape(raw[pos:]))
    else: tokens=[escape(raw)]
    lang=(' language-'+re.sub(r'[^a-z0-9_-]','',language.lower())) if language else ''
    return '<pre><code class="%s">%s</code></pre>'%(lang.strip(),''.join(tokens))

def heading_slug(text):
    text=re.sub(r'[`*_~]','',text).lower()
    return re.sub(r'[^a-z0-9]+','-',text).strip('-') or 'section'

def render_markdown(text):
    lines=text.splitlines();out=[];para=[];list_type=None;code=None;code_lang='';used_ids={}
    def flush_para():
        if para: out.append('<p>%s</p>'%inline(' '.join(x.strip() for x in para)));para.clear()
    def close_list():
        nonlocal list_type
        if list_type: out.append('</%s>'%list_type);list_type=None
    i=0
    while i<len(lines):
        line=lines[i]
        if line.startswith('```'):
            flush_para();close_list()
            if code is None: code=[];code_lang=line[3:].strip().split()[0] if line[3:].strip() else ''
            else: out.append(code_html(code,code_lang));code=None;code_lang=''
            i+=1;continue
        if code is not None: code.append(line);i+=1;continue
        if line.strip().startswith('$$'):
            flush_para();close_list();expr=line.strip()[2:]
            if expr.endswith('$$'): expr=expr[:-2]
            else:
                parts=[expr] if expr else [];i+=1
                while i<len(lines) and not lines[i].strip().endswith('$$'): parts.append(lines[i]);i+=1
                if i<len(lines):
                    tail=lines[i].strip()[:-2].strip()
                    if tail:parts.append(tail)
                expr=' '.join(parts)
            out.append('<div class="equation-block"><code>%s</code></div>'%escape(expr.strip()));i+=1;continue
        if not line.strip():flush_para();close_list();i+=1;continue
        if line.startswith('|') and i+1<len(lines) and re.match(r'^\s*\|?[\s:|-]+\|\s*$',lines[i+1]):
            flush_para();close_list();rows=[line];i+=2
            while i<len(lines) and lines[i].startswith('|'):rows.append(lines[i]);i+=1
            cells=lambda row:[x.strip() for x in row.strip().strip('|').split('|')]
            heads=cells(rows[0]);out.append('<div class="table-scroll"><table><thead><tr>%s</tr></thead><tbody>'%''.join('<th scope="col">%s</th>'%inline(x) for x in heads))
            for row in rows[1:]:out.append('<tr>%s</tr>'%''.join('<td>%s</td>'%inline(x) for x in cells(row)))
            out.append('</tbody></table></div>');continue
        if line.startswith('#'):
            flush_para();close_list();n=len(line)-len(line.lstrip('#'))
            if n<=3 and line[n:n+1]==' ':
                source=line[n+1:].strip();base=heading_slug(source);count=used_ids.get(base,0);used_ids[base]=count+1;ident=base if count==0 else '%s-%d'%(base,count+1)
                out.append('<h%d id="%s">%s</h%d>'%(n,ident,inline(source),n));i+=1;continue
        if line.startswith('> '):
            flush_para();close_list();quote=[]
            while i<len(lines) and lines[i].startswith('> '):quote.append(lines[i][2:].strip());i+=1
            out.append('<blockquote><p>%s</p></blockquote>'%inline(' '.join(quote)));continue
        if re.match(r'^\s*[-*] ',line):
            flush_para()
            if list_type!='ul':close_list();out.append('<ul>');list_type='ul'
            out.append('<li>%s</li>'%inline(re.sub(r'^\s*[-*] ','',line)));i+=1;continue
        if re.match(r'^\s*\d+\. ',line):
            flush_para()
            if list_type!='ol':close_list();out.append('<ol>');list_type='ol'
            out.append('<li>%s</li>'%inline(re.sub(r'^\s*\d+\. ','',line)));i+=1;continue
        if line.strip() in ('---','***'):flush_para();close_list();out.append('<hr>');i+=1;continue
        para.append(line);i+=1
    if code is not None:out.append(code_html(code,code_lang))
    flush_para();close_list();return '\n'.join(out)

def load_posts():
    posts=[]
    for path in sorted(ROOT.glob('*.md')):
        raw=path.read_text(encoding='utf-8')
        if not raw.startswith('---\n'):raise ValueError('Missing front matter: %s'%path)
        _,front,body=raw.split('---',2);meta={}
        for line in front.strip().splitlines():
            if ':' not in line:continue
            key,val=line.split(':',1);val=val.strip()
            if key.strip()=='tags':meta['tags']=[x.strip() for x in val.strip('[]').split(',') if x.strip()]
            else:meta[key.strip()]=val.strip('"\'')
        for key in ('slug','title','date','description'):
            if not meta.get(key):raise ValueError('%s missing in %s'%(key,path))
        slug=meta['slug']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug):raise ValueError('Unsafe slug in %s'%path)
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',meta['date']):raise ValueError('Date must be YYYY-MM-DD in %s'%path)
        meta['title']=escape(meta['title'],quote=True);meta['description']=escape(meta['description'],quote=True)
        meta['tags']=[escape(x,quote=True) for x in meta.get('tags',[])]
        meta['desc']=meta.pop('description');meta['body']=render_markdown(body.strip())
        words=len(re.findall(r'\b[\w-]+\b',re.sub(r'<[^>]+>',' ',meta['body'])))
        meta['read_time']=max(1,round(words/220));posts.append(meta)
    return posts

POSTS=load_posts()
