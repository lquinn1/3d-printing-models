# SPDX-License-Identifier: MIT
"""Render images/preview.png from the STLs (small numpy z-buffer, no GPU needed).
Usage (from the model folder): python3 source/render_preview.py"""
import numpy as np, trimesh
def rot(elev, azim):
    a, e = np.radians(azim), np.radians(elev)
    Rz = np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    Rx = np.array([[1,0,0],[0,np.cos(e),-np.sin(e)],[0,np.sin(e),np.cos(e)]])
    return Rx@Rz
def render(meshes, elev, azim, size=700, pad=0.06):
    R = rot(elev, azim)
    allv = np.vstack([m.vertices@R.T for m,_ in meshes])
    lo, hi = allv[:,[0,2]].min(0), allv[:,[0,2]].max(0)
    sc = size*(1-2*pad)/(hi-lo).max(); off = (size - (hi-lo)*sc)/2
    img = np.ones((size,size,3)); zb = np.full((size,size), np.inf)
    L = np.array([-0.4,-0.8,0.5]); L/=np.linalg.norm(L)
    for m, col in meshes:
        v = m.vertices@R.T; n = m.face_normals@R.T
        px = (v[:,0]-lo[0])*sc+off[0]; py = size-((v[:,2]-lo[1])*sc+off[1]); d = v[:,1]
        shade = np.clip(n@L,0,1)*0.6+0.4
        for f, s in zip(m.faces, shade):
            x, y, z = px[f], py[f], d[f]
            x0,x1 = int(max(np.floor(x.min()),0)), int(min(np.ceil(x.max()),size-1))
            y0,y1 = int(max(np.floor(y.min()),0)), int(min(np.ceil(y.max()),size-1))
            if x1<x0 or y1<y0: continue
            X,Y = np.meshgrid(np.arange(x0,x1+1)+0.5, np.arange(y0,y1+1)+0.5)
            den = (y[1]-y[2])*(x[0]-x[2])+(x[2]-x[1])*(y[0]-y[2])
            if abs(den)<1e-12: continue
            a = ((y[1]-y[2])*(X-x[2])+(x[2]-x[1])*(Y-y[2]))/den
            b = ((y[2]-y[0])*(X-x[2])+(x[0]-x[2])*(Y-y[2]))/den
            c = 1-a-b; ins = (a>=-1e-6)&(b>=-1e-6)&(c>=-1e-6)
            if not ins.any(): continue
            Z = a*z[0]+b*z[1]+c*z[2]
            sub = zb[y0:y1+1, x0:x1+1]; upd = ins & (Z<sub)
            sub[upd] = Z[upd]; img[y0:y1+1, x0:x1+1][upd] = np.array(col)*s
    return img

if __name__ == "__main__":
    import trimesh, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    h = trimesh.load("files/remote_wall_holder.stl"); c = trimesh.load("files/remote_fit_coupon.stl")
    r = trimesh.creation.box((38.09, 13.34, 151.26)); r.apply_translation((0, 4.25+13.34/2, 3.0+151.26/2))
    fig, axs = plt.subplots(1,3, figsize=(13,6), dpi=110)
    for ax, im, t in zip(axs, [render([(h,(0.3,0.55,0.85)),(r,(0.86,0.86,0.89))],20,200),
                               render([(h,(0.3,0.55,0.85))],25,205),
                               render([(c,(0.95,0.6,0.25))],45,200)],
                         ["with remote", "holder", "fit coupon (10 mm slice)"]):
        ax.imshow(im); ax.axis('off'); ax.set_title(t)
    plt.tight_layout(); plt.savefig("images/preview.png", facecolor='white')
