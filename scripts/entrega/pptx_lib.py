"""Escritor mínimo de PresentationML (16:9) con la biblioteca estándar.

Genera tema, patrón, diseños, diapositivas con notas del orador, tablas nativas e imágenes (PNG con SVG editable opcional).
"""
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED

EMU = 914400
W_IN, H_IN = 13.333, 7.5
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

NEGRO, TINTA, LIMA, VERDE, GRIS, SUAVE, BLANCO = "0B0B0B", "141414", "C1F11D", "2F7D00", "6B7280", "F3F6EC", "FFFFFF"


def e(v):
    return int(round(v * EMU))


def esc(t):
    return escape(t)


# ----------------------------------------------------------------------------- texto
def R(texto, size=16, bold=False, color=TINTA, italic=False, mono=False):
    f = '<a:latin typeface="Courier New"/><a:cs typeface="Courier New"/>' if mono else ""
    return (f'<a:r><a:rPr lang="es-PE" sz="{int(size * 100)}" b="{int(bold)}" i="{int(italic)}" dirty="0">'
            f'<a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{f}</a:rPr><a:t>{esc(texto)}</a:t></a:r>')


def P(contenido, size=16, bold=False, color=TINTA, align="l", after=0, before=0, line=None, mono=False, italic=False):
    """Párrafo. contenido: texto o lista de (texto, {opciones}) para varios formatos."""
    if isinstance(contenido, str):
        runs = R(contenido, size, bold, color, italic, mono)
    else:
        runs = "".join(R(t, **{**dict(size=size, bold=bold, color=color, mono=mono, italic=italic), **o}) for t, o in contenido)
    ls = f'<a:lnSpc><a:spcPct val="{int(line * 1000)}"/></a:lnSpc>' if line else ""
    return (f'<a:p><a:pPr algn="{align}">{ls}<a:spcBef><a:spcPts val="{int(before * 100)}"/></a:spcBef>'
            f'<a:spcAft><a:spcPts val="{int(after * 100)}"/></a:spcAft></a:pPr>{runs}'
            f'<a:endParaRPr lang="es-PE" sz="{int(size * 100)}" dirty="0"/></a:p>')


def relleno(c):
    return f'<a:solidFill><a:srgbClr val="{c}"/></a:solidFill>' if c else "<a:noFill/>"


def borde(c, w=1.0, dash=None):
    if not c:
        return "<a:ln><a:noFill/></a:ln>"
    d = f'<a:prstDash val="{dash}"/>' if dash else ""
    return f'<a:ln w="{int(w * 12700)}"><a:solidFill><a:srgbClr val="{c}"/></a:solidFill>{d}</a:ln>'


