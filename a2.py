import requests
import json
import os
from tabulate import tabulate 
from datetime import datetime 

DATAJUD_API_URL = "https://api-publica.datajud.cnj.jus.br/api_publica_stj/_search" 
API_KEY = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="

def buscar_jurisprudencia_datajud(termo_busca):
    """
    Busca processos no DataJud (focado no STJ) usando um payload de busca otimizado e
    apresenta os resultados em uma tabela formatada, com a data em DD/MM/YYYY e
    correção de caracteres especiais no Órgão Julgador.
    """
    print(f"Buscando por '{termo_busca}' no STJ (Endpoint: {DATAJUD_API_URL})...")
    
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
            print("❌ Nenhuma decisão judicial encontrada para este termo nos metadados do STJ.")
            print("---")
            return

        print(f"\n✅ Foram encontrados {len(resultados)} resultados para '{termo_busca}':\n")
        
        link_stj = "https://processo.stj.jus.br/processo/pesquisa/"
        print(f"🔗 Para consultar detalhes completos do processo, utilize o número de processo no site do STJ: [Consulta Processual STJ]({link_stj})\n")
        
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
                    orgao_julgado = orgao_julgado_raw.encode('latin-1', 'ignore').decode('utf-8', 'ignore')
                except Exception:
                    orgao_julgado = orgao_julgado_raw 
            
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
        
        print(tabulate(tabela_dados, headers=headers_tabela, tablefmt="pipe"))
        
    except requests.exceptions.HTTPError as errh:
        print(f"❌ Erro HTTP: {errh}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")

if __name__ == "__main__":
    if API_KEY == "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw==":
        termo = input("🔍 Insira o termo ou conceito para busca jurisprudencial: ")
        
        if termo:
            buscar_jurisprudencia_datajud(termo)
        else:
            print("Nenhum termo inserido. Encerrando o programa.")
    else:
        print("⚠️ Atenção: Verifique se sua chave de acesso (API_KEY) está correta, caso contrário a busca falhará.")

# Exemplos de termos/conceitos: dano moral, ICMS, overbooking, aborto, princípio da insignificância.
