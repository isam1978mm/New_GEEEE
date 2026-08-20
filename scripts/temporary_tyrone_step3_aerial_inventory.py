#!/usr/bin/env python3
"""Temporary research-only fast EarthExplorer scene-list query for Tyrone 3X."""
from __future__ import annotations
import html as html_lib, json, re
from pathlib import Path
from urllib.parse import urlencode
import requests

OUT=Path("artifacts/tyrone_step3_aerial_inventory"); OUT.mkdir(parents=True,exist_ok=True)
LAT,LON=32.7215,-108.4193; ALIAS="AERIAL_COMBIN"; ROOT="https://earthexplorer.usgs.gov/"
DATE_START="01/01/1990"; DATE_END="12/31/1999"
PREDEFINED=ROOT+"criteria?"+urlencode({"node":"EE","dataset_name":ALIAS,"aoiFilter":json.dumps([[LAT,LON]],separators=(",",":"))})
def compact(t): return re.sub(r"\s+"," ",html_lib.unescape(t)).strip()
def save(n,t): (OUT/n).write_text(t,encoding="utf-8")
def ps(s,p):
 r=s.post(ROOT+"tabs/save",data={"data":json.dumps(p,separators=(",",":"))},timeout=120); return [r.status_code,compact(r.text)[:500]]
def rows(text,cid):
 out=[]
 for m in re.finditer(r"<tr\b([^>]*(?:data-entityId|data-entityid)[^>]*)>(.*?)</tr>",text,re.I|re.S):
  a,b=m.group(1),m.group(2)
  def at(n):
   q=re.search(rf"\b{n}=[\"']([^\"']*)[\"']",a,re.I); return html_lib.unescape(q.group(1)) if q else None
  eid=at("data-entityId")
  if eid: out.append({"collection_id":cid,"entity_id":eid,"display_id":at("data-displayId"),"scene_id":at("data-scene-id"),"corner_points":at("data-corner-points"),"row_text":compact(re.sub(r"<[^>]+>"," ",b))})
 return list({r["entity_id"]:r for r in out}.values())
def main():
 s=requests.Session(); s.headers.update({"User-Agent":"Mozilla/5.0 Tyrone-research/1.0","Referer":ROOT})
 l=s.get(PREDEFINED,timeout=120,allow_redirects=True); l.raise_for_status()
 cats=s.get(ROOT+"dataset/categories",timeout=120); cats.raise_for_status(); save("dataset_categories.html",cats.text)
 cid=None; tag=None
 for t in re.findall(r"<span\b[^>]*class=[\"'][^\"']*collection[^\"']*[\"'][^>]*>",cats.text,re.I):
  am=re.search(r"data-datasetAlias=[\"']([^\"']+)[\"']",t,re.I); im=re.search(r"data-datasetId=[\"']([^\"']+)[\"']",t,re.I)
  if am and im and am.group(1).upper()==ALIAS: cid=im.group(1); tag=t; break
 if not cid:
  p=cats.text.upper().find(ALIAS); sn=cats.text[max(0,p-1200):p+1200]; ids=re.findall(r"data-datasetId=[\"']([^\"']+)[\"']",sn,re.I); cid=ids[-1] if ids else None
 if not cid: raise RuntimeError("AERIAL_COMBIN collection id not found")
 s.post(ROOT+"tabs/clear",timeout=120)
 tab1=ps(s,{"tab":1,"destination":4,"coordinates":[{"c":"0","a":f"{LAT:.4f}","o":f"{LON:.4f}"}],"format":"dd","dStart":DATE_START,"dEnd":DATE_END,"searchType":"Std","includeUnknownCC":"1","maxCC":100,"minCC":0,"months":[str(i) for i in range(12)],"pType":"polygon"})
 tab2=ps(s,{"tab":2,"destination":4,"cList":[cid],"selected":cid})
 sel=s.post(ROOT+"dataset/select",data={"datasetId":cid},timeout=120)
 sr=s.post(ROOT+"scene/search",data={"datasetId":cid,"resultsPerPage":100},timeout=300); sr.raise_for_status(); save("scene_search_page1.html",sr.text)
 rr=rows(sr.text,cid)
 nums=[int(x) for x in re.findall(r"(?:data-page|value)=[\"'](\d+)[\"']",sr.text,re.I)]; mp=min(max(nums or [1]),10)
 for pg in range(2,mp+1):
  x=s.post(ROOT+"scene/search",data={"datasetId":cid,"resultsPerPage":100,"pageNum":pg},timeout=300)
  if x.ok: save(f"scene_search_page{pg}.html",x.text); rr.extend(rows(x.text,cid))
 rr=list({r["entity_id"]:r for r in rr}.values())
 result={"status":"STEP3_FAST_SCENE_LIST_COMPLETE","dataset_alias":ALIAS,"collection_id":cid,"point_wgs84":[LAT,LON],"date_start":"1990-01-01","date_end":"1999-12-31","tab1_save":tab1,"tab2_save":tab2,"dataset_select_status":sel.status_code,"scene_search_status":sr.status_code,"scene_search_chars":len(sr.text),"scene_count":len(rr),"scenes":rr,"imagery_downloaded":False,"depth_calculated":False,"production_code_modified":False}
 (OUT/"scene_list.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,indent=2)); return 0
if __name__=="__main__": raise SystemExit(main())
