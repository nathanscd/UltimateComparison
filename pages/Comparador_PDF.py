import streamlit as st
import pdfplumber
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import difflib
import time

st.set_page_config(page_title="Comparador de PDFs", page_icon="📄")
st.title("Comparador de PDFs")
st.markdown("Faça upload de dois PDFs para comparar os parágrafos (cada linha é considerada um parágrafo).")

uploaded_pdf1 = st.file_uploader("Selecione o primeiro PDF", type=["pdf"])
uploaded_pdf2 = st.file_uploader("Selecione o segundo PDF", type=["pdf"])

def extract_paragraphs(file):
    paragraphs = []
    with pdfplumber.open(file) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text(x_tolerance=1, y_tolerance=1)
            if texto:
                linhas = texto.split("\n")
                for linha in linhas:
                    if linha.strip():
                        paragraphs.append(linha.strip())  # cada linha vira um parágrafo
    return paragraphs

def compare_paragraphs(p1, p2):
    diff = difflib.ndiff(p1.split(), p2.split())
    result = []
    for token in diff:
        if token.startswith("  "):
            result.append(token[2:])
        elif token.startswith("- "):
            result.append(f"[REMOVIDO: {token[2:]}]")
        elif token.startswith("+ "):
            result.append(f"[ADICIONADO: {token[2:]}]")
    return " ".join(result)

def generate_pdf(paragraphs1, paragraphs2):
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4)
    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_normal.wordWrap = "CJK"
    style_bold = ParagraphStyle("Bold", parent=style_normal, fontName="Helvetica-Bold", spaceAfter=6)

    story = []
    max_len = max(len(paragraphs1), len(paragraphs2))

    progresso_bar = st.progress(0)
    progresso_text = st.empty()
    inicio = time.time()

    for i in range(max_len):
        p1 = paragraphs1[i] if i < len(paragraphs1) else ""
        p2 = paragraphs2[i] if i < len(paragraphs2) else ""
        result = compare_paragraphs(p1, p2)

        story.append(Paragraph("PARÁGRAFO INICIAL:", style_bold))
        story.append(Paragraph(p1 or "[VAZIO]", style_normal))
        story.append(Spacer(1, 12))

        story.append(Paragraph("PARÁGRAFO DE COMPARAÇÃO:", style_bold))
        story.append(Paragraph(p2 or "[VAZIO]", style_normal))
        story.append(Spacer(1, 12))

        story.append(Paragraph("RESULTADO DAS DIFERENÇAS:", style_bold))
        story.append(Paragraph(result or "Sem diferenças.", style_normal))
        story.append(Spacer(1, 24))

        # Atualiza barra de progresso
        progresso_atual = i + 1
        progresso_bar.progress(progresso_atual / max_len)
        tempo_passado = time.time() - inicio
        tempo_estimado = (tempo_passado / progresso_atual) * (max_len - progresso_atual)
        tempo_str = f"{tempo_estimado/60:.1f} min restantes" if tempo_estimado > 60 else f"{tempo_estimado:.1f} seg restantes"
        progresso_text.markdown(f"**Processando parágrafo {progresso_atual}/{max_len} | {tempo_str}**")

    doc.build(story)
    output.seek(0)
    return output

if uploaded_pdf1 and uploaded_pdf2:
    if st.button("Iniciar Comparação"):
        paragraphs1 = extract_paragraphs(uploaded_pdf1)
        paragraphs2 = extract_paragraphs(uploaded_pdf2)
        pdf_bytes = generate_pdf(paragraphs1, paragraphs2)
        st.success("✅ Comparação concluída!")

        st.download_button(
            "📥 Baixar PDF de resultado",
            data=pdf_bytes,
            file_name="resultado_comparacao.pdf",
            mime="application/pdf"
        )
