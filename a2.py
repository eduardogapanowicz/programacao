import requests
import json
import os
import pandas as pd  
from datetime import datetime  
import streamlit as st 

DATAJUD_API_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search" 
API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

def buscar_jurisprudencia_datajud(termo_busca):
    """
    Busca processos no DataJud (focado no STJ) e retorna um DataFrame do Pandas
    com os resultados formatados para exibição no Streamlit, incluindo correção de codificação.
    """
    st.info(f"Buscando por '{termo_busca}' na jurisprudência do STJ...")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {API_KEY}" 
    }
    
    payload = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": termo_busca,
                            "fields": ["assuntos.nome", "ementa", "ementaInteiroTeor", "outrosAssuntos", "assuntosProcessuais.nome"],
                            "type": "best_fields", 
                            "fuzziness": "AUTO"
                        }
                    }
                ]
            }
        },
        "size": 100, 
        "sort": [{"dataAjuizamento": "desc"}] 
    }
    
    try:
        response = requests.post(DATAJUD_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status() 
        
        dados = response.json()
        resultados = dados.get('hits', {}).get('hits', [])
        
        if not resultados:
            st.warning("❌ Nenhuma decisão judicial encontrada para este termo nos metadados do STJ.")
            st.markdown("---")
            return

        st.success(f"✅ Foram encontrados {len(resultados)} resultados para '{termo_busca}':")
        
        link_stj = "https://processo.stj.jus.br/processo/pesquisa/"
        st.markdown(f"🔗 Para consultar detalhes completos do processo, utilize o número de processo no site do STJ: [Consulta Processual STJ]({link_stj})")
        
        tabela_dados = []
        
        for hit in resultados:
            processo = hit.get('_source', {})
            
            numero_processo = processo.get("numeroProcesso", "N/A")
            classe_processual = processo.get("classe", {}).get("nome", "N/A")
            data_ajuizamento_str = processo.get("dataAjuizamento", "N/A")
            
            orgao_julgado_raw = processo.get("orgaoJulgador", {}).get("nome", "N/A")
            orgao_julgado = "N/A"
            
            if orgao_julgado_raw != "N/A":
                try:
                    bytes_latin1 = orgao_julgado_raw.encode('latin1', 'ignore')
                    orgao_julgado = bytes_latin1.decode('utf8', 'ignore').strip()
                    
                except Exception:
                    orgao_julgado = orgao_julgado_raw.strip() 

            data_formatada = "N/A"
            if data_ajuizamento_str != "N/A":
                try:
                    objeto_data = datetime.strptime(data_ajuizamento_str, '%Y%m%d%H%M%S')
                    data_formatada = objeto_data.strftime('%d/%m/%Y')
                except ValueError:
                    try:
                        data_apenas = data_ajuizamento_str.split('T')[0]
                        objeto_data = datetime.strptime(data_apenas, '%Y-%m-%d')
                        data_formatada = objeto_data.strftime('%d/%m/%Y')
                    except Exception:
                        data_formatada = "Erro Formato" 

            tabela_dados.append([
                numero_processo,
                data_formatada,
                classe_processual,
                orgao_julgado,
            ])
            
        headers_tabela = [
            "Número do Processo", 
            "Data Ajuizamento", 
            "Classe Processual", 
            "Órgão Julgador",
        ]
        
        df_resultados = pd.DataFrame(tabela_dados, columns=headers_tabela)
        st.dataframe(df_resultados)
        
    except requests.exceptions.HTTPError as errh:
        st.error(f"❌ Erro HTTP: {errh}")
    except Exception as e:
        st.error(f"❌ Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Busca Jurisprudencial STJ (DataJud)",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("⚖️ Busca Jurisprudencial DataJud (STJ)")
    st.markdown("---")

    if API_KEY == "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==":
        
        termo = st.text_input("🔍 Insira o termo ou conceito para busca jurisprudencial:", 
                              placeholder="Ex: dano moral, ICMS, overbooking",
                              key="termo_busca")
        
        if st.button("🔎 Realizar Busca"):
            if termo:
                buscar_jurisprudencia_datajud(termo)
            else:
                st.warning("Nenhum termo inserido. Por favor, digite um termo para buscar.")
    else:
        st.warning("⚠️ Atenção: Verifique se sua chave de acesso (API_KEY) está correta, caso contrário a busca falhará.")
