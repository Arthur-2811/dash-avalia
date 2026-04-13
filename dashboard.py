import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

import facebook
import planilhas

# ==========================================
# CONFIGURAÇÃO DA PÁGINA E CSS CUSTOMIZADO
# ==========================================
st.set_page_config(layout="wide", page_title="Dash Avalia", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* Estilo base para os cartões */
    .st-card {
        background-color: #1E1E2B;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        margin-bottom: 1rem;
        border: 1px solid #2B2B3C;
    }
    
    .card-anual { background-color: #243B2A; border: 1px solid #365C40; }
    .card-semestral { background-color: #1F3653; border: 1px solid #2D5280; }
    .card-mensal { background-color: #43285C; border: 1px solid #643A8A; }
    .card-renovacao { background-color: #30414F; border: 1px solid #445D70; }
    
    .card-roas { 
        background-color: #38311B; 
        border: 1px solid #E1B12C; 
        border-radius: 10px; 
        padding: 20px;
        box-shadow: 0px 0px 15px rgba(225, 177, 44, 0.1);
    }

    .card-title { font-size: 0.95rem; color: #A0A0B5; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;}
    .card-value { font-size: 2rem; font-weight: bold; color: white; margin-bottom: 5px; line-height: 1.2;}
    .card-delta-up { font-size: 0.8rem; color: #4CAF50; }
    .card-delta-down { font-size: 0.8rem; color: #F44336; }
    .card-delta-neutral { font-size: 0.8rem; color: #8A8A9E; }
</style>
""", unsafe_allow_html=True)

def criar_cartao(titulo, valor, subtitulo, icone="", classe_css="st-card", tipo_delta="neutral"):
    cor_delta = "card-delta-up" if tipo_delta == "up" else "card-delta-down" if tipo_delta == "down" else "card-delta-neutral"
    html = f"""
    <div class="{classe_css}">
        <div class="card-title">{icone} {titulo}</div>
        <div class="card-value">{valor}</div>
        <div class="{cor_delta}">{subtitulo}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def carregar_dados_facebook(inicio, fim):
    return facebook.get_facebook_data(inicio, fim)

@st.cache_data(ttl=600)
def carregar_dados_planilhas(inicio, fim):
    return planilhas.get_sheets_data(inicio, fim)

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
def main():
    # --- MENU LATERAL ---
    with st.sidebar:
        if st.button("🔄 Atualizar Dados", use_container_width=True, type="primary"):
            st.cache_data.clear()
            st.rerun()
            
        st.markdown("---")
        
        st.header("Filtros de Período")
        hoje = datetime.date.today()
        datas = st.date_input("Selecione o Período:", [hoje, hoje])
        
        if len(datas) == 2:
            data_inicio, data_fim = datas
        else:
            data_inicio = data_fim = datas[0]
            
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.expander("⚙️ Opções Avançadas"):
            st.write("Aproveite para conferir a planilha crua de Leads.")
            mostrar_debug = st.checkbox("Ativar Modo Debug")
        
    # --- CABEÇALHO ---
    st.title("Dashboard de Performance - Avalia NR01")
    st.markdown(f"<span style='color:#A0A0B5;'>Analisando o período: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}</span>", unsafe_allow_html=True)
    
    # --- PROCESSAMENTO DOS DADOS ---
    with st.spinner("Sincronizando dados com o Google e Facebook..."):
        df_fb = carregar_dados_facebook(data_inicio, data_fim)
        df_leads, df_vendas = carregar_dados_planilhas(data_inicio, data_fim)
        
    # Cálculos Vendas
    vendas_novas = df_vendas[~df_vendas['É Renovação']]
    
    qtd_anual = len(vendas_novas[vendas_novas['Categoria Plano'] == 'Anual'])
    qtd_sem = len(vendas_novas[vendas_novas['Categoria Plano'] == 'Semestral'])
    
    total_vendas_novas = len(vendas_novas)
    qtd_mensal = total_vendas_novas - qtd_anual - qtd_sem 
    if qtd_mensal < 0: qtd_mensal = 0
    
    df_renovacoes = df_vendas[df_vendas['É Renovação']]
    qtd_renovacoes = len(df_renovacoes)
    
    # --- BANNER DE COMPRADORES (MARQUEE) ---
    if not df_vendas.empty:
        mensagens = []
        for idx, row in df_vendas.iterrows():
            nome_cliente = str(row.get('Nome', 'Cliente')).title()
            plano = row.get('Categoria Plano', 'Mensal')
            if row.get('É Renovação', False):
                mensagens.append(f"🔄 <b>{nome_cliente}</b> renovou o Plano {plano}!")
            else:
                mensagens.append(f"🛒 <b>{nome_cliente}</b> acabou de comprar o Plano {plano}!")
                
        texto_banner = " &nbsp;&nbsp;&nbsp;&nbsp; ⭐ &nbsp;&nbsp;&nbsp;&nbsp; ".join(mensagens)
        
        st.markdown(f"""
        <div style="background-color: #1E1E2B; border: 1px solid #E1B12C; border-radius: 8px; padding: 12px; margin-top: 15px; margin-bottom: 25px;">
            <marquee direction="left" scrollamount="6" style="color: #FFFFFF; font-size: 16px;">
                {texto_banner}
            </marquee>
        </div>
        """, unsafe_allow_html=True)

    # Cálculos Financeiros
    investimento_total = df_fb['Investimento'].sum() if not df_fb.empty else 0
    total_leads = len(df_leads)
    faturamento_novas = vendas_novas['Valor bruto'].sum()
    
    cpl = investimento_total / total_leads if total_leads > 0 else 0
    cpa = investimento_total / total_vendas_novas if total_vendas_novas > 0 else 0
    roas = faturamento_novas / investimento_total if investimento_total > 0 else 0

    # ==========================================
    # SESSÃO 1: VISÃO GERAL DE VENDAS
    # ==========================================
    st.markdown("### 📊 Visão Geral de Vendas")
    
    c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1.5])
    
    with c1: criar_cartao("Novas Anuais", qtd_anual, "↕ 0% (sem alteração)", "🟢", "st-card card-anual")
    with c2: criar_cartao("Novas Semestrais", qtd_sem, "↕ 0% (sem alteração)", "🔵", "st-card card-semestral")
    with c3: criar_cartao("Novas Mensais", qtd_mensal, "↕ 0% (sem alteração)", "🟣", "st-card card-mensal")
    with c4: criar_cartao("Renovações", qtd_renovacoes, "↕ 0% (sem alteração)", "🔄", "st-card card-renovacao")
    
    # Gráfico Donut de Mix de Vendas
    with c5:
        st.markdown("<div class='st-card' style='padding-top:10px; padding-bottom:0px;'>", unsafe_allow_html=True)
        st.markdown("<div class='card-title' style='justify-content:center;'>Mix de Vendas</div>", unsafe_allow_html=True)
        
        df_mix = pd.DataFrame({
            "Plano": ["Anual", "Semestral", "Mensal", "Renovações"],
            "Quantidade": [qtd_anual, qtd_sem, qtd_mensal, qtd_renovacoes]
        })
        
        if df_mix['Quantidade'].sum() == 0:
            df_mix = pd.DataFrame({"Plano": ["Sem Dados"], "Quantidade": [1]})
            cores_mix = ["#2B2B3C"]
        else:
            cores_mix = ["#365C40", "#2D5280", "#643A8A", "#445D70"]

        fig = px.pie(df_mix, values='Quantidade', names='Plano', hole=0.6, color_discrete_sequence=cores_mix)
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            margin=dict(t=10, b=10, l=10, r=10), 
            height=130, 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # SESSÃO 2: PERFORMANCE E TRÁFEGO
    # ==========================================
    st.markdown("### 🎯 Retorno de Tráfego e Performance")
    
    p1, p2, p3, p4 = st.columns(4)
    with p1: criar_cartao("Gasto FB", f"R$ {investimento_total:,.2f}", "↕ (Período)", "💰")
    with p2: criar_cartao("Leads (Avalia)", total_leads, "↕ (Período)", "👥")
    with p3: criar_cartao("Vendas Novas", total_vendas_novas, "↕ (Período)", "🛒")
    with p4: criar_cartao("Faturamento (Novas)", f"R$ {faturamento_novas:,.2f}", "↕ (Período)", "📄")

    b1, b2, b3 = st.columns([1, 1, 2])
    with b1: criar_cartao("CPL", f"R$ {cpl:,.2f}", "↕ (Período)", "🎯")
    with b2: criar_cartao("CPA", f"R$ {cpa:,.2f}", "↕ (Período)", "💳")
    
    with b3:
        largura_barra = min((roas / 4) * 100, 100)
        html_roas = f"""
        <div class="card-roas">
            <div class="card-title">📊 ROAS (Retorno sobre Gasto)</div>
            <div style="display:flex; justify-content:space-between; align-items:flex-end;">
                <div>
                    <div class="card-value">{roas:.2f}x</div>
                    <div class="card-delta-up">Meta Base: 4.00x</div>
                </div>
                <div style="width: 50%; text-align:right;">
                    <div style="font-size:10px; color:#A0A0B5; margin-bottom:4px;">Progresso da Meta</div>
                    <div style="background-color: #2B2B3C; height: 8px; border-radius: 4px; width: 100%;">
                        <div style="background-color: #E1B12C; height: 8px; border-radius: 4px; width: {largura_barra}%;"></div>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(html_roas, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # SESSÃO 3: ANÁLISE DE RENOVAÇÕES
    # ==========================================
    st.markdown("### 🔄 Análise de Renovações por Plano")
    
    if not df_renovacoes.empty:
        # Conta a quantidade de renovações por plano
        contagem_renov = df_renovacoes['Categoria Plano'].value_counts().reset_index()
        contagem_renov.columns = ['Plano', 'Quantidade']
        
        # 🎯 NOVA PALETA DE CORES: Mais elegante, moderna e fluida com o Dark Mode
        mapa_cores = {
            'Anual': '#20B2AA',       # Light Sea Green
            'Semestral': '#4A90E2',   # Azul Moderno
            'Mensal': '#5E81AC',      # Slate Blue (Azul Acinzentado super premium)
            'Outros': '#8A8A9E'       # Cinza
        }
        
        fig_renov = px.bar(
            contagem_renov, 
            x='Plano', 
            y='Quantidade', 
            text='Quantidade',
            color='Plano',
            color_discrete_map=mapa_cores
        )
        
        largura_barra = 0.2 if len(contagem_renov) == 1 else 0.5
        
        # 🎯 CORREÇÃO DO NÚMERO CORTADO: cliponaxis=False libera o texto para fora da área de corte
        fig_renov.update_traces(
            textposition='outside', 
            textfont_size=18, 
            textfont_color='white',
            width=largura_barra,
            cliponaxis=False 
        )
        
        # 🎯 CRIA UMA FOLGA NO TOPO (Garante que o número sempre vai aparecer inteiro)
        max_y = contagem_renov['Quantidade'].max() * 1.3 if not contagem_renov.empty else 10
        
        fig_renov.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            height=300,
            margin=dict(t=40, b=20, l=10, r=10), # Aumentei a margem do topo (t=40)
            xaxis=dict(title="", showgrid=False, tickfont=dict(size=14, color='#A0A0B5')),
            yaxis=dict(title="", showgrid=False, showticklabels=False, range=[0, max_y]) 
        )
        
        st.markdown("<div class='st-card'>", unsafe_allow_html=True)
        st.plotly_chart(fig_renov, use_container_width=True, config={'displayModeBar': False})
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Nenhuma renovação registrada no período selecionado.")

    # --- SESSÃO DEBUG ---
    if mostrar_debug:
        st.markdown("---")
        st.warning("MODO DEBUG ATIVADO")
        df_leads_puro, _ = carregar_dados_planilhas(data_inicio, data_fim)
        st.dataframe(df_leads_puro.head())

if __name__ == "__main__":
    main()
