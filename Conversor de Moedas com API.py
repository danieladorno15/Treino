import requests
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import json
from functools import lru_cache

class ConversorMoedas:
    def __init__(self, root):
        self.root = root
        self.root.title("Conversor de Moedas - API Banco Central")
        
        # Feriados nacionais (pode ser expandido)
        self.feriados = {
            '01/01', '21/04', '01/05', '07/09', '12/10', '02/11', '15/11', '25/12'
        }
        
        # Carregar lista de moedas
        self.moedas = self.carregar_moedas()
        
        # Variáveis
        self.valor_var = tk.StringVar()
        self.de_moeda_var = tk.StringVar()
        self.para_moeda_var = tk.StringVar()
        self.data_var = tk.StringVar(value=self.ultimo_dia_util().strftime('%d/%m/%Y'))
        self.resultado_var = tk.StringVar()
        
        # Criar interface
        self.criar_interface()
    
    def ultimo_dia_util(self):
        """Retorna o último dia útil (considerando finais de semana e feriados)"""
        data = datetime.now()
        
        # Se for fim de semana, voltar para sexta-feira
        if data.weekday() >= 5:  # 5=sábado, 6=domingo
            data -= timedelta(days=data.weekday() - 4)
        
        # Verificar se é feriado
        while self.eh_feriado(data) or not self.dia_util(data):
            data -= timedelta(days=1)
        
        return data
    
    def dia_util(self, data):
        """Verifica se a data é um dia útil (segunda a sexta)"""
        return data.weekday() < 5  # 0=segunda, 4=sexta
    
    def eh_feriado(self, data):
        """Verifica se a data é um feriado nacional"""
        return data.strftime('%d/%m') in self.feriados
    
    def carregar_moedas(self):
        try:
            with open('moedas_bc.json', 'r', encoding='utf-8') as f:
                moedas = json.load(f)
                # Garante que o Real (BRL) está na lista
                moedas['BRL'] = 'Real Brasileiro'
                return moedas
        except:
            url = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/Moedas?$format=json"
            try:
                response = requests.get(url)
                data = response.json()
                moedas = {item['simbolo']: item['nomeFormatado'] for item in data['value']}
                # Adiciona o Real Brasileiro manualmente
                moedas['BRL'] = 'Real Brasileiro'
                
                with open('moedas_bc.json', 'w', encoding='utf-8') as f:
                    json.dump(moedas, f, ensure_ascii=False, indent=4)
                
                return moedas
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível carregar a lista de moedas: {str(e)}")
                return {'BRL': 'Real Brasileiro'}  # Retorna pelo menos o BRL
    
    def criar_interface(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Valor:").grid(row=0, column=0, sticky=tk.W, pady=5)
        valor_entry = ttk.Entry(main_frame, textvariable=self.valor_var, width=20)
        valor_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="De:").grid(row=1, column=0, sticky=tk.W, pady=5)
        de_moeda_cb = ttk.Combobox(main_frame, textvariable=self.de_moeda_var, width=20)
        de_moeda_cb['values'] = sorted(list(self.moedas.keys()))
        de_moeda_cb.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Para:").grid(row=2, column=0, sticky=tk.W, pady=5)
        para_moeda_cb = ttk.Combobox(main_frame, textvariable=self.para_moeda_var, width=20)
        para_moeda_cb['values'] = sorted(list(self.moedas.keys()))
        para_moeda_cb.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Data (dd/mm/aaaa):").grid(row=3, column=0, sticky=tk.W, pady=5)
        data_entry = ttk.Entry(main_frame, textvariable=self.data_var, width=20)
        data_entry.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        converter_btn = ttk.Button(main_frame, text="Converter", command=self.converter)
        converter_btn.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Label(main_frame, text="Resultado:").grid(row=5, column=0, sticky=tk.W, pady=5)
        resultado_label = ttk.Label(main_frame, textvariable=self.resultado_var, font=('Arial', 10, 'bold'))
        resultado_label.grid(row=5, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Moedas disponíveis:").grid(row=6, column=0, sticky=tk.W, pady=5)
        info_text = tk.Text(main_frame, height=10, width=50, wrap=tk.WORD)
        info_text.grid(row=7, column=0, columnspan=2, pady=5)
        
        info_text.insert(tk.END, "Lista de moedas disponíveis:\n\n")
        for simbolo, nome in sorted(self.moedas.items()):
            info_text.insert(tk.END, f"{simbolo}: {nome}\n")
        info_text.config(state=tk.DISABLED)
    
    def converter(self):
        try:
            valor = float(self.valor_var.get().replace(',', '.'))
            de_moeda = self.de_moeda_var.get()
            para_moeda = self.para_moeda_var.get()
            data_str = self.data_var.get()
            
            if not de_moeda or not para_moeda:
                raise ValueError("Selecione as moedas para conversão")
            
            if de_moeda == para_moeda:
                self.resultado_var.set(f"Resultado: {valor:.2f} {para_moeda}")
                return
            
            try:
                data = datetime.strptime(data_str, '%d/%m/%Y')
            except ValueError:
                raise ValueError("Formato de data inválido. Use dd/mm/aaaa")
            
            if data.date() > datetime.now().date():
                raise ValueError("Não é possível consultar cotações futuras")
            
            # Ajustar para último dia útil se necessário
            data_ajustada = self.ajustar_para_dia_util(data)
            if data_ajustada != data:
                messagebox.showinfo("Aviso", f"Data ajustada para {data_ajustada.strftime('%d/%m/%Y')} (último dia útil)")
            
            # Obter taxas de câmbio
            if de_moeda != 'BRL':
                taxa_de = self.obter_taxa_cambio(de_moeda, data_ajustada)
            else:
                taxa_de = 1.0
                
            if para_moeda != 'BRL':
                taxa_para = self.obter_taxa_cambio(para_moeda, data_ajustada)
            else:
                taxa_para = 1.0
            
            # Calcular conversão
            if de_moeda == 'BRL':
                resultado = valor / taxa_para
            elif para_moeda == 'BRL':
                resultado = valor * taxa_de
            else:
                # Conversão entre duas moedas estrangeiras via BRL
                valor_em_brl = valor * taxa_de
                resultado = valor_em_brl / taxa_para
            
            # Formatar resultado
            resultado_formatado = f"{resultado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            self.resultado_var.set(f"Resultado: {resultado_formatado} {para_moeda}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {str(e)}")
    
    def ajustar_para_dia_util(self, data):
        """Ajusta a data para o último dia útil válido"""
        data_original = data
        max_tentativas = 30  # Limite para evitar loop infinito
        
        while max_tentativas > 0:
            if self.dia_util(data) and not self.eh_feriado(data):
                return data
            data -= timedelta(days=1)
            max_tentativas -= 1
        
        return data_original
    
    @lru_cache(maxsize=100)
    def obter_taxa_cambio(self, moeda, data):
        """Obtém a taxa de câmbio para uma moeda específica na data informada"""
        if moeda == 'BRL':
            return 1.0
        
        data_formatada = data.strftime('%m-%d-%Y')
        url = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='{moeda}'&@dataCotacao='{data_formatada}'&$top=100&$format=json"
        
        try:
            response = requests.get(url, timeout=10)
            data_api = response.json()
            
            if 'value' in data_api and len(data_api['value']) > 0:
                return float(data_api['value'][0]['cotacaoCompra'])
            else:
                raise Exception(f"Nenhuma cotação disponível para {moeda} em {data.strftime('%d/%m/%Y')}")
        except Exception as e:
            raise Exception(f"Erro ao obter cotação para {moeda}: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConversorMoedas(root)
    root.mainloop()