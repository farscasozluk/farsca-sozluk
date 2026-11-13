"""ENEX okuma ve ENML -> satır listesi dönüşümü."""
import re
from lxml import etree
import lxml.html

BLOCK = {'div','p','li','h1','h2','h3','h4','h5','h6','tr','blockquote','pre','table','ol','ul','en-todo','hr'}

def read_enex(path):
    parser = etree.XMLParser(huge_tree=True, recover=True)
    tree = etree.parse(path, parser)
    for n in tree.iter('note'):
        title = (n.findtext('title') or '').strip()
        content = n.findtext('content') or ''
        created = n.findtext('created') or ''
        updated = n.findtext('updated') or ''
        tags = [t.text for t in n.findall('tag') if t.text]
        yield dict(title=title, content=content, created=created, updated=updated, tags=tags)

def enml_lines(content):
    """Return list of dicts: text, italic (fraction of italic chars), bold spans, li (bool), depth."""
    content = re.sub(r'^\s*<\?xml[^>]*\?>', '', content)
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content)
    if not content.strip():
        return []
    try:
        root = lxml.html.fragment_fromstring(content, create_parent='div')
    except Exception:
        return []
    lines = []
    cur = {'segs': [], 'li': False}
    def flush():
        segs = cur['segs']
        text = ''.join(s[0] for s in segs)
        if text.strip() or segs:
            lines.append({'segs': segs, 'li': cur['li']})
        cur['segs'] = []
        cur['li'] = False
    def walk(el, ital, bold, in_li):
        tag = el.tag if isinstance(el.tag, str) else ''
        tag = tag.lower()
        style = (el.get('style') or '') if tag else ''
        if 'display:none' in style.replace(' ', ''):
            if el.tail: cur['segs'].append((el.tail, ital, bold))
            return
        if tag in ('en-media','img','script','style'):
            if el.tail: cur['segs'].append((el.tail, ital, bold))
            return
        is_block = tag in BLOCK
        i2 = ital or tag in ('i','em') or 'font-style:italic' in style.replace(' ','')
        b2 = bold or tag in ('b','strong') or 'font-weight:bold' in style.replace(' ','') or 'font-weight:700' in style.replace(' ','')
        li2 = in_li or tag == 'li'
        if is_block and cur['segs']:
            flush()
        if tag == 'br':
            flush()
            if el.tail: cur['segs'].append((el.tail, ital, bold)); cur['li'] = in_li
            return
        if is_block: cur['li'] = li2
        if el.text: cur['segs'].append((el.text, i2, b2)); cur['li'] = cur['li'] or li2
        for ch in el:
            walk(ch, i2, b2, li2)
        if is_block:
            if cur['segs']: flush()
            elif tag in ('div','p') and len(el)==0 and not (el.text or '').strip():
                lines.append({'segs': [], 'li': False})  # empty paragraph
        if el.tail:
            cur['segs'].append((el.tail, ital, bold))
    walk(root, False, False, False)
    if cur['segs']: flush()
    out = []
    for l in lines:
        text = ''.join(s[0] for s in l['segs']).replace('\xa0',' ')
        n = len(text.strip()) or 1
        it = sum(len(s[0].strip()) for s in l['segs'] if s[1]) / n
        bold = [s[0] for s in l['segs'] if s[2] and s[0].strip()]
        out.append({'text': text.strip(), 'italic': it, 'li': l['li'], 'bold': bold})
    # collapse multiple empties
    res = []
    for l in out:
        if not l['text'] and res and not res[-1]['text']:
            continue
        res.append(l)
    while res and not res[0]['text']: res.pop(0)
    while res and not res[-1]['text']: res.pop()
    return res
