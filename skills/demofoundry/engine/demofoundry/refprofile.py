"""Measure a product screenshot into JSON, instead of reading the image into an agent's context.

  python -m demofoundry refprofile <shot.png>                         # one file, prints JSON
  python -m demofoundry refprofile --all "<glob>" --out <file.json>   # batch

Measures implementation-independent quantities: card bounding box (sub-pixel), corner radius,
border colour and width, fill, title-rail icon / text ink boxes and stroke width, ink bands inside
the card (structure), dark content blocks, main colour clusters. Lengths are logical px
(image px ÷ --scale, default 2 for retina shots).

--threshold is the luminance where the card edge is found (default 16.5, set for dark UIs
on a near-black canvas); light UIs need their own value.
"""
import sys, os, json, glob, zlib, struct
import numpy as np


# ───────────────────────── minimal PNG decoder (8-bit RGB / RGBA), enough for UI sampling ─────────────────────────
def load(path):
    raw = open(path,'rb').read()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n', 'not png'
    pos, idat, meta = 8, [], {}
    while pos < len(raw):
        ln, = struct.unpack('>I', raw[pos:pos+4]); typ = raw[pos+4:pos+8]
        data = raw[pos+8:pos+8+ln]; pos += 12 + ln
        if typ == b'IHDR':
            w,h,bd,ct,_,_,il = struct.unpack('>IIBBBBB', data)
            meta = dict(w=w,h=h,bd=bd,ct=ct,il=il)
        elif typ == b'IDAT': idat.append(data)
        elif typ == b'IEND': break
    assert meta['bd']==8 and meta['ct'] in (2,6) and meta['il']==0, meta
    ch = 3 if meta['ct']==2 else 4
    w,h = meta['w'], meta['h']
    buf = np.frombuffer(zlib.decompress(b''.join(idat)), dtype=np.uint8)
    stride = w*ch
    out = np.zeros((h, stride), dtype=np.uint8)
    prev = np.zeros(stride, dtype=np.uint8)
    for y in range(h):
        off = y*(stride+1); ft = buf[off]
        line = buf[off+1:off+1+stride].astype(np.int32).copy()
        if ft == 1:
            for i in range(ch, stride): line[i] = (line[i] + line[i-ch]) & 255
        elif ft == 2:
            line = (line + prev) & 255
        elif ft == 3:
            for i in range(stride):
                a = line[i-ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif ft == 4:
            for i in range(stride):
                a = int(line[i-ch]) if i >= ch else 0
                b = int(prev[i]); cc = int(prev[i-ch]) if i >= ch else 0
                p = a+b-cc; pa,pb,pc = abs(p-a),abs(p-b),abs(p-cc)
                pr = a if (pa<=pb and pa<=pc) else (b if pb<=pc else cc)
                line[i] = (line[i] + pr) & 255
        line = line.astype(np.uint8)
        out[y] = line; prev = line
    return out.reshape(h, w, ch)[:, :, :3].astype(np.float64)

def lum(a):  # Rec.709
    return 0.2126*a[...,0] + 0.7152*a[...,1] + 0.0722*a[...,2]

def edge(prof, t, from_start=True):
    """Sub-pixel edge: linear interpolation where the profile crosses t."""
    n = len(prof)
    rng = range(1, n) if from_start else range(n-1, 0, -1)
    for i in rng:
        a, b = (prof[i-1], prof[i]) if from_start else (prof[i], prof[i-1])
        if a <= t < b:
            f = (t-a)/(b-a)
            return (i-1+f) if from_start else (i-f)
    return float('nan')



THRESHOLD = 16.5
hexs = lambda c: '#%02x%02x%02x' % tuple(int(round(v)) for v in c)
SCALE = 2.0
R2   = lambda v: round(float(v)/SCALE, 2)      # image px → logical px

def profile(path):
    a = load(path); L = lum(a); H, W = L.shape
    out = {'file': path, 'image_px': [W, H]}

    rm, cm = np.median(L,axis=1), np.median(L,axis=0); T = THRESHOLD
    cy0,cy1 = edge(rm,T,True), edge(rm,T,False)
    cx0,cx1 = edge(cm,T,True), edge(cm,T,False)

    # ---- what is this image? ----
    bad = any(np.isnan(v) for v in (cx0,cx1,cy0,cy1))
    # degenerate: edges reversed or nearly touching (real case: a horizontal wire measured as a -510×2.9 "card")
    if not bad and ((cx1-cx0) < 20 or (cy1-cy0) < 20):
        bad = True
    if not bad:
        fills = (cx1-cx0) > 0.95*W and (cy1-cy0) > 0.95*H
    if bad or fills:
        # close-up crop: no whole card in the image (port, wire, handle, toolbar close-up)
        out['mode'] = 'crop'
        ink = L > (np.median(L) + 25)
        ys, xs = np.where(ink)
        if len(ys):
            out['object'] = {'x':R2(xs.min()),'y':R2(ys.min()),
                             'w':R2(xs.max()-xs.min()+1),'h':R2(ys.max()-ys.min()+1)}
            px = a[ys.min():ys.max()+1, xs.min():xs.max()+1].reshape(-1,3)
            q = (px//16*16).astype(int)
            k2,c2 = np.unique(q,axis=0,return_counts=True); o=np.argsort(-c2)[:6]
            out['colors'] = [{'hex':hexs(k2[i]),'pct':round(100*c2[i]/len(px),1)} for i in o]
        out['note'] = 'close-up crop: no whole card; object bounding box and main colours only'
        return out
    out['mode'] = 'card'
    CW,CH = cx1-cx0, cy1-cy0
    ix0,iy0 = int(round(cx0)), int(round(cy0))
    out['card'] = {'w':R2(CW),'h':R2(CH),'x_in_image':R2(cx0),'y_in_image':R2(cy0)}

    mid = int((cy0+cy1)/2)
    inner_px = L[iy0+6:int(cy1)-6, ix0+6:int(cx1)-6]
    spread = float(np.std(inner_px))
    media = spread > 22          # media filling the card → large variance inside
    out['content'] = 'media' if media else 'flat'
    fill = np.median(a[mid, ix0+30:ix0+80], axis=0)
    prof = L[mid, ix0-4:ix0+10]
    bw   = sum(1 for v in prof if v > lum(fill)+6)
    ys = np.arange(int(cy0)+1, min(int(cy0)+150, H-1)); ins=[]
    for y in ys:
        e = edge(L[y, ix0-6:ix0+200], T, True)
        if not np.isnan(e): ins.append(ix0-6+e-cx0)
    ins = np.array(ins)
    rad = (ys-cy0)[int(np.argmin(np.abs(ins-0.5)))] if len(ins) else float('nan')
    shell = {'border':hexs(a[mid, ix0+1]), 'border_w':R2(bw), 'radius':R2(rad)}
    if media:
        # card filled by media: the fill is the photo itself and meaningless; measure the border on the outer 1-3px,
        # against the canvas ground outside the card rather than against a "fill"
        ring = a[iy0+1:iy0+4, ix0+6:int(cx1)-6].reshape(-1,3)
        shell['fill'] = None
        shell['fill_note'] = 'card filled by media; no usable fill colour'
        shell['border_from_ring'] = hexs(np.median(ring,axis=0))
        shell['inner_stddev'] = round(spread,1)
    else:
        shell['fill'] = hexs(fill)
        # the mid-line sample can land inside a sub-region (real case: a minimap's mid-line hit the viewport frame).
        # sample a strip just inside the top edge too; when they disagree, say so and let the reader decide.
        ty0 = iy0 + bw + 4                        # bw = border width (image px); sample past the border
        top = np.median(a[ty0:ty0+6, ix0+30:int(cx1)-30].reshape(-1,3), axis=0)
        shell['fill_top_strip'] = hexs(top)
        if np.abs(top - fill).max() > 4:
            shell['fill_note'] = 'mid-line and top-strip fills disagree: the mid-line probably hit a sub-region; the card fill is likely fill_top_strip'
    out['shell'] = shell

    BG = lum(fill); FG = 244.0; TH = (BG+FG)/2
    out['ink_threshold'] = round(TH,1)

    def substem(y0,y1,x0,x1):
        ws=[]
        for y in range(max(y0,0), min(y1,H)):
            row = L[y, x0:x1]; on = row>TH; i=0; n=len(row)
            while i<n:
                if on[i]:
                    j=i
                    while j+1<n and on[j+1]: j+=1
                    if j-i+1>=2 and i>0 and j+1<n:
                        l = i-1+(TH-row[i-1])/(row[i]-row[i-1]) if row[i]!=row[i-1] else i-.5
                        r = j+1-(TH-row[j+1])/(row[j]-row[j+1]) if row[j]!=row[j+1] else j+.5
                        ws.append(r-l)
                    i=j+1
                else: i+=1
        return R2(np.median(ws)) if ws else None

    # title rail (above the card)
    if iy0 > 12:
        tb = L[:iy0-3, :]
        on = tb.max(axis=0) > TH
        segs,run=[],None
        for i,v in enumerate(on):
            if v and run is None: run=i
            elif not v and run is not None: segs.append([run,i-1]); run=None
        if run is not None: segs.append([run,len(on)-1])
        if segs:
            m=[segs[0][:]]
            for s in segs[1:]:
                if s[0]-m[-1][1] <= 7: m[-1][1]=s[1]
                else: m.append(s[:])
            def vext(x0,x1):
                r=np.where(tb[:, x0:x1+1].max(axis=1)>TH)[0]
                return (int(r[0]), int(r[-1])) if len(r) else (0,0)
            icon=m[0]; it,ib = vext(*icon)
            rail={'icon':{'left_from_card':R2(icon[0]-cx0),'w':R2(icon[1]-icon[0]+1),
                          'h':R2(ib-it+1),'bottom_above_card':R2(cy0-ib)}}
            if len(m)>1:
                txt=(m[1][0], m[-1][1]); tt,tb2 = vext(*txt)
                rail['text']={'left_from_card':R2(txt[0]-cx0),'ink_w':R2(txt[1]-txt[0]+1),
                              'ink_h':R2(tb2-tt+1),'bottom_above_card':R2(cy0-tb2),
                              'gap_from_icon':R2(txt[0]-icon[1]-1),
                              'color':hexs(np.percentile(a[tt:tb2+1, txt[0]:txt[1]+1].reshape(-1,3),99,axis=0)),
                              'stem':substem(tt+2,tb2-2,txt[0],txt[1])}
            out['rail']=rail

    # structure inside the card: horizontal / vertical bands with ink
    inner = L[iy0+4:int(cy1)-4, ix0+4:int(cx1)-4]
    def bands(mask, axis):
        v = mask.sum(axis=axis) > 0
        segs,run=[],None
        for i,x in enumerate(v):
            if x and run is None: run=i
            elif not x and run is not None: segs.append([R2(run+4), R2(i-1+4)]); run=None
        if run is not None: segs.append([R2(run+4), R2(len(v)-1+4)])
        return segs
    ink = inner > TH
    out['bands'] = {'rows': bands(ink,1)[:24], 'cols_count': len(bands(ink,0))}

    # dark content blocks: areas clearly off the fill but darker than text (minimap blocks, placeholders, dividers…).
    # the bands above only catch bright ink (threshold set for text) and would miss these. Skipped for media cards.
    if not media:
        ty0 = iy0 + bw + 4
        ref_l = lum(np.median(a[ty0:ty0+6, ix0+30:int(cx1)-30].reshape(-1,3), axis=0))
        inner_l = L[iy0+4:int(cy1)-4, ix0+4:int(cx1)-4]
        mask = np.abs(inner_l - ref_l) > 10
        mask &= inner_l < TH                      # bright ink is covered by bands
        seen = np.zeros_like(mask); blocks = []
        hh, ww = mask.shape
        for y0_ in range(hh):
            row = mask[y0_]
            if not row.any(): continue
            for x0_ in np.where(row & ~seen[y0_])[0]:
                if seen[y0_, x0_]: continue
                stack=[(y0_,x0_)]; seen[y0_,x0_]=True; ys=[]; xs=[]
                while stack:
                    cy_,cx_=stack.pop(); ys.append(cy_); xs.append(cx_)
                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny,nx=cy_+dy,cx_+dx
                        if 0<=ny<hh and 0<=nx<ww and mask[ny,nx] and not seen[ny,nx]:
                            seen[ny,nx]=True; stack.append((ny,nx))
                if len(ys) < 40: continue
                bx0,bx1,by0,by1 = min(xs),max(xs),min(ys),max(ys)
                bw,bh = bx1-bx0+1, by1-by0+1
                fill_ratio = len(ys)/(bw*bh)
                blocks.append({'x':R2(bx0+4),'y':R2(by0+4),'w':R2(bw),'h':R2(bh),
                  'kind':'frame' if fill_ratio < 0.35 else 'solid',
                  # colour from this component's own pixels: a frame's bounding box often contains other blocks
                  'color':hexs(np.median(a[np.array(ys)+iy0+4, np.array(xs)+ix0+4],axis=0))})
                if len(blocks) >= 40: break
            if len(blocks) >= 40: break
        out['blocks'] = sorted(blocks, key=lambda b:(b['y'],b['x']))

    # main colour clusters inside the card (quantised to 16 levels)
    px = a[iy0+4:int(cy1)-4, ix0+4:int(cx1)-4].reshape(-1,3)
    q = (px//16*16).astype(int)
    keys,counts = np.unique(q, axis=0, return_counts=True)
    order = np.argsort(-counts)[:8]
    out['colors'] = [{'hex':hexs(keys[i]), 'pct':round(100*counts[i]/len(px),1)} for i in order]
    return out

def main(argv=None):
    global SCALE, THRESHOLD
    args = list(sys.argv[1:] if argv is None else argv)
    for flag in ('--scale', '--threshold'):
        if flag in args:
            i = args.index(flag); v = float(args[i + 1]); args = args[:i] + args[i + 2:]
            if flag == '--scale': SCALE = v
            else: THRESHOLD = v
    if args and args[0] == '--all':
        out = 'ref-profile.json'
        if '--out' in args:
            i = args.index('--out'); out = args[i + 1]; args = args[:i] + args[i + 2:]
        if len(args) < 2:
            sys.exit('--all needs a glob, e.g. "mold/evidence/*/screenshots/*.png"')
        paths = sorted(glob.glob(args[1]))
        if not paths:
            sys.exit("no images match: %s" % args[1])
        res = {}
        for p in paths:
            try: res[p] = profile(p)
            except Exception as e: res[p] = {'file': p, 'error': str(e)}
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(res, f, ensure_ascii=False, indent=1)
        ok = sum(1 for v in res.values() if 'error' not in v)
        print("measured %d images (%d ok) → %s" % (len(res), ok, out))
    elif args:
        print(json.dumps(profile(args[0]), ensure_ascii=False, indent=1))
    else:
        sys.exit(__doc__)
