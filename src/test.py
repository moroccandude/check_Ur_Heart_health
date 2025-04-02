from fpdf import FPDF

# Create instance of FPDF class
pdf = FPDF()

# Add a page
pdf.add_page()

# Set font
pdf.set_font("Arial", size=10)

# Add title
pdf.cell(200, 10, ln=True, align="C")

# Add content
content = """
Ismail Samil
+212 719599803
ismailsamilacc@gmail.com
02/04/2025

Objet : Candidature pour le Concours de Data Engineering

Monsieur,

Je me permets de vous adresser ma candidature pour le concours de Data Engineering. Ayant récemment terminé une formation spécialisée en data engineering et big data, et étant certifié Azure, je suis passionné par ce domaine et désireux d'appliquer mes compétences au sein de votre organisation.

Lors de mes précédentes expériences et formations, j'ai acquis des compétences solides en développement Java, gestion de données et cloud computing. J'ai également eu l'occasion de travailler sur des projets concrets, ce qui m'a permis de développer ma rigueur et ma capacité à résoudre des problèmes techniques complexes.

Je serais ravi de pouvoir discuter avec vous de l'opportunité d'apporter ma contribution à vos projets et de poursuivre ma carrière dans un environnement stimulant et innovant.

Dans l'attente de votre réponse, je vous prie d'agréer, Monsieur, l'expression de mes salutations distinguées.

Ismail Samil
"""

# Add the content
pdf.multi_cell(0, 10, content)

# Save the pdf with name
pdf_output_path="/home/usmail/Desktop/letter_motivation/Lettre_de_Motivation.pdf"
pdf.output(pdf_output_path)

pdf_output_path