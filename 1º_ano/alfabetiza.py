import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuração da página Streamlit
st.set_page_config(
    page_title="Dashboard de Alfabetização 1º ano",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Adicionando o logotipo na barra lateral
logo_url = '1º_ano/img/Logomarca da Secretaria de Educação 2021.png'
with st.sidebar:
    st.image(logo_url, width=300)

# Título principal do aplicativo
st.title("📊 Dashboard dos Resultados da Alfabetização - AMA / 1º ANO (2008 - 2024)")
st.markdown("Bem-vindo ao sistema de acesso aos resultados de alfabetização das escolas municipais de Maracanaú.")

# Função para carregar os dados
@st.cache_data
def load_data(file_path):
    df = pd.read_excel(file_path)
    return df

# Carregamento dos dados
try:
    df_login = load_data('1º_ano/xls/senhas_acesso.xlsx')  # Planilha de login
    df_ama = load_data('1º_ano/xls/bd_ama.xlsx')  # Planilha de alfabetização
    
    # Remover espaços extras nos nomes das colunas e valores
    df_login.columns = df_login.columns.str.strip()
    df_ama.columns = df_ama.columns.str.strip()
    df_login['INEP'] = df_login['INEP'].astype(str).str.strip()
    df_ama['INEP'] = df_ama['INEP'].astype(str).str.strip()

    # Formatar a coluna 'EDIÇÃO' para exibir apenas o ano (sem .0)
    df_ama['EDIÇÃO'] = df_ama['EDIÇÃO'].astype(int).astype(str)  # Converte para inteiro e depois para string

except FileNotFoundError as e:
    st.error(f"Erro: Arquivo não encontrado: {e.filename}. Verifique os arquivos.")
    st.stop()

# Função de logout
def logout():
    st.session_state.login_success = False
    st.session_state.escola_logada = None
    st.success("Logout realizado com sucesso!")

# Função para formatar a variação
def formatar_variacao(valor, eh_percentual=False):
    if valor > 0:
        sinal = "▲"
        cor = "green"
    elif valor < 0:
        sinal = "▼"
        cor = "red"
    else:
        sinal = ""
        cor = "blue"
    
    if eh_percentual:
        return f'<p style="color:{cor};">{sinal} {valor:.2f}%</p>'
    else:
        return f'<p style="color:{cor};">{sinal} {valor:.2f}</p>'

# INEP mestre
INEP_MESTRE = '2307650'

# Barra lateral para login
with st.sidebar:
    st.header("🔒 Acesso Restrito")
    st.markdown("Para acessar, insira o INEP da escola.")

    with st.form(key='login_form'):
        inep = st.text_input('INEP').strip()
        login_button = st.form_submit_button('Login')

# Verificação de login
if 'login_success' not in st.session_state:
    st.session_state.login_success = False

if login_button:
    if inep == INEP_MESTRE:
        st.session_state.login_success = True
        st.session_state.escola_logada = 'TODAS'
        st.success('Login realizado com sucesso como administrador!')
    elif inep in df_login['INEP'].values:
        st.session_state.login_success = True
        st.session_state.escola_logada = inep
        nome_escola = df_ama[df_ama['INEP'] == inep]['ESCOLA'].iloc[0]  # Pega o nome da escola
        st.success(f'Login realizado com sucesso! Bem-vindo, {nome_escola}!')
    else:
        st.error('INEP incorreto.')
        st.session_state.login_success = False

# Exibir dashboard após login
if st.session_state.login_success:
    if st.sidebar.button("Sair"):
        logout()
    
    # Filtra os dados da escola logada
    inep_logado = st.session_state.escola_logada

    if inep_logado == 'TODAS':
        # Se for o INEP mestre, exibe todas as escolas
        escolas = df_ama['ESCOLA'].unique().tolist()
        escolas.insert(0, 'TODAS')  # Adiciona a opção "TODAS"

        # Filtro de escolas acima da tabela de resultados
        escola_selecionada = st.selectbox("Selecione a ESCOLA", escolas)

        if escola_selecionada == 'TODAS':
            df_escola_ama = df_ama.copy()  # Exibe todos os dados
        else:
            df_escola_ama = df_ama[df_ama['ESCOLA'] == escola_selecionada].copy()  # Filtra pela escola selecionada
    else:
        # Se não for o INEP mestre, exibe apenas os dados da escola logada
        df_escola_ama = df_ama[df_ama['INEP'] == inep_logado].copy()

    if df_escola_ama.empty:
        st.warning("Não há dados disponíveis para esta escola.")
    else:
        # Ordena os dados pela coluna 'EDIÇÃO' em ordem crescente
        df_escola_ama = df_escola_ama.sort_values(by='EDIÇÃO')

        # Tabela de resultados de alfabetização (com textos centralizados)
        
        st.subheader(f"Tabela de Resultados - Percentual médio de Alfabetização - {escola_selecionada if inep_logado == 'TODAS' else nome_escola}")
        st.dataframe(
            df_escola_ama,
            use_container_width=True,
            column_config={
                "INEP": st.column_config.TextColumn("INEP", help="Código INEP da escola"),
                "ESCOLA": st.column_config.TextColumn("ESCOLA", help="Nome da escola"),
                "EDIÇÃO": st.column_config.TextColumn("EDIÇÃO", help="Ano da edição"),
                "PERCENTUAL ALFABETIZAÇÃO": st.column_config.NumberColumn(
                    "PERCENTUAL ALFABETIZAÇÃO",
                    help="Percentual de alfabetização",
                    format="%.1f%%"
                ),
            },
            hide_index=True,
        )

        # Tabela de diferença entre edições
        st.subheader(f"Tabela Comparativa entre Edições - {escola_selecionada if inep_logado == 'TODAS' else nome_escola}")
        variacao_data = []
        for i in range(1, len(df_escola_ama)):
            edicao_atual = df_escola_ama.iloc[i]['EDIÇÃO']
            edicao_anterior = df_escola_ama.iloc[i - 1]['EDIÇÃO']
            percentual_atual = df_escola_ama.iloc[i]['PERCENTUAL ALFABETIZAÇÃO']
            percentual_anterior = df_escola_ama.iloc[i - 1]['PERCENTUAL ALFABETIZAÇÃO']
            diferenca = percentual_atual - percentual_anterior

            # Formata a comparação entre edições (ex: "2023 - 2022")
            comparacao_edicoes = f"{edicao_atual} - {edicao_anterior}"

            variacao_data.append({
                'Escola': df_escola_ama.iloc[i]['ESCOLA'],  # mostra a escola
                'Comparação': comparacao_edicoes,  # Nova coluna com a comparação entre edições
                'Edição Atual': edicao_atual,
                'Edição Anterior': edicao_anterior,
                'Diferença Percentual': diferenca
            })

        if variacao_data:
            variacao_df = pd.DataFrame(variacao_data)
            variacao_df['Diferença Percentual'] = variacao_df['Diferença Percentual'].apply(
                lambda x: formatar_variacao(x, eh_percentual=True)
            )
            st.write(variacao_df.to_html(escape=False, index=False), unsafe_allow_html=True)
        else:
            st.write("Não há dados suficientes para calcular a variação entre as edições.")

        # Gráfico de barras para o percentual de alfabetização por edição
        st.subheader(f"Gráfico Percentual de Alfabetização por Edição - {escola_selecionada if inep_logado == 'TODAS' else nome_escola}")
        fig_bar, ax_bar = plt.subplots(figsize=(8, 4))

        # Altere a cor das barras para azul
        barras = ax_bar.bar(df_escola_ama['EDIÇÃO'], df_escola_ama['PERCENTUAL ALFABETIZAÇÃO'], color='blue')

        # Adicionar rótulos de percentual nas barras
        for barra in barras:
            altura = barra.get_height()
            ax_bar.text(
                barra.get_x() + barra.get_width() / 2,  # Posição X do rótulo
                altura + 0.05,  # Posição Y do rótulo (acima da barra)
                f'{altura:.1f}%',  # Valor do percentual
                ha='center',  # Alinhamento horizontal
                va='bottom',  # Alinhamento vertical
                color='black',  # Cor do rótulo
                fontsize=10  # Tamanho da fonte
            )

        # Configuração dos rótulos dos eixos
        ax_bar.set_xlabel('Edição', color='blue', fontsize=12)  # Rótulo do eixo X
        ax_bar.set_ylabel('Percentual de Alfabetização', color='blue', fontsize=12)  # Rótulo do eixo Y
        ax_bar.tick_params(axis='x', colors='blue', labelsize=10)  # Configuração dos ticks do eixo X
        ax_bar.tick_params(axis='y', colors='blue', labelsize=10)  # Configuração dos ticks do eixo Y

        st.pyplot(fig_bar)

        # Gráfico de linhas para o percentual de alfabetização por edição
        st.subheader(f"Gráfico Percentual de Alfabetização por Edição - {escola_selecionada if inep_logado == 'TODAS' else nome_escola}")
        fig_line, ax_line = plt.subplots(figsize=(8, 4))
        ax_line.plot(df_escola_ama['EDIÇÃO'], df_escola_ama['PERCENTUAL ALFABETIZAÇÃO'], marker='o', color='blue', linestyle='-', linewidth=2, markersize=8)

        # Adicionar rótulos de percentual nos pontos
        for i, (edicao, percentual) in enumerate(zip(df_escola_ama['EDIÇÃO'], df_escola_ama['PERCENTUAL ALFABETIZAÇÃO'])):
            ax_line.text(
                edicao,  # Posição X do rótulo
                percentual + 0.05,  # Posição Y do rótulo (acima do ponto)
                f'{percentual:.1f}%',  # Valor do percentual
                ha='center',  # Alinhamento horizontal
                va='bottom',  # Alinhamento vertical
                color='black',  # Cor do rótulo
                fontsize=10  # Tamanho da fonte
            )

        # Configuração dos rótulos dos eixos
        ax_line.set_xlabel('Edição', color='blue', fontsize=12)  # Rótulo do eixo X
        ax_line.set_ylabel('Percentual de Alfabetização', color='blue', fontsize=12)  # Rótulo do eixo Y
        ax_line.tick_params(axis='x', colors='blue', labelsize=10)  # Configuração dos ticks do eixo X
        ax_line.tick_params(axis='y', colors='blue', labelsize=10)  # Configuração dos ticks do eixo Y

        st.pyplot(fig_line)
else:
    st.info("Por favor, faça login para acessar os dados.")