class Diapositiva:
    def __init__(self, diseno, titulo=None, notas=""):
        self.diseno, self.notas = diseno, notas
        self.formas, self.rels, self._id = [], [], 1   # rels: (rid, tipo, destino)
        if titulo:
            self.titulo(titulo)

    def nid(self):
        self._id += 1
        return self._id

    # ---- elementos
    def titulo(self, texto):
        i = self.nid()
        self.formas.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="Título"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>'
            f'<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr lang="es-PE" dirty="0"/><a:t>{esc(texto)}</a:t></a:r></a:p></p:txBody></p:sp>')

    def numero(self):
        i = self.nid()
        self.formas.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="Número de diapositiva"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="sldNum" sz="quarter" idx="12"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>'
            '<a:p><a:fld id="{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}" type="slidenum"><a:rPr lang="es-PE"/><a:t>‹#›</a:t></a:fld>'
            '<a:endParaRPr lang="es-PE"/></a:p></p:txBody></p:sp>')

    def forma(self, x, y, w, h, parrafos=(), relleno_c=None, linea=None, lw=1.0, geom="roundRect", adj=12000, anchor="ctr",
              ins=(0.12, 0.06, 0.12, 0.06), nombre="Forma", texto_caja=False, dash=None):
        i = self.nid()
        av = f'<a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst>' if geom == "roundRect" else "<a:avLst/>"
        tx = ""
        if parrafos:
            tx = (f'<p:txBody><a:bodyPr wrap="square" lIns="{e(ins[0])}" tIns="{e(ins[1])}" rIns="{e(ins[2])}" bIns="{e(ins[3])}" '
                  f'anchor="{anchor}" rtlCol="0"><a:noAutofit/></a:bodyPr><a:lstStyle/>{"".join(parrafos)}</p:txBody>')
        else:
            tx = '<p:txBody><a:bodyPr rtlCol="0" anchor="ctr"/><a:lstStyle/><a:p><a:endParaRPr lang="es-PE"/></a:p></p:txBody>'
        cnv = '<p:cNvSpPr txBox="1"/>' if texto_caja else "<p:cNvSpPr/>"
        self.formas.append(
            f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{esc(nombre)} {i}"/>{cnv}<p:nvPr/></p:nvSpPr><p:spPr>'
            f'<a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm><a:prstGeom prst="{geom}">{av}</a:prstGeom>'
            f'{relleno(relleno_c)}{borde(linea, lw, dash)}</p:spPr>{tx}</p:sp>')

    def texto(self, x, y, w, h, parrafos, anchor="t", nombre="Texto", ins=(0, 0, 0, 0)):
        self.forma(x, y, w, h, parrafos, None, None, geom="rect", anchor=anchor, ins=ins, nombre=nombre, texto_caja=True)

    def circulo(self, x, y, d, texto, relleno_c=LIMA, color=NEGRO, size=16, linea=None):
        self.forma(x, y, d, d, [P(texto, size, True, color, "ctr")], relleno_c, linea, geom="ellipse", ins=(0, 0, 0, 0), nombre="Círculo")

    def linea(self, x1, y1, x2, y2, color=NEGRO, w=2.0, flecha=True, dash=None):
        i = self.nid()
        fx, fy = int(x2 < x1), int(y2 < y1)
        d = f'<a:prstDash val="{dash}"/>' if dash else ""
        fin = '<a:tailEnd type="triangle" w="med" len="med"/>' if flecha else ""
        self.formas.append(
            f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{i}" name="Conector {i}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr><p:spPr>'
            f'<a:xfrm flipH="{fx}" flipV="{fy}"><a:off x="{e(min(x1, x2))}" y="{e(min(y1, y2))}"/><a:ext cx="{e(abs(x2 - x1))}" cy="{e(abs(y2 - y1))}"/></a:xfrm>'
            f'<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:ln w="{int(w * 12700)}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill>{d}{fin}</a:ln>'
            '</p:spPr></p:cxnSp>')

    def imagen(self, png, svg, x, y, w, h, descr):
        i = self.nid()
        rp = f"rId{len(self.rels) + 2}"
        self.rels.append((rp, "image", png))
        ext = ""
        if svg:
            rs = f"rId{len(self.rels) + 2}"
            self.rels.append((rs, "image", svg))
            ext = ('<a:extLst><a:ext uri="{96DAC541-7B7A-43D3-8B79-37D633B846F1}"><asvg:svgBlip '
                   'xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" '
                   f'r:embed="{rs}"/></a:ext></a:extLst>')
        self.formas.append(
            f'<p:pic><p:nvPicPr><p:cNvPr id="{i}" name="Imagen {i}" descr="{esc(descr)}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            f'<p:blipFill><a:blip r:embed="{rp}">{ext}</a:blip><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')

    def tabla(self, x, y, anchos, filas, alto_fila=0.5, size=14, encabezado=True, fill_enc=NEGRO, color_enc=LIMA, mono_cols=(), negrita_col0=True):
        i = self.nid()
        total = sum(anchos)
        g = "".join(f'<a:gridCol w="{e(a)}"/>' for a in anchos)
        trs = ""
        for n, fila in enumerate(filas):
            es_enc = encabezado and n == 0
            tcs = ""
            for j, cel in enumerate(fila):
                if es_enc:
                    col, b, fondo = color_enc, True, fill_enc
                else:
                    col, b, fondo = TINTA, negrita_col0 and j == 0, (SUAVE if n % 2 == 0 else BLANCO)
                lineas = cel if isinstance(cel, list) else [cel]
                ps = "".join(P(t, size, b, col, mono=(j in mono_cols and not es_enc)) for t in lineas)
                ln = ('<a:lnL w="0"><a:noFill/></a:lnL><a:lnR w="0"><a:noFill/></a:lnR><a:lnT w="0"><a:noFill/></a:lnT>'
                      '<a:lnB w="12700"><a:solidFill><a:srgbClr val="D1D5DB"/></a:solidFill></a:lnB>')
                tcs += (f'<a:tc><a:txBody><a:bodyPr/><a:lstStyle/>{ps}</a:txBody>'
                        f'<a:tcPr marL="{e(0.12)}" marR="{e(0.1)}" marT="{e(0.05)}" marB="{e(0.05)}" anchor="ctr">{ln}{relleno(fondo)}</a:tcPr></a:tc>')
            trs += f'<a:tr h="{e(alto_fila)}">{tcs}</a:tr>'
        self.formas.append(
            f'<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id="{i}" name="Tabla {i}"/><p:cNvGraphicFramePr><a:graphicFrameLocks noGrp="1"/></p:cNvGraphicFramePr><p:nvPr/></p:nvGraphicFramePr>'
            f'<p:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(total)}" cy="{e(alto_fila * len(filas))}"/></p:xfrm>'
            f'<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/table"><a:tbl><a:tblPr firstRow="{int(encabezado)}" bandRow="1"/>'
            f'<a:tblGrid>{g}</a:tblGrid>{trs}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>')

    # ---- XML
    def xml(self):
        return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld {NS}><p:cSld><p:spTree>'
                '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
                '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>' + "".join(self.formas) +
                '</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')

    def xml_notas(self):
        ps = "".join(f'<a:p><a:r><a:rPr lang="es-PE" dirty="0"/><a:t>{esc(l)}</a:t></a:r></a:p>' for l in self.notas.split("\n"))
        return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:notes {NS}><p:cSld><p:spTree>'
                '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
                '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
                '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Imagen de diapositiva 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr>'
                '<p:nvPr><p:ph type="sldImg"/></p:nvPr></p:nvSpPr><p:spPr/></p:sp>'
                '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Marcador de notas 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
                '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr><p:spPr/>'
                f'<p:txBody><a:bodyPr/><a:lstStyle/>{ps}</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>')


