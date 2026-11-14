import sys, json; sys.path.insert(0,'pylib'); sys.path.insert(0,'.')
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
from suave import contornos
im=Image.open('../images/3.png').convert('RGB'); print('imagen',im.size)
W,H=im.size
a=np.array(im)
# figura frontal = componente conectado mas grande de la mitad izquierda
near=(a.min(axis=2)>238)
fg=~near
fg[:, int(W*0.50):]=False   # solo la figura de la izquierda (la espalda queda fuera)
lab,n=ndi.label(cv2.morphologyEx(fg.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8)))
sz=ndi.sum(lab>0,lab,range(1,n+1)); fg=(lab==1+int(np.argmax(sz)))
fg=ndi.binary_fill_holes(fg)
ys,xs=np.where(fg); x0,y0,x1,y1=xs.min(),ys.min(),xs.max()+1,ys.max()+1; print('bbox figura',x0,y0,x1,y1)
rgb=a[y0:y1,x0:x1]; al=fg[y0:y1,x0:x1].astype(np.uint8)
Z=3
rgb=cv2.resize(rgb,None,fx=Z,fy=Z,interpolation=cv2.INTER_CUBIC); al=cv2.resize(al,(rgb.shape[1],rgb.shape[0]),interpolation=cv2.INTER_NEAREST)
rgb=cv2.bilateralFilter(rgb,7,30,7)
lab_img=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).reshape(-1,3).astype(np.float32)
ok=(al.reshape(-1)>0); idx=np.where(ok)[0][::5]
K=9
_,_,cent=cv2.kmeans(lab_img[idx],K,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,40,0.5),3,cv2.KMEANS_PP_CENTERS)
lbl=((lab_img[:,None,:]-cent[None,:,:])**2).sum(axis=2).argmin(axis=1).astype(np.uint8).reshape(al.shape)
lbl=cv2.medianBlur(lbl,5)
cols=[]
for k in range(K):
    m=(lbl==k)&(al>0); cols.append(rgb[m].mean(axis=0) if m.any() else np.zeros(3))
orden=sorted(range(K),key=lambda k:cols[k].sum())
hexc=lambda c:'#%02x%02x%02x'%tuple(int(v) for v in c)
print('colores',[hexc(cols[k]) for k in orden])
parts=['<path fill="%s" d="%s"/>'%(hexc(cols[orden[0]]),contornos(al,1.8,200,1.0/Z,cv2.RETR_EXTERNAL,1.0))]
for k in orden:
    m=((lbl==k)&(al>0)).astype(np.uint8)
    d=contornos(m,1.6,40,1.0/Z,cv2.RETR_CCOMP,1.0)
    if d: parts.append('<path fill="%s" fill-rule="evenodd" d="%s"/>'%(hexc(cols[k]),d))
g=''.join(parts)
open('torso_trazado.txt','w').write(g)
json.dump({'w':int(x1-x0),'h':int(y1-y0),'x0':int(x0),'y0':int(y0)},open('torso_dim.json','w'))
print('KB',len(g)//1024)
# vista previa
open('torso_prev.svg','w').write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">%s</svg>'%(x1-x0,y1-y0,g))
