import pandas as pd
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount

# ==========================================
# CREDENCIAIS DA API
# ==========================================
APP_ID = '2205037596979712'
APP_SECRET = '9c89d88daf3845f5e96f9553219b8f43'
ACCESS_TOKEN = 'EAAfVeFKvMgABROAWy0JdkRO4M5YVDk6cGZBMUt5RNpJ7dsz4TTd6NMB6X8jr8Lw9b3ZCPYIgLyZABGmx5Wy4VzE9kktlbB2zrXr4XmdWz2ZAMCe9gHOxK6CyrZAp8EC2joKiWbBQIiYl65gJYsKCcn5KeekILGEiAUDFN6i98ZBk8pZCaMM8ZBAQ1PIgqSmM'
AD_ACCOUNT_ID = 'act_1055611486646226'

def get_facebook_data(data_inicio, data_fim):
    FacebookAdsApi.init(APP_ID, APP_SECRET, ACCESS_TOKEN)
    account = AdAccount(AD_ACCOUNT_ID)
    
    fields = ['campaign_name', 'spend', 'impressions', 'clicks', 'ctr', 'cpc']
    
    # Parâmetro novo: O Facebook agora filtra as datas que você escolher no Dashboard!
    params = {
        'level': 'campaign', 
        'time_range': {
            'since': data_inicio.strftime('%Y-%m-%d'),
            'until': data_fim.strftime('%Y-%m-%d')
        }
    } 
    
    insights = account.get_insights(fields=fields, params=params)
    dados = []
    
    for item in insights:
        nome_campanha = item.get('campaign_name', '')
        if "Avalia" in nome_campanha:
            dados.append({
                'Investimento': float(item.get('spend', 0)),
                'Cliques': int(item.get('clicks', 0)),
            })
            
    return pd.DataFrame(dados)