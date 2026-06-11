"""
Движок для КМД-чертежей в DXF R12.
Использовать вместе с profiles.py.
Все координаты в мм, масштаб 1:1.
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(__file__))

class DXFDrawing:
    def __init__(self, sheet="A1"):
        sizes = {"A4":(210,297),"A3":(297,420),
                 "A2":(420,594),"A1":(594,841),"A0":(841,1189)}
        w,h = sizes.get(sheet,(841,594))
        self.W,self.H = max(w,h),min(w,h)
        self.ents = []

    def _e(self,s): self.ents.append(s)

    def line(self,x1,y1,x2,y2,layer="КОНТУР",lw=0.5):
        self._e(f"  0\nLINE\n  8\n{layer}\n"
                f" 10\n{x1:.3f}\n 20\n{y1:.3f}\n 30\n0.0\n"
                f" 11\n{x2:.3f}\n 21\n{y2:.3f}\n 31\n0.0")

    def rect(self,x,y,w,h,layer="КОНТУР",lw=0.5):
        pts=[(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
        v="".join(f"  0\nVERTEX\n  8\n{layer}\n"
                  f" 10\n{p[0]:.3f}\n 20\n{p[1]:.3f}\n 30\n0.0\n" for p in pts)
        self._e(f"  0\nPOLYLINE\n  8\n{layer}\n 66\n1\n 70\n1\n"
                f" 10\n{x:.3f}\n 20\n{y:.3f}\n 30\n0.0\n"+v+
                f"  0\nSEQEND\n  8\n{layer}")

    def circle(self,cx,cy,r,layer="КОНТУР"):
        self._e(f"  0\nCIRCLE\n  8\n{layer}\n"
                f" 10\n{cx:.3f}\n 20\n{cy:.3f}\n 30\n0.0\n 40\n{r:.3f}")

    def text(self,x,y,s,h=3.5,layer="ТЕКСТЫ",rot=0):
        self._e(f"  0\nTEXT\n  8\n{layer}\n"
                f" 10\n{x:.3f}\n 20\n{y:.3f}\n 30\n0.0\n"
                f" 40\n{h:.2f}\n  1\n{s}\n 50\n{rot:.1f}")

    def hatch(self,x,y,w,h,layer="ШТРИХОВКА",angle=45,sp=3):
        rad=math.radians(angle)
        diag=math.sqrt(w*w+h*h)*1.5
        n=int(diag/sp)+4
        cx,cy=x+w/2,y+h/2
        for i in range(-n,n):
            d=i*sp
            nx2,ny2=-math.sin(rad),math.cos(rad)
            ox,oy=cx+nx2*d,cy+ny2*d
            ux,uy=math.cos(rad),math.sin(rad)
            x1,y1=ox-ux*diag/2,oy-uy*diag/2
            x2,y2=ox+ux*diag/2,oy+uy*diag/2
            pts=[((x1+(x2-x1)*t/30),(y1+(y2-y1)*t/30))
                 for t in range(31)
                 if x-.1<=(x1+(x2-x1)*t/30)<=x+w+.1
                 and y-.1<=(y1+(y2-y1)*t/30)<=y+h+.1]
            if len(pts)>=2:
                self.line(pts[0][0],pts[0][1],pts[-1][0],pts[-1][1],layer,.18)

    def dim_h(self,x1,y,x2,label,off=-12):
        yd=y+off
        self.line(x1,y,x1,yd+2,"РАЗМЕРЫ",.25)
        self.line(x2,y,x2,yd+2,"РАЗМЕРЫ",.25)
        self.line(x1,yd,x2,yd,"РАЗМЕРЫ",.35)
        for sx,dx in[(x1,1),(x2,-1)]:
            self.line(sx,yd,sx+dx*5,yd+1.5,"РАЗМЕРЫ",.35)
            self.line(sx,yd,sx+dx*5,yd-1.5,"РАЗМЕРЫ",.35)
        self.text((x1+x2)/2,yd+2,label,3.0,"РАЗМЕРЫ")

    def dim_v(self,x,y1,y2,label,off=12):
        xd=x+off
        self.line(x,y1,xd-2,y1,"РАЗМЕРЫ",.25)
        self.line(x,y2,xd-2,y2,"РАЗМЕРЫ",.25)
        self.line(xd,y1,xd,y2,"РАЗМЕРЫ",.35)
        for sy,dy in[(y1,1),(y2,-1)]:
            self.line(xd,sy,xd+1.5,sy+dy*5,"РАЗМЕРЫ",.35)
            self.line(xd,sy,xd-1.5,sy+dy*5,"РАЗМЕРЫ",.35)
        self.text(xd+3,(y1+y2)/2,label,3.0,"РАЗМЕРЫ",rot=90)

    def leader(self,x1,y1,x2,y2,label):
        self.line(x1,y1,x2,y2,"РАЗМЕРЫ",.35)
        self.line(x2,y2,x2+50,y2,"РАЗМЕРЫ",.35)
        self.circle(x1,y1,1.5,"РАЗМЕРЫ")
        self.text(x2+2,y2+2,label,3.0)

    def ibeam_cross(self,cx,cy,profile):
        from profiles import IBEAMS
        p=IBEAMS[profile]
        h,b,tw,tf=p["h"],p["b"],p["tw"],p["tf"]
        self.rect(cx-b/2,cy+h/2-tf,b,tf,"СТОЙКА_16Б1")
        self.hatch(cx-b/2,cy+h/2-tf,b,tf,angle=45,sp=2)
        self.rect(cx-b/2,cy-h/2,b,tf,"СТОЙКА_16Б1")
        self.hatch(cx-b/2,cy-h/2,b,tf,angle=45,sp=2)
        self.rect(cx-tw/2,cy-h/2+tf,tw,h-2*tf,"СТОЙКА_16Б1")
        self.hatch(cx-tw/2,cy-h/2+tf,tw,h-2*tf,angle=45,sp=2)

    def ibeam_side(self,xl,yb,height,profile):
        from profiles import IBEAMS
        p=IBEAMS[profile]
        b,tw,tf=p["b"],p["tw"],p["tf"]
        self.rect(xl,yb,b,tf,"СТОЙКА_16Б1")
        self.rect(xl,yb+height-tf,b,tf,"СТОЙКА_16Б1")
        self.rect(xl+b/2-tw/2,yb+tf,tw,height-2*tf,"СТОЙКА_16Б1")

    def frame(self,title=""):
        self.rect(0,0,self.W,self.H,"РАМКА",1.0)
        self.rect(20,5,self.W-25,self.H-10,"РАМКА",.4)
        if title:
            self.text(self.W/2-len(title)*2,self.H-8,title,5.0)

    def title_block(self,num,obj,name,dev="",chk="",sheet="1",total="1",scale="1:1"):
        TX=self.W-190; TY=5; TW=185; TH=55
        self.rect(TX,TY,TW,TH,"РАМКА",.7)
        for dy in[12,22,32,42]:
            self.line(TX,TY+dy,TX+TW,TY+dy,"РАМКА",.4)
        self.line(TX+80,TY,TX+80,TY+TH,"РАМКА",.4)
        self.line(TX+145,TY+32,TX+145,TY+TH,"РАМКА",.4)
        self.text(TX+40,TY+4,num,4.0)
        self.text(TX+40,TY+14,obj,3.0)
        self.text(TX+40,TY+24,name,3.5)
        self.text(TX+112,TY+34,"Стадия: Р",3.0)
        self.text(TX+112,TY+45,f"Лист {sheet}/{total}",3.0)
        self.text(TX+160,TY+34,scale,3.0)
        if dev: self.text(TX+3,TY+34,f"Разраб. {dev}",2.5)
        if chk: self.text(TX+3,TY+45,f"Провер. {chk}",2.5)

    def spec_table(self,rows,x=10,y=10,w=580):
        cols=[x+3,x+28,x+120,x+280,x+345,x+400,x+450,x+510]
        heads=["Поз.","Марка","Наименование","ГОСТ",
               "L мм","Масса кг","Кол.","Примечание"]
        rh=12; TH=(len(rows)+2)*rh
        self.rect(x,y,w,TH,"РАМКА",.7)
        self.rect(x,y+TH-rh,w,rh,"РАМКА",.5)
        for cx,ch in zip(cols,heads):
            self.text(cx,y+TH-rh+3,ch,2.8)
            self.line(cx-1,y,cx-1,y+TH,"РАМКА",.3)
        self.line(x,y+TH-2*rh,x+w,y+TH-2*rh,"РАМКА",.3)
        for ri,row in enumerate(rows):
            ry=y+TH-rh*(ri+2)
            self.line(x,ry,x+w,ry,"РАМКА",.3)
            for val,cx in zip(row,cols):
                self.text(cx,ry+3,str(val),2.8)

    def save(self,path):
        LAYERS=[("0",7,"CONTINUOUS"),("КОНТУР",2,"CONTINUOUS"),
                ("РАЗМЕРЫ",3,"CONTINUOUS"),("ОСИ",1,"CENTER"),
                ("ШТРИХОВКА",8,"CONTINUOUS"),("ТЕКСТЫ",7,"CONTINUOUS"),
                ("РАМКА",7,"CONTINUOUS"),("СВАРКА",1,"CONTINUOUS"),
                ("НЕВИДИМЫЕ",8,"DASHED"),("СТОЙКА_16Б1",4,"CONTINUOUS"),
                ("ПАНЕЛЬ",5,"CONTINUOUS")]
        out=["  0\nSECTION\n  2\nHEADER",
             "  9\n$ACADVER\n  1\nAC1009",
             "  9\n$INSUNITS\n 70\n4","  0\nENDSEC",
             "  0\nSECTION\n  2\nTABLES",
             "  0\nTABLE\n  2\nLTYPE\n 70\n3",
             "  0\nLTYPE\n  2\nCONTINUOUS\n 70\n64\n  3\nSolid\n 72\n65\n 73\n0\n 40\n0.0",
             "  0\nLTYPE\n  2\nDASHED\n 70\n64\n  3\nDashed\n 72\n65\n 73\n0\n 40\n0.0",
             "  0\nLTYPE\n  2\nCENTER\n 70\n64\n  3\nCenter\n 72\n65\n 73\n0\n 40\n0.0",
             "  0\nENDTAB",
             f"  0\nTABLE\n  2\nLAYER\n 70\n{len(LAYERS)}"]
        for n,c,lt in LAYERS:
            out.append(f"  0\nLAYER\n  2\n{n}\n 70\n64\n 62\n{c}\n  6\n{lt}")
        out+=["  0\nENDTAB",
              "  0\nTABLE\n  2\nSTYLE\n 70\n1",
              "  0\nSTYLE\n  2\nSTANDARD\n 70\n0\n 40\n0.0\n 41\n1.0\n"
              " 42\n0.2\n 50\n0.0\n 71\n0\n  4\ntxt\n  1\n",
              "  0\nENDTAB","  0\nENDSEC",
              "  0\nSECTION\n  2\nENTITIES"]
        out.extend(self.ents)
        out+=["  0\nENDSEC","  0\nEOF"]
        with open(path,'w',encoding='utf-8') as f:
            f.write('\n'.join(out))
        print(f"Сохранено: {path}")
