import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile
import os
import json

CAMINHO_PADRAO = r"C:\Users\Eduardo\Desktop\Projeto1\Projeto2"
ARQUIVO_LAUDOS = r"C:\Users\Eduardo\Desktop\Projeto1\Projeto2\laudos.json"

1
def carregar_laudos(arquivo_json):
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Arquivo {arquivo_json} não encontrado.")
        return {}
    except json.JSONDecodeError:
        print(f"Erro ao ler {arquivo_json}. Verifique o formato.")
        return {}

def criar_pagina_laudo(texto):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(temp_file.name, pagesize=A4)
    width, height = A4

    y = height - 50
    for linha in texto.split("\n"):
        c.drawString(50, y, linha)
        y -= 20
    c.save()
    return temp_file.name

def inserir_laudo_no_pdf(pdf_original, texto_laudo, pdf_destino):
    novo_laudo_pdf = criar_pagina_laudo(texto_laudo)

    doc_original = fitz.open(pdf_original)
    doc_laudo = fitz.open(novo_laudo_pdf)

    doc_original.insert_pdf(doc_laudo)

    doc_original.save(pdf_destino)
    doc_original.close()
    doc_laudo.close()
    os.remove(novo_laudo_pdf)

def main():
    laudos_padrao = carregar_laudos(ARQUIVO_LAUDOS)
    if not laudos_padrao:
        print("Nenhum laudo encontrado. Verifique o arquivo JSON.")
        return

    print("Selecione um laudo:")
    titulos = list(laudos_padrao.keys())
    for i, titulo in enumerate(titulos, start=1):
        print(f"{i}. {titulo}")

    escolha = int(input("Digite o número do laudo: "))
    if escolha < 1 or escolha > len(titulos):
        print("Escolha inválida.")
        return

    texto_escolhido = laudos_padrao[titulos[escolha - 1]]

    nome_arquivo = input("Digite o nome do arquivo PDF (sem o caminho): ").strip()
    caminho_pdf = os.path.join(CAMINHO_PADRAO, nome_arquivo)

    if not os.path.exists(caminho_pdf):
        print(f"Arquivo '{caminho_pdf}' não encontrado.")
        return

    nome_base, ext = os.path.splitext(nome_arquivo)
    novo_nome = os.path.join(CAMINHO_PADRAO, f"{nome_base}_report{ext}")

    inserir_laudo_no_pdf(caminho_pdf, texto_escolhido, novo_nome)
    print(f"\n✅ PDF com laudo salvo como: {novo_nome}")

if __name__ == "__main__":
    main()
