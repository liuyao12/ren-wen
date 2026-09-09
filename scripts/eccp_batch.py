#!/usr/bin/env python3
"""Rebuild batch 01 from preserved MediaWiki responses and explicit editorial rules.

This is an editorial import, not a general name recognizer. The rules list identifies
occurrences in this batch; source HTML is inert and source wording is never corrected.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import argparse, copy, hashlib, json, re

ROOT = Path(__file__).resolve().parents[1]

@dataclass
class Node:
    tag: str = ''
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    def text(self):
        return ''.join(c if isinstance(c,str) else c.text() for c in self.children)

class Tree(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root=Node(''); self.stack=[self.root]; self.feed(text)
    def handle_starttag(self,tag,attrs):
        n=Node(tag,dict(attrs)); self.stack[-1].children.append(n)
        if tag not in {'br','hr','img','meta','link','input','wbr','source'}: self.stack.append(n)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:
                del self.stack[i:]; break
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if self.stack[-1].tag==tag: self.handle_endtag(tag)
    def handle_data(self,text): self.stack[-1].children.append(text)

def nodes(n):
    yield n
    for c in n.children:
        if isinstance(c,Node): yield from nodes(c)

def clean(n):
    if isinstance(n,str): return re.sub(r'[ \t\r\n]+',' ',n)
    if n.tag in {'script','style','img','hr','link'} or 'ws-pagenum' in n.attrs.get('class','').split(): return ''
    children=[clean(c) for c in n.children]
    # Flatten purely presentational wrappers, retaining source italics and emphasis.
    tag=n.tag if n.tag in {'i','b','em','strong','sup','sub','br','a'} else ''
    attrs={}
    if tag=='a':
        url=urljoin('https://en.wikisource.org',n.attrs.get('href',''))
        if url.startswith(('https://','http://')): attrs={'href':url}
        else: tag=''
    return Node(tag,attrs,children)

def fragment(n,start,end):
    """Slice text coordinates while retaining inline HTML and source links."""
    if isinstance(n,str): return escape(n[start:end],quote=False)
    result=[]; offset=0
    for c in n.children:
        size=len(c if isinstance(c,str) else c.text())
        lo=max(0,start-offset); hi=min(size,end-offset)
        if hi>lo: result.append(fragment(c,lo,hi))
        offset+=size
    inner=''.join(result)
    if not inner: return ''
    if not n.tag:return inner
    attrs=''.join(f' {k}="{escape(str(v),quote=True)}"' for k,v in n.attrs.items())
    return f'<{n.tag}{attrs}>{inner}</{n.tag}>' if n.tag!='br' else '<br>'

def source_paragraphs(html):
    root=Tree(html).root
    body=next(n for n in nodes(root) if 'prp-pages-output' in n.attrs.get('class','').split())
    paragraphs=[]
    for p in nodes(body):
        if p.tag!='p': continue
        n=clean(p); t=n.text()
        if not t.strip(): continue
        # Trim only presentation whitespace, not source punctuation or word-internal spaces.
        lo=len(t)-len(t.lstrip()); hi=len(t.rstrip())
        paragraphs.append(Tree(fragment(n,lo,hi)).root)
    return paragraphs

def split_paragraphs(paragraphs,starts):
    result=[]
    for source_index,n in enumerate(paragraphs,1):
        text=n.text(); cuts={0,len(text)}
        for start in starts:
            at=text.find(start)
            if at>0: cuts.add(at)
        cuts=sorted(cuts)
        for a,b in zip(cuts,cuts[1:]):
            while a<b and text[a].isspace(): a+=1
            while b>a and text[b-1].isspace(): b-=1
            if b>a: result.append((Tree(fragment(n,a,b)).root,source_index))
    return result

def matches(text,rule):
    for term in rule['terms']:
        pattern=re.escape(term)
        if term[0].isascii() and term[0].isalnum(): pattern=r'(?<![\w])'+pattern
        if term[-1].isascii() and term[-1].isalnum(): pattern+=r'(?![\w-])'
        for m in re.finditer(pattern,text): yield m.start(),m.end(),term

def annotate(n,rules,pid,existing):
    text=n.text(); hits=[]
    for priority,rule in enumerate(rules):
        for a,b,term in matches(text,rule): hits.append((a,b,rule,priority))
    # Prefer the full, explicitly named work to personal words inside its title.
    hits.sort(key=lambda x:(x[0],-(x[1]-x[0]),x[3]))
    selected=[]; end=-1
    for hit in hits:
        if hit[0]<end:continue
        selected.append(hit);end=hit[1]
    known=list(existing); reserved={m['id'] for m in known}; used=set(); cursor=0; parts=[]; records=[]; serial=1
    for a,b,rule,_ in selected:
        quote=text[a:b]
        old=next((m for m in known if m['entity']==rule['entity'] and m['quote']==quote and m['id'] not in used),None)
        if old: mid=old['id']
        else:
            while f'{pid}-n{serial:03}' in used | reserved: serial+=1
            mid=f'{pid}-n{serial:03}';serial+=1
        used.add(mid)
        parts.append(fragment(n,cursor,a))
        parts.append(f'<span id="{mid}" data-entity="{rule["entity"]}">{fragment(n,a,b)}</span>')
        cursor=b
        record={**(old or {}),'id':mid,'witness':rule['witness'],'passage':pid,'entity':rule['entity'],'quote':quote,'status':(old or {}).get('status','proposed'),'origin':(old or {}).get('origin','eccp-batch-01'),'note':rule.get('note','Explicit batch annotation; awaiting independent review.')}
        records.append(record)
    parts.append(fragment(n,cursor,len(text)))
    return '<p id="'+pid+'">'+''.join(parts)+'</p>',records


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--rebuild',action='store_true',help='Explicitly rebuild an existing batch in a review worktree; inspect its diff before publication.')
    args=parser.parse_args()
    if (args.root/'data/editorial/eccp-batch-01-report.json').exists() and not args.rebuild:
        parser.error('This batch already exists. Edit its records directly, or explicitly use --rebuild in a review worktree.')
    from scripts.eccp_compile import compile_batch
    compile_batch(args.root)

if __name__=='__main__': main()