# ----------------------------------------------------------------------------- piezas fijas del paquete
def tema(nombre, fuente="Arial"):
    cols = dict(dk1=NEGRO, lt1=BLANCO, dk2=TINTA, lt2=SUAVE, accent1=LIMA, accent2=VERDE, accent3=GRIS, accent4="9BD60F",
                accent5="FDE68A", accent6="0A7C86", hlink="2F7D00", folHlink="6B7280")
    cx = "".join(f'<a:{k}><a:srgbClr val="{v}"/></a:{k}>' for k, v in cols.items())
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="{nombre}">'
            f'<a:themeElements><a:clrScheme name="{nombre}">{cx}</a:clrScheme>'
            f'<a:fontScheme name="{nombre}"><a:majorFont><a:latin typeface="{fuente}"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
            f'<a:minorFont><a:latin typeface="{fuente}"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
            '<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
            '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
            '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
            '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
            '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
            '</a:fmtScheme></a:themeElements></a:theme>')


def _marcador(i, nombre, tipo, x, y, w, h, extra_lst="", idx=None, texto="", tamano=None, parrafo=""):
    ph = f'<p:ph type="{tipo}"' + (f' idx="{idx}"' if idx is not None else "") + (f' sz="{tamano}"' if tamano else "") + "/>"
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{i}" name="{nombre}"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr>{ph}</p:nvPr></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{e(x)}" y="{e(y)}"/><a:ext cx="{e(w)}" cy="{e(h)}"/></a:xfrm></p:spPr>'
            f'<p:txBody><a:bodyPr lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:noAutofit/></a:bodyPr><a:lstStyle>{extra_lst}</a:lstStyle>'
            f'{parrafo or "<a:p><a:endParaRPr lang=\"es-PE\"/></a:p>"}</p:txBody></p:sp>')


GRP = ('<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
       '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>')


