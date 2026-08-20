#!/usr/bin/env python3
"""Temporary research-only EarthExplorer NAPP inventory for Tyrone 3X.

Discovers EarthExplorer collections whose alias/title contains NAPP or National
Aerial Photography Program, then queries a real four-corner Tyrone 3X AOI for
1995-1999. Records scene identifiers only. No imagery/depth/model/app changes.
"""
from __future__ import annotations
import html as html_lib, json, re
from pathlib import Path
from urllib.parse import urlencode
import requests

OUT=Path("artifacts/tyrone_step3_aerial_inventory"); OUT.mkdir(parents=True,exist_ok=True)
ROOT="https://earthexplorer.usgs.gov/"
AOI=[(32.7160,-108.4250),(32.7160,-108.4130),(32.7270,-108.4130),(32.7270,-108.4250)]
CENTER=(32.7215,-108.4193)

def compact(t): return re.sub(r"\s+"," ",html_lib.unescape(t)).strip()
def ps(s,p):
    r=s.post(ROOT+"tabs/save",data={"data":json.dumps(p,separators=(",",":"))},timeout=120)
    return [r.status_code,compact(r.text)[:500]]
def parse_rows(text,cid,alias):
    out=[]
    for m in re.finditer(r"<tr\b([^>]*(?:data-entityId|data-entityid)[^>]*)>(.*?)</tr>",text,re.I|re.S):
        a,b=m.group(1),m.group(2)
        def at(n):
            q=re.search(rf"\b{n}=[\"']([^\"']*)[\"']",a,re.I)
            return html_lib.unescape(q.group(1)) if q else None
        eid=at("data-entityId")
        if eid:
            out.append({"collection_id":cid,"dataset_alias":alias,"entity_id":eid,"display_id":at("data-displayId"),"scene_id":at("data-scene-id"),"corner_points":at("data-corner-points"),"row_text":compact(re.sub(r"<[^>]+>"," ",b))})
    return list({r["entity_id"]:r for r in out}.values())
def discover(s):
    r=s.get(ROOT+"dataset/categories",timeout=120); r.raise_for_status()
    (OUT/"dataset_categories.html").write_text(r.text,encoding="utf-8")
    matches=[]
    # Parse complete collection spans when possible.
    for m in re.finditer(r"<span\b([^>]*class=[\"'][^\"']*collection[^\"']*[\"'][^>]*)>(.*?)</span>",r.text,re.I|re.S):
        attrs,body=m.group(1),m.group(2)
        am=re.search(r"data-datasetAlias=[\"']([^\"']+)[\"']",attrs,re.I)
        im=re.search(r"data-datasetId=[\"']([^\"']+)[\"']",attrs,re.I)
        title=compact(re.sub(r"<[^>]+>"," ",body))
        if not (am and im): continue
        alias=am.group(1); cid=im.group(1)
        if re.search(r"napp|national aerial photography",alias+" "+title,re.I):
            matches.append({"alias":alias,"collection_id":cid,"title":title})
    # Fallback: inspect ±500 chars around every NAPP occurrence for attributes.
    if not matches:
        for mm in re.finditer(r"NAPP|National Aerial Photography",r.text,re.I):
            sn=r.text[max(0,mm.start()-800):min(len(r.text),mm.end()+800)]
            am=re.search(r"data-datasetAlias=[\"']([^\"']+)[\"']",sn,re.I)
            im=re.search(r"data-datasetId=[\"']([^\"']+)[\"']",sn,re.I)
            if am and im: matches.append({"alias":am.group(1),"collection_id":im.group(1),"title":compact(re.sub(r"<[^>]+>"," ",sn))[:500]})
    return list({(x["alias"],x["collection_id"]):x for x in matches}.values())
def query(c):
    alias,cid=c["alias"],c["collection_id"]
    s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 Tyrone-research/1.0","Referer":ROOT})
    pre=ROOT+"criteria?"+urlencode({"node":"EE","dataset_name":alias,"aoiFilter":json.dumps([[CENTER[0],CENTER[1]]],separators=(",",":"))})
    l=s.get(pre,timeout=120,allow_redirects=True); l.raise_for_status()
    s.post(ROOT+"tabs/clear",timeout=120)
    coords=[{"c":str(i),"a":f"{lat:.4f}","o":f"{lon:.4f}"} for i,(lat,lon) in enumerate(AOI)]
    tab1=ps(s,{"tab":1,"destination":4,"coordinates":coords,"format":"dd","dStart":"01/01/1995","dEnd":"12/31/1999","searchType":"Std","includeUnknownCC":"1","maxCC":100,"minCC":0,"months":[str(i) for i in range(12)],"pType":"polygon"})
    tab2=ps(s,{"tab":2,"destination":4,"cList":[cid],"selected":cid})
    sel=s.post(ROOT+"dataset/select",data={"datasetId":cid},timeout=120)
    sr=s.post(ROOT+"scene/search",data={"datasetId":cid,"resultsPerPage":100},timeout=300)
    text=sr.text if sr.ok else ""
    (OUT/f"scene_search_{re.sub(r'[^A-Za-z0-9_.-]+','_',alias)}.html").write_text(text,encoding="utf-8")
    rr=parse_rows(text,cid,alias)
    return {**c,"tab1_save":tab1,"tab2_save":tab2,"dataset_select_status":sel.status_code,"scene_search_status":sr.status_code,"scene_search_chars":len(text),"scene_count":len(rr),"scenes":rr}
def main():
    s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 Tyrone-research/1.0"})
    candidates=discover(s)
    queries=[]
    for c in candidates:
        try: queries.append(query(c))
        except Exception as exc: queries.append({**c,"error":type(exc).__name__+": "+str(exc)})
    result={"status":"STEP3_NAPP_COLLECTION_QUERY_COMPLETE","aoi_polygon_latlon":AOI,"center_wgs84":CENTER,"date_start":"1995-01-01","date_end":"1999-12-31","napp_collections":candidates,"queries":queries,"imagery_downloaded":False,"depth_calculated":False,"production_code_modified":False}
    (OUT/"scene_list.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
