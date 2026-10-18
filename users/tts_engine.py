import os
import asyncio
from edge_tts import Communicate

async def gerar_faixa_audio(texto: str, caminho_saida: str, voz: str) -> bool:
    """
    Gera uma única faixa de áudio de forma assíncrona usando o edge-tts.
    Retorna True em caso de sucesso, False em caso de falha.
    """
    try:
        comunicador = Communicate(texto, voz)
        await comunicador.save(caminho_saida)
        return True
    except Exception as e:
        print(f"Erro ao gerar a faixa {caminho_saida}: {e}")
        return False

async def processar_audiolivro_completo(blocos: list, pasta_saida: str, voz: str, callback_progresso=None) -> list:
    """
    Processa uma lista de blocos de texto sequencialmente, guardando as faixas MP3.
    Permite um callback opcional para atualizar barras de progresso na interface web.
    """
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    faixas_geradas = []
    total_faixas = len(blocos)

    for i, bloco in enumerate(blocos):
        numero_faixa = f"{i + 1:03d}"
        nome_ficheiro = f"faixa_{numero_faixa}.mp3"
        caminho_completo = os.path.join(pasta_saida, nome_ficheiro)

        # Executa a geração assíncrona desta faixa
        sucesso = await gerar_faixa_audio(bloco, caminho_completo, voz)
        
        if sucesso:
            faixas_geradas.append(caminho_completo)

        # Se a interface web nos deu uma função para atualizar o progresso, chamamo-la aqui
        if callback_progresso:
            # Envia o índice atual (1-based) e o total para a UI saber onde vai
            callback_progresso(i + 1, total_faixas)

    return faixas_geradas