def patron(n_disenos):
    titulo = _marcador(2, "Título", "title", 0.6, 0.38, 12.13, 0.85, parrafo='<a:p><a:r><a:rPr lang="es-PE"/><a:t>Haga clic para modificar el título</a:t></a:r></a:p>')
    numero = _marcador(3, "Número de diapositiva", "sldNum", 12.0, 7.02, 0.73, 0.3, idx=12, tamano="quarter",
                       parrafo='<a:p><a:fld id="{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}" type="slidenum"><a:rPr lang="es-PE"/><a:t>‹#›</a:t></a:fld><a:endParaRPr lang="es-PE"/></a:p>',
                       extra_lst='<a:lvl1pPr algn="r"><a:defRPr sz="1100"><a:solidFill><a:srgbClr val="6B7280"/></a:solidFill></a:defRPr></a:lvl1pPr>')
    ids = "".join(f'<p:sldLayoutId id="{2147483649 + i}" r:id="rId{i + 1}"/>' for i in range(n_disenos))
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
            f'<p:spTree>{GRP}{titulo}{numero}</p:spTree></p:cSld>'
            '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            f'<p:sldLayoutIdLst>{ids}</p:sldLayoutIdLst>'
            '<p:txStyles><p:titleStyle><a:lvl1pPr algn="l"><a:lnSpc><a:spcPct val="90000"/></a:lnSpc><a:defRPr sz="3200" b="1"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
            '<a:latin typeface="+mj-lt"/><a:ea typeface="+mj-ea"/><a:cs typeface="+mj-cs"/></a:defRPr></a:lvl1pPr></p:titleStyle>'
            '<p:bodyStyle><a:lvl1pPr marL="0" indent="0" algn="l"><a:buNone/><a:defRPr sz="1800"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill><a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr></p:bodyStyle>'
            '<p:otherStyle><a:defPPr><a:defRPr lang="es-PE"/></a:defPPr><a:lvl1pPr marL="0" algn="l"><a:defRPr sz="1800"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill><a:latin typeface="+mn-lt"/></a:defRPr></a:lvl1pPr></p:otherStyle></p:txStyles></p:sldMaster>')


def diseno(nombre, oscuro=False, con_titulo=True, pie=True):
    fondo = f'<p:bg><p:bgPr><a:solidFill><a:srgbClr val="{NEGRO}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>' if oscuro else ""
    col_t = BLANCO if oscuro else NEGRO
    sp = ""
    if con_titulo:
        sp += _marcador(2, "Título", "title", 0.6, 0.38, 12.13, 0.85,
                        extra_lst=f'<a:lvl1pPr><a:defRPr sz="3200" b="1"><a:solidFill><a:srgbClr val="{col_t}"/></a:solidFill></a:defRPr></a:lvl1pPr>',
                        parrafo='<a:p><a:r><a:rPr lang="es-PE"/><a:t>Haga clic para modificar el título</a:t></a:r></a:p>')
    if pie:
        col_n = "9CA3AF" if oscuro else "6B7280"
        sp += _marcador(3, "Número de diapositiva", "sldNum", 12.0, 7.02, 0.73, 0.3, idx=12, tamano="quarter",
                        parrafo='<a:p><a:fld id="{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}" type="slidenum"><a:rPr lang="es-PE"/><a:t>‹#›</a:t></a:fld><a:endParaRPr lang="es-PE"/></a:p>',
                        extra_lst=f'<a:lvl1pPr algn="r"><a:defRPr sz="1100"><a:solidFill><a:srgbClr val="{col_n}"/></a:solidFill></a:defRPr></a:lvl1pPr>')
        sp += (f'<p:sp><p:nvSpPr><p:cNvPr id="4" name="Pie de página"/><p:cNvSpPr txBox="1"/><p:nvPr userDrawn="1"/></p:nvSpPr><p:spPr><a:xfrm><a:off x="{e(0.6)}" y="{e(7.02)}"/>'
               f'<a:ext cx="{e(8)}" cy="{e(0.3)}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr><p:txBody><a:bodyPr wrap="square" lIns="0" tIns="0" rIns="0" bIns="0" anchor="ctr"><a:noAutofit/></a:bodyPr>'
               f'<a:lstStyle/>{P("inDrive Lab · Base de Datos · Universidad Norbert Wiener", 11, False, col_n)}</p:txBody></p:sp>')
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout {NS} preserve="1" userDrawn="1"><p:cSld name="{nombre}">{fondo}'
            f'<p:spTree>{GRP}{sp}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>')


