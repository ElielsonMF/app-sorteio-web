import streamlit as st
import pandas as pd
import random
import io # Usado para criar o arquivo de download em memória

# --- Configuração da Entrada (Sidebar) ---
st.sidebar.title("Configurações do Sorteio")
st.sidebar.image("logo.jpeg", use_column_width=True)

def realizar_sorteio_unico(lista_itens, numero_vencedores_x):
    """
    Realiza um sorteio único e divide a lista em vencedores e não contemplados.
    """
    # Garante que não tentamos sortear mais vencedores do que temos na lista
    numero_vencedores_x = min(numero_vencedores_x, len(lista_itens))
    
    vencedores = random.sample(lista_itens, numero_vencedores_x)
    
    set_vencedores = set(vencedores)
    nao_contemplados = [item for item in lista_itens if item not in set_vencedores]
    
    return vencedores, nao_contemplados

def to_excel(df, header=True):
    """
    Converte um DataFrame do pandas para um arquivo Excel em bytes,
    pronto para ser baixado pelo Streamlit.
    """
    output = io.BytesIO()
    # Usamos 'openpyxl' como engine para compatibilidade com .xlsx
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=header, sheet_name='Resultados_Sorteio')
    
    processed_data = output.getvalue()
    return processed_data

# --- Interface do Streamlit ---

st.title("🚀 Web App de Sorteio")
st.markdown("Uma ferramenta para realizar sorteios únicos e exportar os resultados.")

# --- 1. Configuração da Entrada (Sidebar) ---
st.sidebar.title("Configurações do Sorteio")
modo_entrada = st.sidebar.radio(
    "Como deseja carregar a lista de itens?",
    ("Inserir manualmente", "Carregar de planilha (Excel)"),
    key="modo_entrada"
)

# Variáveis que vamos preencher
lista_original_y = None
df_original = None
header_option_usada = 0 # 0 para 'sim', None para 'não'
coluna_selecionada = None

# --- 2. Lógica de Entrada ---

if modo_entrada == "Inserir manualmente":
    st.header("Opção 1: Inserir Itens Manualmente")
    texto_itens = st.text_area("Insira os itens/nomes, um por linha:", height=200)
    
    if texto_itens:
        lista_original_y = [item.strip() for item in texto_itens.splitlines() if item.strip()]
        st.info(f"Total de {len(lista_original_y)} itens carregados.")

elif modo_entrada == "Carregar de planilha (Excel)":
    st.header("Opção 2: Carregar de Planilha")
    
    uploaded_file = st.file_uploader("Carregue seu arquivo .xlsx", type=["xlsx"])
    
    if uploaded_file is not None:
        tem_cabecalho = st.checkbox("A primeira linha é um cabeçalho (títulos)", value=True)
        
        if tem_cabecalho:
            header_option_usada = 0 # Primeira linha é cabeçalho (padrão pandas)
        else:
            header_option_usada = None # Nenhuma linha é cabeçalho
        
        try:
            # Carrega a planilha em um DataFrame
            df_original = pd.read_excel(uploaded_file, header=header_option_usada)
            st.dataframe(df_original.head(), use_container_width=True)

            # Seleção da Coluna
            if tem_cabecalho:
                # Se tem cabeçalho, usuário escolhe pelo NOME
                colunas_disponiveis = df_original.columns.tolist()
                coluna_selecionada = st.selectbox("Selecione a coluna com os itens:", colunas_disponiveis)
            else:
                # Se não tem cabeçalho, usuário escolhe pelo NÚMERO (índice)
                # Criamos um "dicionário" para mapear "Coluna 1" -> 0, etc.
                colunas_mapeadas = {f"Coluna {i+1}": i for i in df_original.columns}
                coluna_escolhida_nome = st.selectbox("Selecione a coluna com os itens:", colunas_mapeadas.keys())
                coluna_selecionada = colunas_mapeadas[coluna_escolhida_nome]
            
            # Extrai a lista final
            lista_original_y = df_original[coluna_selecionada].dropna().tolist()
            st.info(f"Total de {len(lista_original_y)} itens carregados da '{coluna_selecionada}'.")

        except Exception as e:
            st.error(f"Ocorreu um erro ao ler o arquivo: {e}")

# --- 3. Execução do Sorteio (só aparece se a lista foi carregada) ---

if lista_original_y:
    st.divider()
    st.header("Realizar o Sorteio")
    
    # Número de vencedores
    numero_vencedores_x = st.number_input(
        f"Quantos vencedores (x) devem ser sorteados? (de {len(lista_original_y)} itens)",
        min_value=1,
        max_value=len(lista_original_y),
        value=1,
        step=1
    )
    
    # Botão para executar
    if st.button("🍀 REALIZAR SORTEIO!", use_container_width=True, type="primary"):
        
        vencedores, nao_contemplados = realizar_sorteio_unico(lista_original_y, numero_vencedores_x)
        
        st.balloons()
        st.header("Resultados")
        
        # Exibe os resultados em colunas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"🏆 {len(vencedores)} Vencedores")
            st.dataframe(pd.DataFrame(vencedores, columns=["Vencedor"]), use_container_width=True)
        
        with col2:
            st.subheader(f"({len(nao_contemplados)}) Não Contemplados")
            st.dataframe(pd.DataFrame(nao_contemplados, columns=["Não Contemplado"]), use_container_width=True)
            
        # --- 4. Lógica de Download (só para Excel) ---
        if modo_entrada == "Carregar de planilha (Excel)" and df_original is not None:
            st.divider()
            st.subheader("Download do Resultado")
            
            # Prepara o DataFrame final
            df_resultado = df_original.copy()
            df_resultado['Vencedores_Sorteio'] = pd.Series(vencedores)
            df_resultado['Nao_Contemplados_Sorteio'] = pd.Series(nao_contemplados)
            
            # Converte para bytes
            excel_bytes = to_excel(df_resultado, header=(header_option_usada == 0))
            
            st.download_button(
                label="Baixar Excel com Resultados",
                data=excel_bytes,
                file_name="resultado_sorteio.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True

            )
