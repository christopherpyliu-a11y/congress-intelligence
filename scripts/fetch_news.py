#!/usr/bin/env python3
"""Fetch public congressional news hourly; retain sourced items from the last 5 days."""
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
import pathlib
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlencode

ROOT = pathlib.Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc
NOW = dt.datetime.now(UTC)
CUTOFF = NOW - dt.timedelta(days=5)
FEEDS = {
    "The Hill — House": "https://thehill.com/homenews/house/feed/",
    "The Hill — Senate": "https://thehill.com/homenews/senate/feed/",
    "Roll Call": "https://rollcall.com/feed/",
    "Defense News — Congress": "https://www.defensenews.com/arc/outboundfeeds/rss/category/congress/?outputType=xml",
    "Politico — Congress": "https://www.politico.com/rss/congress.xml",
}
TERMS = re.compile(r"\b(congress|senate|senator|house of representatives|lawmaker|representative|capitol hill|legislation|bill|committee|taiwan|china|indo.pacific|pentagon|national defense authorization|ndaa)\b", re.I)
TAG = re.compile(r"<[^>]+>")
def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "CongressIQ-PublicFeedMonitor/1.0 (+https://github.com/christopherpyliu-a11y/congress-intelligence)", "Accept": "application/rss+xml,application/atom+xml,application/xml,text/xml"})
    with urllib.request.urlopen(req, timeout=18) as resp:
        return resp.read(3_000_000)

def dt_parse(value):
    if not value: return None
    try:
        d = email.utils.parsedate_to_datetime(value)
    except (ValueError, TypeError):
        try: d = dt.datetime.fromisoformat(value.replace("Z","+00:00"))
        except ValueError: return None
    return (d.replace(tzinfo=UTC) if d.tzinfo is None else d.astimezone(UTC))

def safe_link(link):
    try:
        p = urlparse(link)
        if p.scheme not in ("http", "https") or not p.netloc: return None
        if p.hostname in ("news.google.com", "google.com"): return None
        return link
    except ValueError: return None

def text(node, *tags):
    for tag in tags:
        v = node.findtext(tag)
        if v: return v.strip()
    return ""

def parse_feed(source, content):
    root=ET.fromstring(content)
    ns={"a":"http://www.w3.org/2005/Atom","content":"http://purl.org/rss/1.0/modules/content/"}
    if root.tag.endswith("feed"):
        entries=root.findall("a:entry",ns)
        atom=True
    else:
        entries=root.findall(".//item")
        atom=False
    results=[]
    for e in entries:
        title=html.unescape(text(e,"title","a:title") if not atom else text(e,"a:title")).strip()
        raw_date=text(e,"pubDate","dc:date") if not atom else text(e,"a:published","a:updated")
        when=dt_parse(raw_date)
        if not when or not CUTOFF<=when<=NOW+dt.timedelta(minutes=5): continue
        if atom:
            link=""
            for el in e.findall("a:link",ns):
                if el.get("rel","alternate")=="alternate" and el.get("href"):
                    link=el.get("href"); break
            description=text(e,"a:summary","a:content")
        else:
            link=text(e,"link")
            description=text(e,"description")
        link=safe_link(link)
        if not link or not title: continue
        if not TERMS.search(title+" "+re.sub(TAG," ",description)): continue
        summary=html.unescape(TAG.sub(" ",description))
        summary=" ".join(summary.split())[:380]
        if not summary: summary="來源提供新聞標題及原文連結；尚無可確認的摘要。"
        category="涉台／涉中" if re.search(r"taiwan|china|indo.pacific",title+" "+summary,re.I) else "國會動態"
        results.append({"id":hashlib.sha256(link.encode()).hexdigest()[:20],"title":title,"summary":summary,
                        "published_at":when.isoformat().replace("+00:00","Z"),"source_url":link,
                        "source":source,"category":category})
    return results

def existing():
    try:
        o=json.loads((ROOT/"news.json").read_text(encoding="utf-8"))
        return o if isinstance(o,list) else []
    except (OSError, ValueError): return []

def valid(row):
    if not isinstance(row,dict): return False
    published=dt_parse(row.get("published_at",""))
    return bool(published and CUTOFF<=published<=NOW+dt.timedelta(minutes=5)
                and row.get("title") and safe_link(row.get("source_url","")))

def main():
    before=[x for x in existing() if valid(x)]
    merged={x["source_url"]:x for x in before}
    diagnostics={}
    fresh=0
    for source, url in FEEDS.items():
        try:
            rows=parse_feed(source,get(url))
            for row in rows:
                if row["source_url"] not in merged: fresh+=1
                merged[row["source_url"]]=row
            diagnostics[source]={"ok":True,"fetched":len(rows)}
        except Exception as exc:
            diagnostics[source]={"ok":False,"error":str(exc)[:180]}
    # Do not overwrite a previously working feed archive if every source failed.
    rows=sorted(merged.values(),key=lambda x:x["published_at"],reverse=True)[:400]
    (ROOT/"news.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    status={"checked_at":NOW.isoformat(),"last_window_days":5,"new_items":fresh,
            "retained_items":len(rows),"sources":diagnostics,
            "warning":"RSS摘要保留來源原語言；不代表已通過AI中文翻譯或政策研判。"}
    (ROOT/"news-status.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(status,ensure_ascii=False))
if __name__=="__main__": main()