def patron_notas():
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:notesMaster {NS}><p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>{GRP}'
            '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Imagen de diapositiva 1"/><p:cNvSpPr><a:spLocks noGrp="1" noRot="1" noChangeAspect="1"/></p:cNvSpPr><p:nvPr><p:ph type="sldImg" idx="2"/></p:nvPr></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="685800" y="1143000"/><a:ext cx="5486400" cy="3086100"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln w="12700"><a:solidFill><a:prstClr val="black"/></a:solidFill></a:ln></p:spPr></p:sp>'
            '<p:sp><p:nvSpPr><p:cNvPr id="3" name="Marcador de notas 2"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr><p:nvPr><p:ph type="body" sz="quarter" idx="3"/></p:nvPr></p:nvSpPr>'
            '<p:spPr><a:xfrm><a:off x="685800" y="4400550"/><a:ext cx="5486400" cy="3600450"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
            '<p:txBody><a:bodyPr vert="horz" lIns="91440" tIns="45720" rIns="91440" bIns="45720" rtlCol="0"/><a:lstStyle/><a:p><a:pPr lvl="0"/><a:r><a:rPr lang="es-PE"/><a:t>Notas del orador</a:t></a:r></a:p></p:txBody></p:sp>'
            '</p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
            '<p:notesStyle><a:lvl1pPr marL="0" algn="l" defTabSz="914400" rtl="0" eaLnBrk="1" latinLnBrk="0" hangingPunct="1"><a:defRPr sz="1200" kern="1200"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill>'
            '<a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl1pPr></p:notesStyle></p:notesMaster>')


def rels(lista):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + "".join(f'<Relationship Id="{i}" Type="{t}" Target="{d}"/>' for i, t, d in lista) + "</Relationships>")


