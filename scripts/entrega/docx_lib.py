"""Utilidades mínimas para escribir WordprocessingML con la biblioteca estándar."""
import re
from xml.sax.saxutils import escape

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"
FRAG_NS = (f'xmlns:w="{W_NS}" xmlns:r="{R_NS}" xmlns:wp="{WP_NS}" xmlns:a="{A_NS}" xmlns:pic="{PIC_NS}"')

TEAL = "0A7C86"      # color de los encabezados de tabla (mismo del estilo Título 1 del documento base)
SOFT = "F3F6EC"
BORDE = "A6A6A6"


def esc(t):
    return escape(t)


def runs(texto, sz=None, color=None, base_b=False, base_i=False, mono=False):
    """Mini marcado: **negrita**, `código`, __cursiva__."""
    out, b, code, it = [], base_b, False, base_i
    for tok in re.split(r"(\*\*|`|__)", texto):
        if tok == "**":
            b = not b
        elif tok == "`":
            code = not code
        elif tok == "__":
            it = not it
        elif tok:
            out.append(run(tok, b=b, i=it, sz=sz, color=color, mono=code or mono))
    return "".join(out)


def run(t, b=False, i=False, sz=None, color=None, mono=False, caps=False):
    p = ""
    if mono:
        p += '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
    if b:
        p += "<w:b/><w:bCs/>"
    if i:
        p += "<w:i/><w:iCs/>"
    if caps:
        p += "<w:caps/>"
    if color:
        p += f'<w:color w:val="{color}"/>'
    s = sz
    if mono and sz is None:
        s = 19
    if s:
        p += f'<w:sz w:val="{s}"/><w:szCs w:val="{s}"/>'
    rpr = f"<w:rPr>{p}</w:rPr>" if p else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(t)}</w:t></w:r>'


def ppr(style=None, keep_next=False, keep_lines=False, page_break=False, num=None, shd=None, tabs=None,
        before=None, after=None, line=None, left=None, hanging=None, jc=None, sect=None, widow=True):
    x = ""
    if style:
        x += f'<w:pStyle w:val="{style}"/>'
    if keep_next:
        x += "<w:keepNext/>"
    if keep_lines:
        x += "<w:keepLines/>"
    if page_break:
        x += "<w:pageBreakBefore/>"
    if num:
        x += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/></w:numPr>'
    if shd:
        x += f'<w:shd w:val="clear" w:color="auto" w:fill="{shd}"/>'
    if tabs:
        x += "<w:tabs>" + "".join(f'<w:tab w:val="{v}" w:leader="{l}" w:pos="{p}"/>' for v, l, p in tabs) + "</w:tabs>"
    sp = ""
    if before is not None:
        sp += f' w:before="{before}"'
    if after is not None:
        sp += f' w:after="{after}"'
    if line is not None:
        sp += f' w:line="{line}" w:lineRule="auto"'
    if sp:
        x += f"<w:spacing{sp}/>"
    if left is not None or hanging is not None:
        x += "<w:ind" + (f' w:left="{left}"' if left is not None else "") + (f' w:hanging="{hanging}"' if hanging is not None else "") + "/>"
    if jc:
        x += f'<w:jc w:val="{jc}"/>'
    if sect:
        x += sect
    return f"<w:pPr>{x}</w:pPr>" if x else ""


def para(contenido="", **kw):
    if isinstance(contenido, (list, tuple)):
        contenido = "".join(contenido)
    return f"<w:p>{ppr(**kw)}{contenido}</w:p>"


def texto(t, **kw):
    """Párrafo de cuerpo con el mismo formato que el texto de los compañeros."""
    kw.setdefault("after", 140)
    kw.setdefault("line", 340)
    kw.setdefault("jc", "both")
    return para(runs(t), **kw)


def viñeta(t, num=2):
    return para(runs(t), style="Prrafodelista", num=num, after=80, line=320, jc="both")


def codigo(lineas):
    """Bloque monoespaciado con fondo continuo."""
    out = []
    for i, l in enumerate(lineas):
        out.append(para(run(l if l else " ", mono=True, sz=15), style="Cdigo", keep_lines=True, keep_next=i < len(lineas) - 1))
    return "".join(out)


def campo(instr, cache):
    return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            f'<w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            f'<w:r><w:t>{esc(str(cache))}</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r>')


def celda(contenido, ancho, fill=None, b=False, color=None, sz=18, jc=None, mono=False, keep=False):
    if isinstance(contenido, str):
        contenido = [contenido]
    ps = ""
    for linea in contenido:
        ps += para(runs(linea, sz=sz, color=color, base_b=b, mono=mono), after=40, line=264, jc=jc, keep_next=keep)
    sh = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
    bd = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="{BORDE}"/>' for s in ("top", "left", "bottom", "right"))
    return (f'<w:tc><w:tcPr><w:tcW w:w="{ancho}" w:type="dxa"/><w:tcBorders>{bd}</w:tcBorders>{sh}'
            '<w:tcMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/><w:bottom w:w="60" w:type="dxa"/>'
            f'<w:right w:w="100" w:type="dxa"/></w:tcMar></w:tcPr>{ps}</w:tc>')


def tabla(encabezados, filas, anchos, sz=18, mono_cols=(), bold_first=False, zebra=True, jc_cols=None, keep=None):
    total = sum(anchos)
    if keep is None:
        keep = len(filas) <= 14   # las tablas cortas no se parten entre páginas
    x = (f'<w:tbl><w:tblPr><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
         '<w:tblLook w:val="0420" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>'
         "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{a}"/>' for a in anchos) + "</w:tblGrid>")
    x += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(
        celda(h, a, fill=TEAL, b=True, color="FFFFFF", sz=sz, keep=keep) for h, a in zip(encabezados, anchos)) + "</w:tr>"
    for n, fila in enumerate(filas):
        fill = SOFT if zebra and n % 2 == 1 else None
        x += "<w:tr><w:trPr><w:cantSplit/></w:trPr>"
        for j, (c, a) in enumerate(zip(fila, anchos)):
            x += celda(c, a, fill=fill, b=bold_first and j == 0, sz=sz, mono=j in mono_cols,
                       jc=(jc_cols or {}).get(j), keep=keep and n < len(filas) - 1)
        x += "</w:tr>"
    return x + "</w:tbl>"


def imagen(rid, cx, cy, ident, nombre, descr):
    return (f'<w:r><w:rPr><w:noProof/></w:rPr><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:docPr id="{ident}" name="{esc(nombre)}" descr="{esc(descr)}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            f'<pic:nvPicPr><pic:cNvPr id="{ident}" name="{esc(nombre)}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')


def sect(horizontal=False, start=None, footer_rid="rId10"):
    if horizontal:
        sz = '<w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/><w:pgMar w:top="1134" w:right="1440" w:bottom="1134" w:left="1440" w:header="708" w:footer="567" w:gutter="0"/>'
    else:
        sz = '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1300" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
    pg = f'<w:pgNumType w:start="{start}"/>' if start else ""
    return f'<w:sectPr><w:footerReference w:type="default" r:id="{footer_rid}"/>{sz}{pg}<w:cols w:space="720"/><w:docGrid w:linePitch="360"/></w:sectPr>'
