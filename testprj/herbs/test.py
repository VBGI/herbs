from fpdf import FPDF


pdf = FPDF()
pdf.add_page()
pdf.image('./imgs/bgi_logo.png', w=20, h=20)

pdf.output('MYF.pdf', 'F')
pdf.set_font('Arial', 'B', 16)
