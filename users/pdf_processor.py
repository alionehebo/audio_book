import os
from pypdf import PdfReader

def extrair_texto_pdf(ficheiro_pdf) -> str:
    """
    Lê um objeto de ficheiro PDF (ou caminho) e extrai o texto de todas as páginas,
    normalizando os espaços e quebras de linha.
    """
    try:
        leitor = PdfReader(ficheiro_pdf)
        texto_completo = ""

        for pagina in leitor.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                # Substitui quebras de linha por espaços para evitar pausas abruptas na fala
                texto_completo += texto_pagina.replace("\n", " ") + " "

        # Remove espaços duplos ou triplos residuais
        texto_completo = " ".join(texto_completo.split())
        return texto_completo
    except Exception as e:
        print(f"Erro ao ler o PDF: {e}")
        return ""

def dividir_texto_em_blocos(texto: str, limite_caracteres: int = 4000) -> list:
    """
    Divide uma string longa de texto em vários blocos menores respeitando o limite,
    tentando cortar sempre num ponto final ou espaço para preservar a integridade das frases.
    """
    blocos = []
    total_caracteres = len(texto)
    posicao_atual = 0

    if total_caracteres == 0:
        return blocos

    while posicao_atual < total_caracteres:
        fim_estimado = posicao_atual + limite_caracteres

        # Se o que resta do texto já cabe num único bloco, adiciona e encerra
        if fim_estimado >= total_caracteres:
            blocos.append(texto[posicao_atual:].strip())
            break

        # Tenta cortar o texto num ponto final para manter a semântica da frase
        ponto_corte = texto.rfind(". ", posicao_atual, fim_estimado)
        
        # Se não encontrar ponto final num raio razoável, tenta cortar num espaço
        if ponto_corte == -1 or ponto_corte < posicao_atual + (limite_caracteres // 2):
            ponto_corte = texto.rfind(" ", posicao_atual, fim_estimado)

        # Se mesmo assim falhar (ex: uma palavra gigante), faz um corte seco no limite estimado
        if ponto_corte == -1:
            ponto_corte = fim_estimado

        blocos.append(texto[posicao_atual:ponto_corte].strip())
        posicao_atual = ponto_corte + 1

    return blocos
