# app/services/pdf_creator.py

import os
import io
import math
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from textwrap import wrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
REPORTS_PATH = os.path.join(BASE_PATH, "..", "reports")


# ------------------------------------------------------------
#  GERA O GRÁFICO RADAR
# ------------------------------------------------------------
def gerar_grafico_radar(pilares: dict) -> io.BytesIO:
    labels = list(pilares.keys())
    values = list(pilares.values())

    num_vars = len(labels)

    angles = [n / float(num_vars) * 2 * math.pi for n in range(num_vars)]
    angles += angles[:1]
    values += values[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.25)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(
        [lbl.replace("_", " ").capitalize() for lbl in labels],
        fontsize=7,
    )

    ax.grid(True)
    ax.set_yticklabels([])

    buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf


# ------------------------------------------------------------
#  FUNÇÃO PARA QUEBRA DE LINHA
# ------------------------------------------------------------
def _draw_wrapped_text(c, text, x, y, max_chars=95, leading=14):
    if not text:
        return y
    lines = wrap(text, max_chars)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


# ------------------------------------------------------------
#  GERA O PDF COMPLETO
# ------------------------------------------------------------
def gerar_pdf_relatorio(dados: dict, session_id: int) -> str:
    if not os.path.exists(REPORTS_PATH):
        os.makedirs(REPORTS_PATH, exist_ok=True)

    pdf_path = os.path.join(REPORTS_PATH, f"score_{session_id}.pdf")

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    margin_x = 50
    y = height - 60

    # HEADER — NOME + AUTORIA + DATA
    c.setFont("Helvetica-Bold", 22)
    c.drawString(margin_x, y, dados["nome"])
    y -= 28

    c.setFont("Helvetica", 13)
    c.drawString(margin_x, y, "Relatório Pessoal do Score de Riqueza™")
    y -= 18

    data_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    c.setFont("Helvetica", 10)
    c.drawString(
        margin_x,
        y,
        f"Método desenvolvido por Fernando Tessaro • Gerado em {data_str}",
    )
    y -= 35

    # RESUMO GERAL
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "Resumo Geral")
    y -= 20

    c.setFont("Helvetica", 12)
    c.drawString(margin_x, y, f"Score Total: {dados['score_total']}")
    y -= 16
    c.drawString(margin_x, y, f"Perfil identificado: {dados['perfil']}")
    y -= 16
    c.drawString(margin_x, y, f"Pilar mais forte: {dados['pilar_dominante']}")
    y -= 16
    c.drawString(margin_x, y, f"Pilar mais vulnerável: {dados['pilar_toxico']}")
    y -= 30

    # GRÁFICO RADAR
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "Distribuição dos Pilares")
    y -= 20

    radar_buf = gerar_grafico_radar(dados["pilares"])
    radar_img = ImageReader(radar_buf)

    img_w, img_h = 280, 280
    img_x = margin_x
    img_y = y - img_h

    c.drawImage(
        radar_img,
        img_x,
        img_y,
        width=img_w,
        height=img_h,
        mask="auto",
        preserveAspectRatio=True,
    )
    y = img_y - 20

    # Lista dos pilares
    c.setFont("Helvetica", 11)
    for nome_pilar, valor in dados["pilares"].items():
        label = nome_pilar.replace("_", " ").capitalize()
        c.drawString(margin_x, y, f"{label}: {valor}")
        y -= 14

    y -= 20

    if y < 150:
        c.showPage()
        y = height - 60

    # INTERPRETAÇÃO COMBINADA (perfil + pilar forte + pilar tóxico)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin_x, y, "Leitura do seu momento")
    y -= 20

    c.setFont("Helvetica", 11)
    y = _draw_wrapped_text(c, dados["interpretacao"], margin_x, y)

    y -= 25

    # CONVITE ESTRATÉGICO — SOMENTE SE RENDA QUALIFICADA
    if dados.get("renda_qualificada", True):
        c.setFont("Helvetica-Bold", 14)
        c.drawString(margin_x, y, "Convite estratégico")
        y -= 20

        c.setFont("Helvetica", 11)
        y = _draw_wrapped_text(c, dados["convite_sessao"], margin_x, y)

    c.showPage()
    c.save()

    return pdf_path