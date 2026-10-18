import os
import asyncio
import streamlit as st
import streamlit.components.v1 as components
from users.pdf_processor import extrair_texto_pdf, dividir_texto_em_blocos
from users.tts_engine import processar_audiolivro_completo

# 1. Configuração da Página Web
st.set_page_config(
    page_title="PDF to AudioBook Neural",
    page_icon="🎧",
    layout="wide"
)

st.title("🎧 Audio livro")
st.markdown("Transforme os seus livros e documentos PDF em áudio de alta qualidade com controlos avançados de reprodução.")

# Inicializar estados de sessão para controlar qual faixa está a tocar
if "faixa_atual_index" not in st.session_state:
    st.session_state.faixa_atual_index = 0
if "faixas_geradas" not in st.session_state:
    st.session_state.faixas_geradas = []

# 2. Barra Lateral de Configurações (Sidebar)
st.sidebar.header("⚙️ Configurações de Voz")

opcoes_vozes = {
    "🇵🇹 Raquel (Feminino - Portugal)": "pt-PT-RaquelNeural",
    "🇵🇹 Duarte (Masculino - Portugal)": "pt-PT-DuarteNeural",
    "🇧🇷 Francisca (Feminino - Brasil)": "pt-BR-FranciscaNeural",
    "🇧🇷 Antonio (Masculino - Brasil)": "pt-BR-AntonioNeural",
    "🇧🇷 Thalita (Feminino - Brasil)": "pt-BR-ThalitaNeural"
}

voz_selecionada_label = st.sidebar.selectbox("Escolha o Narrador:", options=list(opcoes_vozes.keys()))
voz_id = opcoes_vozes[voz_selecionada_label]

limite_caracteres = st.sidebar.slider(
    "Tamanho Máximo por Faixa:",
    min_value=1000, max_value=6000, value=4000, step=500
)

# --- NOVAS FUNCIONALIDADES DO REPRODUTOR ---
st.sidebar.markdown("---")
st.sidebar.header("🎵 Modo do Reprodutor")
modo_reproducao = st.sidebar.radio(
    "Escolha o comportamento:",
    options=["Manual (Tocar um de cada vez)", "Autoplay (Passar à próxima faixa)", "Repetir (Loop na mesma faixa)"]
)

# 3. Área de Upload (Drag-and-Drop)
st.subheader("📁 Carregue o seu Ficheiro")
pdf_carregado = st.file_uploader("Arraste e solte o seu livro PDF aqui", type=["pdf"])

if pdf_carregado is not None:
    st.success(f"✔️ Ficheiro recebido com sucesso: {pdf_carregado.name}")
    
    if st.button("🚀 Iniciar Conversão para Áudio", type="primary"):
        with st.spinner("📖 A extrair texto do PDF..."):
            texto_extraido = extrair_texto_pdf(pdf_carregado)
        
        if not texto_extraido:
            st.error("❌ Não foi possível extrair texto deste PDF.")
        else:
            blocos = dividir_texto_em_blocos(texto_extraido, limite_caracteres=limite_caracteres)
            
            barra_progresso = st.progress(0)
            texto_progresso = st.empty()
            pasta_saida = "audiolivro_gerado"
            
            def atualizar_interface(atual, total):
                percentagem = atual / total
                barra_progresso.progress(percentagem)
                texto_progresso.text(f"🎙️ A gerar faixa {atual} de {total}...")

            # Processamento contínuo com o edge-tts
            st.session_state.faixas_geradas = asyncio.run(
                processar_audiolivro_completo(
                    blocos=blocos, pasta_saida=pasta_saida, voz=voz_id, callback_progresso=atualizar_interface
                )
            )
            
            barra_progresso.empty()
            texto_progresso.empty()
            st.session_state.faixa_atual_index = 0  # Começa na primeira faixa
            st.balloons()

# 4. Painel de Reprodução Inteligente
if st.session_state.faixas_geradas:
    st.write("---")
    st.subheader("🎵 Reprodutor Dinâmico")
    
    total_faixas = len(st.session_state.faixas_geradas)
    idx = st.session_state.faixa_atual_index
    caminho_faixa_atual = st.session_state.faixas_geradas[idx]
    
    nome_faixa_formatado = f"Faixa {idx + 1:03d} de {total_faixas:03d}"
    st.info(f"🔊 A reproduzir agora: **{nome_faixa_formatado}** (Modo: {modo_reproducao})")
    
    # Lógica JavaScript embutida para capturar o fim do áudio no navegador
    with open(caminho_faixa_atual, "rb") as f_audio:
        bytes_audio = f_audio.read()
    
    # Convertemos o áudio para base64 para poder injetar diretamente no HTML/JS
    import base64
    audio_base64 = base64.b64encode(bytes_audio).decode()
    audio_src = f"data:audio/mp3;base64,{audio_base64}"
    
    # Configurações do comportamento JS dependendo da escolha da Sidebar
    loop_attr = "loop" if "Repetir" in modo_reproducao else ""
    autoplay_attr = "autoplay" if "Manual" not in modo_reproducao else ""
    
    # Criamos um botão escondido em HTML que o JS pode "clicar" para avisar o Streamlit que a música acabou
    # Isto permite saltar para a próxima faixa de forma totalmente automatizada!
    codigo_html_player = f"""
    <audio id="meu-player" controls {autoplay_attr} {loop_attr} style="width: 100%;">
        <source src="{audio_src}" type="audio/mp3">
    </audio>
    
    <script>
        var audio = document.getElementById('meu-player');
        audio.onended = function() {{
            if ("{modo_reproducao}" === "Autoplay (Passar à próxima faixa)") {{
                // Envia uma mensagem para o Streamlit avançar de faixa
                window.parent.postMessage({{type: 'streamlit:setComponentValue', value: 'proxima'}}, '*');
            }}
        }};
    </script>
    """
    
    # Renderiza o player inteligente com detetor de eventos
    resposta_player = components.html(codigo_html_player, height=100)
    
    # Se o JavaScript detetou que a música terminou e estamos em modo Autoplay
    if resposta_player == "proxima":
        if st.session_state.faixa_atual_index < total_faixas - 1:
            st.session_state.faixa_atual_index += 1
            st.rerun() # Atualiza a app para carregar o próximo áudio imediatamente
        else:
            st.success("🏁 Chegou ao fim do audiolivro!")
            st.session_state.faixa_atual_index = 0 # Reinicia para o início
            st.rerun()

    # 5. Lista completa de faixas para navegação manual e download
    st.write("### 📂 Índice Geral de Faixas")
    col1, col2 = st.columns(2)
    
    for i, caminho_faixa in enumerate(st.session_state.faixas_geradas):
        nome_f = os.path.basename(caminho_faixa)
        lbl_faixa = f"Visualizar/Baixar Faixa {i + 1:03d}"
        
        with col1 if i % 2 == 0 else col2:
            with st.expander(lbl_faixa):
                if st.button(f"▶️ Selecionar e Tocar Faixa {i+1:03d}", key=f"btn_{i}"):
                    st.session_state.faixa_atual_index = i
                    st.rerun()
                
                with open(caminho_faixa, "rb") as f:
                    st.download_button(
                        label=f"⬇️ Baixar MP3 (Faixa {i+1:03d})",
                        data=f.read(),
                        file_name=nome_f,
                        mime="audio/mp3",
                        key=f"dl_{i}"
                    )
