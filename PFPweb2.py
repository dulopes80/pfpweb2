import streamlit as st
import os
import json
import re
import tempfile
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
from pdf2image import convert_from_bytes  # Necessário: pip install pdf2image e Poppler instalado
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_JUSTIFY

# Configuração do Streamlit
st.set_page_config(page_title="Sistema de Laudos", layout="centered")

# --------------------------------------------------------
# Definição de caminhos relativos (baseados na raiz do repositório)
# --------------------------------------------------------
PASTA_PROJETO = os.path.dirname(__file__)  # Diretório onde o script está
CAMINHO_LAUDOS = os.path.join(PASTA_PROJETO, "laudos.json")
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
if os.path.isdir(desktop_path):
    CAMINHO_SAIDA = desktop_path
else:
    CAMINHO_SAIDA = tempfile.gettempdir()

# Arquivos de carimbos e marca d'água
CAMINHO_CARIMBOS = PASTA_PROJETO  
CAMINHO_MARCA = os.path.join(PASTA_PROJETO, "marca2.pdf")

DIC_CARIMBOS = {
    "Dr. Eduardo": "carimbo.jpg",
    "Dra. Fernanda": "carimbofernanda.jpg",
    "Dr. Jair": "carimbojair.jpg",
    "Dr. Rogério": "carimborogerio.jpg"
}

# --------------------------------------------------------
# Funções auxiliares
# --------------------------------------------------------
def carregar_laudos():
    if not os.path.exists(CAMINHO_LAUDOS):
        return {}
    with open(CAMINHO_LAUDOS, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception as e:
            st.error(f"Erro ao carregar laudos: {e}")
            return {}

def salvar_laudos(laudos):
    with open(CAMINHO_LAUDOS, "w", encoding="utf-8") as f:
        json.dump(laudos, f, ensure_ascii=False, indent=2)

def visualizar_pdf_como_imagem(pdf_file):
    """
    Converte o PDF para imagem (apenas a primeira página) usando pdf2image
    e exibe diretamente na página.
    """
    try:
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()
        # Converte a primeira página do PDF em uma imagem Pillow
        images = convert_from_bytes(pdf_bytes, first_page=1, last_page=1)
        if images:
            st.image(images[0], caption="Visualização do PDF (página 1)")
        else:
            st.error("Não foi possível converter o PDF para imagem.")
    except Exception as e:
        st.error("Erro ao converter PDF para imagem. Certifique-se de ter o Poppler instalado. Erro: " + str(e))
    finally:
        pdf_file.seek(0)

def adicionar_laudo_ao_pdf(pdf_original, texto_laudo, titulo_laudo="Interpretação de resultados", nome_medico=None, nome_arquivo_carimbo=None):
    pdf_original.seek(0)
    reader = PdfReader(pdf_original)
    writer = PdfWriter()
    largura_pagina, altura_pagina = A4
    margem_esquerda = 2 * cm
    margem_direita = 2 * cm

    # Extrai os campos "Nome:" e "Data do exame:" do PDF original
    texto_pdf = ""
    for page in reader.pages:
        parte = page.extract_text()
        if parte:
            texto_pdf += parte + "\n"

    match_nome = re.search(r"Nome:\s*([^\n\r]+)", texto_pdf)
    nome_pdf = match_nome.group(1).strip() if match_nome else "N/A"

    match_date = re.search(r"(?:Date do exame:|Data do exame:)\s*([^\n\r]{1,10})", texto_pdf)
    date_pdf = match_date.group(1).strip() if match_date else "N/A"
    
    # Cria um canvas para compor a nova página de laudo
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)

    topo_info = altura_pagina - 6 * cm
    can.setFont("Helvetica-Bold", 12)
    can.drawString(margem_esquerda, topo_info, f"Nome: {nome_pdf}")
    can.drawRightString(largura_pagina - margem_direita, topo_info, f"Data do exame: {date_pdf}")

    topo_texto = topo_info - 1.7 * cm
    can.setFont("Helvetica-Bold", 14)
    can.drawString(margem_esquerda, topo_texto, titulo_laudo)

    styles = getSampleStyleSheet()
    estilo_laudo = styles["Normal"]
    estilo_laudo.fontName = "Helvetica"
    estilo_laudo.fontSize = 12
    estilo_laudo.leading = 15
    estilo_laudo.alignment = TA_JUSTIFY

    altura_texto = 10 * cm
    pos_texto_y = topo_texto - 1 * cm - altura_texto
    paragrafo_laudo = Paragraph(texto_laudo.replace("\n", "<br/>"), estilo_laudo)
    largura_texto = largura_pagina - margem_esquerda - margem_direita
    frame_texto = Frame(margem_esquerda, pos_texto_y, largura_texto, altura_texto, showBoundary=0)
    frame_texto.addFromList([paragrafo_laudo], can)

    # Inserção do carimbo: leitura em modo binário usando BytesIO
    caminho_carimbo = os.path.join(CAMINHO_CARIMBOS, nome_arquivo_carimbo)
    if os.path.exists(caminho_carimbo):
        with open(caminho_carimbo, "rb") as f:
            carimbo_data = f.read()
        carimbo = ImageReader(BytesIO(carimbo_data))
        largura_carimbo = 3.4 * cm
        altura_carimbo = 2 * cm
        pos_x = largura_pagina - largura_carimbo - 3 * cm
        pos_y = pos_texto_y - altura_carimbo - 0.3 * cm
        can.drawImage(carimbo, pos_x, pos_y, width=largura_carimbo, height=altura_carimbo, mask="auto")

    style_ref = styles["Normal"].clone("ref_estilo")
    style_ref.fontName = "Helvetica"
    style_ref.fontSize = 9
    style_ref.alignment = TA_JUSTIFY

    referencias = ("""
        <b>Referências</b><br/>
        Pereira CAC, Sato T, Rodrigues SC. Valores de referência para espirometria em brasileiros adultos de raça branca. 
        J Bras Pneumol. 2007;33(4):397-406.<br/><br/>
        Sociedade Brasileira de Pneumologia e Tisiologia. Diretrizes para Testes de Função Pulmonar – Atualização 2024. 
        J Bras Pneumol. 2024;50(6):e2024xx.<br/><br/>
        Sociedade Brasileira de Pneumologia e Tisiologia. Diretrizes para Testes de Função Pulmonar – Consenso 2002. 
        J Pneumol. 2002;28(Supl 3):S1-S238.
    """)
    paragrafo_ref = Paragraph(referencias, style_ref)
    frame_ref = Frame(margem_esquerda, 2 * cm, 12 * cm, 6 * cm, showBoundary=0)
    frame_ref.addFromList([paragrafo_ref], can)
    
    can.save()
    packet.seek(0)
    nova_pagina = PdfReader(packet).pages[0]

    # Mescla a marca d'água, se disponível
    if os.path.exists(CAMINHO_MARCA):
        marca = PdfReader(CAMINHO_MARCA).pages[0]
        nova_pagina.merge_page(marca)
    else:
        marca = None

    # Mescla as páginas originais com a nova página de laudo
    for page in reader.pages:
        if marca:
            page.merge_page(marca)
        writer.add_page(page)
    
    writer.add_page(nova_pagina)
    
    saida = BytesIO()
    writer.write(saida)
    return saida

