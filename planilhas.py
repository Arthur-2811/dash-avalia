import pandas as pd
import streamlit as st
import gspread

def conectar_google():
    if "gcp_service_account" in st.secrets:
        return gspread.service_account_from_dict(dict(st.secrets["gcp_service_account"]))
    elif "google_credentials" in st.secrets:
        return gspread.service_account_from_dict(dict(st.secrets["google_credentials"]))
    else:
        return gspread.service_account_from_dict(dict(st.secrets))

def get_sheets_data(data_inicio, data_fim):
    client = conectar_google()
    
    dt_inicio = pd.to_datetime(data_inicio).date()
    dt_fim = pd.to_datetime(data_fim).date()

    ID_LEADS = "1970VtmLGONWYih6sF7lbqf275wTgoE67IdJp9eeAoO0"
    ID_VENDAS = "19CmIQYKZlfOF9PEou32urgiKMBLmli7xejU2_0XCFg0"

    # ==========================
    # TRATAMENTO DE LEADS
    # ==========================
    try:
        aba_leads = client.open_by_key(ID_LEADS).worksheet("Lead")
        df_leads = pd.DataFrame(aba_leads.get_all_records())
        
        if not df_leads.empty:
            df_leads['Data e Hora'] = pd.to_datetime(df_leads['Data e Hora'], errors='coerce')
            df_leads = df_leads.dropna(subset=['Data e Hora'])
            
            df_leads = df_leads[(df_leads['Data e Hora'].dt.date >= dt_inicio) & (df_leads['Data e Hora'].dt.date <= dt_fim)]
            
            if 'first name' in df_leads.columns:
                df_leads_avalia = df_leads[df_leads['first name'].astype(str).str.strip() != ""]
            else:
                df_leads_avalia = df_leads
        else:
            df_leads_avalia = pd.DataFrame()
    except Exception as e:
        st.error(f"Erro Leads: {e}")
        df_leads_avalia = pd.DataFrame()

    # ==========================
    # TRATAMENTO DE VENDAS
    # ==========================
    try:
        aba_vendas = client.open_by_key(ID_VENDAS).worksheet("CA - LANC NOV AVALIA NR01")
        df_vendas = pd.DataFrame(aba_vendas.get_all_records())
        
        if not df_vendas.empty:
            df_vendas['Data e Hora'] = pd.to_datetime(df_vendas['Data e Hora'], dayfirst=True, errors='coerce')
            df_vendas = df_vendas.dropna(subset=['Data e Hora'])
            
            df_vendas = df_vendas.sort_values('Data e Hora')
            df_vendas['É Renovação'] = df_vendas.duplicated(subset=['Email'], keep='first')
            
            df_vendas = df_vendas[(df_vendas['Data e Hora'].dt.date >= dt_inicio) & (df_vendas['Data e Hora'].dt.date <= dt_fim)]
            
            def limpar_moeda(valor):
                if pd.isna(valor) or str(valor).strip() == '': return 0.0
                if isinstance(valor, (int, float)): return float(valor)
                
                v = str(valor).upper().replace('R$', '').strip()
                
                if '.' in v and ',' in v:
                    v = v.replace('.', '').replace(',', '.')
                elif ',' in v:
                    v = v.replace(',', '.')
                
                try: 
                    return float(v)
                except: 
                    return 0.0
            
            df_vendas['Valor bruto'] = df_vendas['Valor bruto'].apply(limpar_moeda)
            
            def classificar_plano(nome):
                n = str(nome).upper().replace('Ê', 'E') 
                
                if 'SEMESTRAL' in n or 'SEMESTRE' in n: 
                    return 'Semestral'
                
                if 'MENSAL' in n or 'MES' in n or '7 DIAS' in n: 
                    return 'Mensal'
                
                if 'ANUAL' in n or ('ANO' in n and 'PLANO ' not in n) or '12 MESES' in n: 
                    return 'Anual'
                    
                return 'Outros'
                
            df_vendas['Categoria Plano'] = df_vendas['Plano'].apply(classificar_plano)
        else:
            df_vendas = pd.DataFrame()
    except Exception as e:
        st.error(f"Erro Vendas: {e}")
        df_vendas = pd.DataFrame()

    return df_leads_avalia, df_vendas