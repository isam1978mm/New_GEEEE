#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib, subprocess
from pathlib import Path
import cv2
from PIL import Image

ROOT = Path('artifacts/tyrone_napp_tiff_preflight')
ROOT.mkdir(parents=True, exist_ok=True)
SRC = Path('data/research/tyrone_napp_1996/Desktop.7z.001')
EX = ROOT / 'extracted'
EX.mkdir(exist_ok=True)
subprocess.run(['7z','x','-y',str(SRC),f'-o{EX}'], check=True)
files = sorted(EX.glob('NP0NAPP0095191*.tif'))

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for ch in iter(lambda:f.read(1024*1024), b''):
            h.update(ch)
    return h.hexdigest()

meta=[]
previews=[]
for p in files:
    with Image.open(p) as im:
        info={
            'name':p.name,'bytes':p.stat().st_size,'sha256':sha256(p),
            'width':im.width,'height':im.height,'mode':im.mode,'format':im.format,
            'dpi':list(im.info.get('dpi',[])) if im.info.get('dpi') else None,
            'compression':im.info.get('compression'),
        }
        meta.append(info)
        prev=im.copy(); prev.thumbnail((1600,1600)); out=ROOT/(p.stem+'_preview.jpg'); prev.convert('RGB').save(out,quality=88); previews.append(out)

# Feature matching on downscaled grayscale images. This is only a stereo-usability preflight.
imgs={}
for p in files:
    im=cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
    scale=min(1.0, 2200.0/max(im.shape[:2]))
    if scale<1.0:
        im=cv2.resize(im,None,fx=scale,fy=scale,interpolation=cv2.INTER_AREA)
    imgs[p.stem]=im
sift=cv2.SIFT_create(nfeatures=12000)
features={k:sift.detectAndCompute(v,None) for k,v in imgs.items()}
bf=cv2.BFMatcher(cv2.NORM_L2)
pairs=[]
names=[p.stem for p in files]
for a,b in zip(names,names[1:]):
    k1,d1=features[a]; k2,d2=features[b]
    knn=bf.knnMatch(d1,d2,k=2)
    good=[m for m,n in knn if m.distance < 0.75*n.distance]
    rec={'pair':[a,b],'keypoints_a':len(k1),'keypoints_b':len(k2),'ratio_test_matches':len(good)}
    if len(good)>=8:
        import numpy as np
        pts1=np.float32([k1[m.queryIdx].pt for m in good])
        pts2=np.float32([k2[m.trainIdx].pt for m in good])
        F,mask=cv2.findFundamentalMat(pts1,pts2,cv2.FM_RANSAC,2.0,0.999)
        inliers=int(mask.sum()) if mask is not None else 0
        rec['fundamental_inliers']=inliers
        rec['inlier_fraction']=inliers/len(good) if good else 0
        draw_matches=[good[i] for i in range(len(good)) if mask is not None and mask.ravel()[i]][:150]
        vis=cv2.drawMatches(imgs[a],k1,imgs[b],k2,draw_matches,None,flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        cv2.imwrite(str(ROOT/f'{a}_{b}_matches.jpg'),vis)
    pairs.append(rec)

result={'status':'COMPLETE','tiffs':meta,'pairwise_matching':pairs,'depth_values_used':False,'production_code_modified':False}
(ROOT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