def aba_laudar():
    st.title("📄 Laudos de Função Pulmonar")
    laudos = carregar_laudos()
    
    arquivo_pdf = st.file_uploader("Selecione o arquivo PDF", type="pdf")
    if arquivo_pdf:
        visualizar_pdf_como_imagem(arquivo_pdf)
    
    st.markdown("### Selecione os textos que deseja incluir")
    selecionados = []
    for categoria, laudos_categoria in laudos.items():
        with st.expander(categoria):
            for nome, texto in laudos_categoria.items():
                if st.checkbox(f"{nome}", key=f"{categoria}_{nome}"):
                    selecionados.append(texto)
    
    texto_final = "\n\n".join(selecionados)
    if texto_final:
        st.text_area("Texto do Laudo (Edite se necessário)", value=texto_final, height=200, key="laudo_editado")
    
    if arquivo_pdf:
        caminho_pdf = os.path.join(CAMINHO_SAIDA, arquivo_pdf.name)
        with open(caminho_pdf, "wb") as f:
            f.write(arquivo_pdf.getvalue())
    
    nome_medico = st.sidebar.selectbox("Selecione o médico responsável", list(DIC_CARIMBOS.keys()))
    
    if st.button("Gerar PDF com Laudo"):
        if not arquivo_pdf or not texto_final:
            st.error("Envie um PDF e selecione pelo menos um laudo.")
            return

        texto_editado = st.session_state.laudo_editado
        arquivo_carimbo = DIC_CARIMBOS[nome_medico]
        
        resultado = adicionar_laudo_ao_pdf(
            arquivo_pdf,
            texto_editado,
            titulo_laudo="Interpretação de resultados",
            nome_medico=nome_medico,
            nome_arquivo_carimbo=arquivo_carimbo
        )
        nome_arquivo = os.path.splitext(arquivo_pdf.name)[0] + "_assinado.pdf"
        caminho_final = os.path.join(CAMINHO_SAIDA, nome_arquivo)
        
        with open(caminho_final, "wb") as f:
            f.write(resultado.getbuffer())
        
        st.success(f"Arquivo salvo em: {caminho_final}")
        st.download_button(
            label="📥 Baixar PDF com Laudo",
            data=resultado.getvalue(),
            file_name=nome_arquivo,
            mime="application/pdf"
        )

def editar_laudos():
    st.subheader("📋 Editar Laudo")
    laudos = carregar_laudos()
    laudos_str = json.dumps(laudos, ensure_ascii=False, indent=2)
    novo_conteudo = st.text_area("Conteúdo do JSON:", value=laudos_str, height=300)
    if st.button("Salvar Alterações"):
        try:
            novo_json = json.loads(novo_conteudo)
            salvar_laudos(novo_json)
            st.success("Arquivo JSON atualizado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao validar o JSON: {e}")

# --------------------------------------------------------
# Interface principal com menu lateral
# --------------------------------------------------------
st.sidebar.title("Menu")
pagina = st.sidebar.radio("Escolha a página", ["Laudar", "Editar Laudo"])

if pagina == "Laudar":
    aba_laudar()
elif pagina == "Editar Laudo":
    editar_laudos()
