#!/usr/bin/env python3
"""Temporary research-only EarthExplorer scene-list query for Tyrone 3X.

Uses a small four-corner polygon around the six 3X plots (not a zero-area
single point) and checks two pre-reclamation time windows. No imagery is
Downloaded and no depth/model/application code is used.
"""
from __future__ import annotations
import html as html_lib, json, re
from pathlib import Path
from urllib.parse import urlencode
import requests

OUT=Path("artifacts/tyrone_step3_aerial_inventory"); OUT.mkdir(parents=True,exist_ok=True)
ALIAS="AERIAL_COMBIN"; ROOT="https://earthexplorer.usgs.gov/"
# Small box around Tyrone 3X and immediate stable-ground margin.
AOI=[
    (32.7160,-108.4250),
    (32.7160,-108.4130),
    (32.7270,-108.4130),
    (32.7270,-108.4250),
]
CENTER=(32.7215,-108.4193)
PREDEFINED=ROOT+"criteria?"+urlencode({"node":"EE","dataset_name":ALIAS,"aoiFilter":json.dumps([[CENTER[0],CENTER[1]]],separators=(",",":"))})
PERIODS=[("2000_to_aug2004","01/01/2000","08/31/2004"),("1990s","01/01/1990","12/31/1999")]

def compact(t): return re.sub(r"\s+"," ",html_lib.unescape(t)).strip()
def ps(s,p):
    r=s.post(ROOT+"tabs/save",data={"data":json.dumps(p,separators=(",",":"))},timeout=120)
    return [r.status_code,compact(r.text)[:500]]
def rows(text,cid):
    out=[]
    for m in re.finditer(r"<tr\b([^>]*(?:data-entityId|data-entityid)[^>]*)>(.*?)</tr>",text,re.I|re.S):
        a,b=m.group(1),m.group(2)
        def at(n):
            q=re.search(rf"\b{n}=[\"']([^\"']*)[\"']",a,re.I)
            return html_lib.unescape(q.group(1)) if q else None
        eid=at("data-entityId")
        if eid:
            out.append({"collection_id":cid,"entity_id":eid,"display_id":at("data-displayId"),"scene_id":at("data-scene-id"),"corner_points":at("data-corner-points"),"row_text":compact(re.sub(r"<[^>]+>"," ",b))})
    return list({r["entity_id"]:r for r in out}.values())

def collection_id(s):
    cats=s.get(ROOT+"dataset/categories",timeout=120); cats.raise_for_status()
    for t in re.findall(r"<span\b[^>]*class=[\"'][^\"']*collection[^\"']*[\"'][^>]*>",cats.text,re.I):
        am=re.search(r"data-datasetAlias=[\"']([^\"']+)[\"']",t,re.I)
        im=re.search(r"data-datasetId=[\"']([^\"']+)[\"']",t,re.I)
        if am and im and am.group(1).upper()==ALIAS: return im.group(1)
    p=cats.text.upper().find(ALIAS)
    sn=cats.text[max(0,p-1200):p+1200] if p>=0 else ""
    ids=re.findall(r"data-datasetId=[\"']([^\"']+)[\"']",sn,re.I)
    if ids: return ids[-1]
    raise RuntimeError("AERIAL_COMBIN collection id not found")

def query_period(label,start,end):
    s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 Tyrone-research/1.0","Referer":ROOT})
    landing=s.get(PREDEFINED,timeout=120,allow_redirects=True); landing.raise_for_status()
    cid=collection_id(s)
    s.post(ROOT+"tabs/clear",timeout=120)
    coords=[{"c":str(i),"a":f"{lat:.4f}","o":f"{lon:.4f}"} for i,(lat,lon) in enumerate(AOI)]
    tab1=ps(s,{"tab":1,"destination":4,"coordinates":coords,"format":"dd","dStart":start,"dEnd":end,"searchType":"Std","includeUnknownCC":"1","maxCC":100,"minCC":0,"months":[str(i) for i in range(12)],"pType":"polygon"})
    tab2=ps(s,{"tab":2,"destination":4,"cList":[cid],"selected":cid})
    sel=s.post(ROOT+"dataset/select",data={"datasetId":cid},timeout=120)
    sr=s.post(ROOT+"scene/search",data={"datasetId":cid,"resultsPerPage":100},timeout=300); sr.raise_for_status()
    (OUT/f"scene_search_{label}_page1.html").write_text(sr.text,encoding="utf-8")
    rr=rows(sr.text,cid)
    nums=[int(x) for x in re.findall(r"(?:data-page|value)=[\"'](\d+)[\"']",sr.text,re.I)]
    mp=min(max(nums or [1]),10)
    for pg in range(2,mp+1):
        x=s.post(ROOT+"scene/search",data={"datasetId":cid,"resultsPerPage":100,"pageNum":pg},timeout=300)
        if x.ok:
            (OUT/f"scene_search_{label}_page{pg}.html").write_text(x.text,encoding="utf-8")
            rr.extend(rows(x.text,cid))
    rr=list({r["entity_id"]:r for r in rr}.values())
    return {"label":label,"date_start":start,"date_end":end,"tab1_save":tab1,"tab2_save":tab2,"dataset_select_status":sel.status_code,"scene_search_status":sr.status_code,"scene_search_chars":len(sr.text),"scene_count":len(rr),"scenes":rr}

def main():
    period_results=[query_period(*p) for p in PERIODS]
    result={"status":"STEP3_AREA_SCENE_LIST_COMPLETE","dataset_alias":ALIAS,"aoi_polygon_latlon":AOI,"center_wgs84":CENTER,"periods":period_results,"imagery_downloaded":False,"depth_calculated":False,"production_code_modified":False}
    (OUT/"scene_list.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
