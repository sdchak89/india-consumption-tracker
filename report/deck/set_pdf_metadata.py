"""Set title, author and licence in the PDF's metadata. Usage: python set_pdf_metadata.py in.pdf out.pdf"""
import sys
import pikepdf
src,dst=sys.argv[1],sys.argv[2]
with pikepdf.open(src) as pdf:
    with pdf.open_metadata(set_pikepdf_as_editor=False) as m:
        m['dc:title']='Where is Indian consumption going?'
        m['dc:creator']=['Mostly AI, with a little nudge from Soumyadeep']
        m['dc:description']='India consumption briefing, November 2026: what 69 months of UPI payments data say about how India spends.'
        m['dc:rights']='© 2026 Soumyadeep Chakraborty. CC BY 4.0.'
        m['pdf:Keywords']='India, consumption, UPI, NPCI, payments, credit'
        m['xmp:CreatorTool']='Soumyadeep Chakraborty'
        m['pdf:Producer']='Soumyadeep Chakraborty'
    pdf.docinfo['/Title']='Where is Indian consumption going?'
    pdf.docinfo['/Author']='Mostly AI, with a little nudge from Soumyadeep'
    pdf.docinfo['/Subject']='India consumption briefing, November 2026'
    pdf.docinfo['/Keywords']='India, consumption, UPI, NPCI, payments, credit'
    pdf.docinfo['/Creator']='Soumyadeep Chakraborty'
    pdf.docinfo['/Producer']='Soumyadeep Chakraborty'
    pdf.save(dst)