def escribir(ruta, diapositivas, disenos, titulo, autor, medios):
    """diapositivas: lista de Diapositiva (cada una indica el índice de su diseño). medios: {nombre_en_paquete: bytes}."""
    n = len(diapositivas)
    ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
          '<Default Extension="png" ContentType="image/png"/><Default Extension="svg" ContentType="image/svg+xml"/>'
          '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
          '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
          '<Override PartName="/ppt/notesMasters/notesMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesMaster+xml"/>'
          '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
          '<Override PartName="/ppt/theme/theme2.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
          '<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>'
          '<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>'
          '<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>'
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
          '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>']
    for i in range(len(disenos)):
        ct.append(f'<Override PartName="/ppt/slideLayouts/slideLayout{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>')
    for i in range(n):
        ct.append(f'<Override PartName="/ppt/slides/slide{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
        ct.append(f'<Override PartName="/ppt/notesSlides/notesSlide{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"/>')
    ct.append("</Types>")
    with ZipFile(ruta, "w", ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(ct))
        z.writestr("_rels/.rels", rels([("rId1", REL + "/officeDocument", "ppt/presentation.xml"),
                                        ("rId2", "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties", "docProps/core.xml"),
                                        ("rId3", REL + "/extended-properties", "docProps/app.xml")]))
        z.writestr("docProps/core.xml",
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                   'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                   f'<dc:title>{esc(titulo)}</dc:title><dc:creator>{esc(autor)}</dc:creator></cp:coreProperties>')
        z.writestr("docProps/app.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
                                       f'<Application>Microsoft Office PowerPoint</Application><Slides>{n}</Slides><Notes>{n}</Notes></Properties>')
        pres_rels = [("rId1", REL + "/slideMaster", "slideMasters/slideMaster1.xml"), ("rId2", REL + "/notesMaster", "notesMasters/notesMaster1.xml")]
        pres_rels += [(f"rId{i + 3}", REL + "/slide", f"slides/slide{i + 1}.xml") for i in range(n)]
        k = n + 3
        pres_rels += [(f"rId{k}", REL + "/presProps", "presProps.xml"), (f"rId{k + 1}", REL + "/viewProps", "viewProps.xml"),
                      (f"rId{k + 2}", REL + "/theme", "theme/theme1.xml"), (f"rId{k + 3}", REL + "/tableStyles", "tableStyles.xml")]
        z.writestr("ppt/_rels/presentation.xml.rels", rels(pres_rels))
        ids = "".join(f'<p:sldId id="{256 + i}" r:id="rId{i + 3}"/>' for i in range(n))
        z.writestr("ppt/presentation.xml",
                   f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentation {NS} saveSubsetFonts="1"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
                   f'<p:notesMasterIdLst><p:notesMasterId r:id="rId2"/></p:notesMasterIdLst><p:sldIdLst>{ids}</p:sldIdLst><p:sldSz cx="12192000" cy="6858000"/><p:notesSz cx="6858000" cy="9144000"/>'
                   '<p:defaultTextStyle><a:lvl1pPr marL="0" algn="l"><a:defRPr sz="1800" kern="1200"><a:solidFill><a:schemeClr val="tx1"/></a:solidFill><a:latin typeface="+mn-lt"/><a:ea typeface="+mn-ea"/><a:cs typeface="+mn-cs"/></a:defRPr></a:lvl1pPr></p:defaultTextStyle></p:presentation>')
        z.writestr("ppt/presProps.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:presentationPr {NS}/>')
        z.writestr("ppt/viewProps.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:viewPr {NS}><p:normalViewPr><p:restoredLeft sz="15620"/><p:restoredTop sz="94660"/></p:normalViewPr><p:slideViewPr><p:cSldViewPr><p:cViewPr varScale="1"><p:scale><a:sx n="100" d="100"/><a:sy n="100" d="100"/></p:scale><p:origin x="0" y="0"/></p:cViewPr><p:guideLst/></p:cSldViewPr></p:slideViewPr><p:notesTextViewPr><p:cViewPr><p:scale><a:sx n="1" d="1"/><a:sy n="1" d="1"/></p:scale><p:origin x="0" y="0"/></p:cViewPr></p:notesTextViewPr><p:gridSpacing cx="76200" cy="76200"/></p:viewPr>')
        z.writestr("ppt/tableStyles.xml", '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>')
        z.writestr("ppt/theme/theme1.xml", tema("inDrive Lab"))
        z.writestr("ppt/theme/theme2.xml", tema("Notas"))
        z.writestr("ppt/slideMasters/slideMaster1.xml", patron(len(disenos)))
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels",
                   rels([(f"rId{i + 1}", REL + "/slideLayout", f"../slideLayouts/slideLayout{i + 1}.xml") for i in range(len(disenos))] +
                        [(f"rId{len(disenos) + 1}", REL + "/theme", "../theme/theme1.xml")]))
        z.writestr("ppt/notesMasters/notesMaster1.xml", patron_notas())
        z.writestr("ppt/notesMasters/_rels/notesMaster1.xml.rels", rels([("rId1", REL + "/theme", "../theme/theme2.xml")]))
        for i, d in enumerate(disenos):
            z.writestr(f"ppt/slideLayouts/slideLayout{i + 1}.xml", d)
            z.writestr(f"ppt/slideLayouts/_rels/slideLayout{i + 1}.xml.rels", rels([("rId1", REL + "/slideMaster", "../slideMasters/slideMaster1.xml")]))
        for i, d in enumerate(diapositivas):
            z.writestr(f"ppt/slides/slide{i + 1}.xml", d.xml())
            lista = [("rId1", REL + "/slideLayout", f"../slideLayouts/slideLayout{d.diseno + 1}.xml")]
            lista += [(rid, REL + "/image", f"../media/{dest}") for rid, _t, dest in d.rels]
            lista.append((f"rId{len(d.rels) + 2}", REL + "/notesSlide", f"../notesSlides/notesSlide{i + 1}.xml"))
            z.writestr(f"ppt/slides/_rels/slide{i + 1}.xml.rels", rels(lista))
            z.writestr(f"ppt/notesSlides/notesSlide{i + 1}.xml", d.xml_notas())
            z.writestr(f"ppt/notesSlides/_rels/notesSlide{i + 1}.xml.rels",
                       rels([("rId1", REL + "/notesMaster", "../notesMasters/notesMaster1.xml"), ("rId2", REL + "/slide", f"../slides/slide{i + 1}.xml")]))
        for nombre, datos in medios.items():
            z.writestr(f"ppt/media/{nombre}", datos)
