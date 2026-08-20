#!/usr/bin/env python3
"""Temporary research-only metadata check for exact Tyrone 1996 NAPP records.

No imagery is downloaded. Queries public EarthExplorer metadata/download-option
pages for the eight NAPP records already found over the fixed Tyrone AOI.
"""
from __future__ import annotations
import html as html_lib, json, re
from pathlib import Path
import requests

OUT=Path("artifacts/tyrone_step3_aerial_inventory"); OUT.mkdir(parents=True,exist_ok=True)
ROOT="https://earthexplorer.usgs.gov/"
CID="5e83a396ee5f70de"
SCENES=[
"N10NAPPW09639042","N10NAPPW09639043",
"NP0NAPP009519108","NP0NAPP009519109","NP0NAPP009519110",
"NP0NAPP009519201","NP0NAPP009519202","NP0NAPP009519203",
]

def compact(t): return re.sub(r"\s+"," ",html_lib.unescape(re.sub(r"<[^>]+>"," ",t))).strip()
def attrs(text):
    pairs={}
    # table label/value pairs
    for m in re.finditer(r"<tr[^>]*>\s*<t[dh][^>]*>(.*?)</t[dh]>\s*<t[dh][^>]*>(.*?)</t[dh]>\s*</tr>",text,re.I|re.S):
        k=compact(m.group(1)).rstrip(":"); v=compact(m.group(2))
        if k and v: pairs[k]=v
    # definition lists
    for m in re.finditer(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>",text,re.I|re.S):
        k=compact(m.group(1)).rstrip(":"); v=compact(m.group(2))
        if k and v: pairs[k]=v
    return pairs

def useful_snippets(text):
    vis=compact(text)
    keys=["roll","frame","exposure","camera","focal","calibration","film","scale","acquisition","scan","resolution","download","medium","high resolution","product"]
    out={}
    low=vis.lower()
    for key in keys:
        pos=low.find(key.lower())
        if pos>=0: out[key]=vis[max(0,pos-220):min(len(vis),pos+650)]
    return out

def main():
    s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 Tyrone-research/1.0","Referer":ROOT})
    # establish ordinary anonymous EarthExplorer session
    s.get(ROOT+"criteria",timeout=120)
    records=[]
    for eid in SCENES:
        rec={"entity_id":eid}
        for kind,url,method in [
            ("metadata_full",ROOT+f"scene/metadata/full/{CID}/{eid}/","get"),
            ("metadata_info",ROOT+f"scene/metadata/info/{CID}/{eid}/","get"),
            ("download_options",ROOT+f"scene/downloadoptions/{CID}/{eid}","post"),
        ]:
            try:
                r=s.get(url,timeout=120) if method=="get" else s.post(url,data={},timeout=120)
                text=r.text
                (OUT/f"{kind}_{eid}.html").write_text(text,encoding="utf-8")
                rec[kind]={
                    "http_status":r.status_code,
                    "chars":len(text),
                    "visible_text":compact(text),
                    "pairs":attrs(text),
                    "snippets":useful_snippets(text),
                    "hrefs":sorted(set(html_lib.unescape(x) for x in re.findall(r"href=[\"']([^\"']+)[\"']",text,re.I))),
                    "data_urls":sorted(set(html_lib.unescape(x) for x in re.findall(r"(?:data-url|data-download-url)=[\"']([^\"']+)[\"']",text,re.I))),
                    "product_ids":sorted(set(x for x in re.findall(r"(?:productId|product-id|data-product-id)[=:\"' ]+([A-Za-z0-9_.-]+)",text,re.I))),
                }
            except Exception as exc:
                rec[kind]={"error":type(exc).__name__+": "+str(exc)}
        records.append(rec)
    result={"status":"STEP3_NAPP_METADATA_DOWNLOAD_CHECK_COMPLETE","collection_id":CID,"scene_count":len(records),"records":records,"imagery_downloaded":False,"depth_calculated":False,"production_code_modified":False}
    (OUT/"scene_list.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
