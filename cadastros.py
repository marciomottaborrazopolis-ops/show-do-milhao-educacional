import json
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import tkinter.scrolledtext as scrolledtext
import os
import webbrowser
import re

# --- Bibliotecas de Leitura de Documentos ---
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from odf import opendocument, teletype
    HAS_ODT = True
except ImportError:
    HAS_ODT = False

ARQUIVO = "perguntas.json"

class AppGerenciador:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador PRO - Show do Milhão")
        self.root.geometry("1020x700") # Aumentei ligeiramente a largura para caber os botões
        self.root.configure(padx=10, pady=10)

        self.dados = self.carregar_json()
        self.indice_atual = None

        # --- Estilos Modernos ---
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam') 
        style.configure("TButton", font=("Arial", 10, "bold"), padding=6)
        style.configure("TLabel", font=("Arial", 11))
        style.configure("Title.TLabel", font=("Arial", 14, "bold"), foreground="#003399")
        style.configure("Aviso.TLabel", font=("Arial", 10, "italic"), foreground="#555555")

        # --- Sistema de Abas (Notebook) ---
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.aba_manual = ttk.Frame(self.notebook)
        self.aba_importacao = ttk.Frame(self.notebook)

        self.notebook.add(self.aba_manual, text="✏️ Editor Manual & Relatórios")
        self.notebook.add(self.aba_importacao, text="🚀 Importação Automática de Arquivos")

        self.construir_aba_manual()
        self.construir_aba_importacao()

    # ==========================================
    # ABA 1: EDITOR MANUAL E RELATÓRIOS
    # ==========================================
    def construir_aba_manual(self):
        frame_esq = tk.Frame(self.aba_manual)
        frame_esq.pack(side="left", fill="y", padx=15, pady=15)

        frame_dir = tk.Frame(self.aba_manual)
        frame_dir.pack(side="right", fill="both", expand=True, padx=15, pady=15)

        ttk.Label(frame_esq, text="📚 Banco de Perguntas:", style="Title.TLabel").pack(anchor="w", pady=(0, 10))
        scroll = tk.Scrollbar(frame_esq)
        scroll.pack(side="right", fill="y")
        self.lista = tk.Listbox(frame_esq, width=45, font=("Arial", 11), yscrollcommand=scroll.set, selectbackground="#0052cc", selectforeground="white")
        self.lista.pack(side="left", fill="y")
        scroll.config(command=self.lista.yview)
        self.lista.bind("<<ListboxSelect>>", self.selecionar)

        ttk.Label(frame_dir, text="Enunciado da Pergunta:", font=("Arial", 11, "bold")).pack(anchor="w")
        self.pergunta_entry = tk.Entry(frame_dir, font=("Arial", 12))
        self.pergunta_entry.pack(fill="x", pady=(5, 10))

        ttk.Label(frame_dir, text="Nível de Dificuldade:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(5, 5))
        self.dificuldade_var = tk.StringVar(value="Fácil")
        self.dificuldade_cb = ttk.Combobox(frame_dir, textvariable=self.dificuldade_var, values=["Fácil", "Médio", "Difícil"], state="readonly", font=("Arial", 11))
        self.dificuldade_cb.pack(anchor="w", pady=(0, 15))

        ttk.Label(frame_dir, text="Alternativas (Marque a correta):", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0, 10))

        self.opcoes_entries = []
        self.resposta_var = tk.IntVar()
        self.resposta_var.set(-1)

        for i in range(4):
            frame_op = tk.Frame(frame_dir)
            frame_op.pack(anchor="w", fill="x", pady=4)
            rb = tk.Radiobutton(frame_op, variable=self.resposta_var, value=i, cursor="hand2")
            rb.pack(side="left")
            ttk.Label(frame_op, text=f"Opção {i+1}:", width=8).pack(side="left")
            entry = tk.Entry(frame_op, font=("Arial", 12))
            entry.pack(side="left", fill="x", expand=True, padx=5)
            self.opcoes_entries.append(entry)

        # Barra de Botões Atualizada
        frame_btn = tk.Frame(frame_dir)
        frame_btn.pack(pady=30, anchor="w")

        ttk.Button(frame_btn, text="➕ Nova", command=self.novo).pack(side="left", padx=2)
        ttk.Button(frame_btn, text="💾 Salvar", command=self.salvar).pack(side="left", padx=2)
        ttk.Button(frame_btn, text="🗑 Excluir", command=self.excluir).pack(side="left", padx=2)
        ttk.Button(frame_btn, text="🧹 Remover Repetidas", command=self.remover_duplicadas).pack(side="left", padx=2)
        ttk.Button(frame_btn, text="🖨️ Relatório", command=self.gerar_relatorio).pack(side="left", padx=(15, 0))

        self.atualizar_lista()

    # ==========================================
    # ABA 2: IMPORTAÇÃO AUTOMÁTICA
    # ==========================================
    def construir_aba_importacao(self):
        container = tk.Frame(self.aba_importacao, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        titulo = "Importe um arquivo de questões (PDF, DOCX, ODT ou TXT)"
        ttk.Label(container, text=titulo, style="Title.TLabel").pack(anchor="w")
        
        instrucoes = (
            "Selecione o arquivo do seu computador ou COPIE E COLE o texto na caixa abaixo.\n"
            "O padrão exigido é o formato de lista (separe as perguntas pulando uma linha):\n\n"
            "1. Qual a capital do Brasil?\n"
            "a) Rio de Janeiro\n"
            "b) São Paulo\n"
            "c) Brasília\n"
            "d) Salvador\n"
            "Resposta: c"
        )
        ttk.Label(container, text=instrucoes, style="Aviso.TLabel").pack(anchor="w", pady=(5, 10))

        # Botões de Ação de Importação
        frame_acao_imp = tk.Frame(container)
        frame_acao_imp.pack(fill="x", pady=5)
        
        ttk.Button(frame_acao_imp, text="📂 Selecionar Arquivo do Computador", command=self.carregar_arquivo).pack(side="left", pady=5)

        # Área de Texto
        self.texto_importacao = scrolledtext.ScrolledText(container, wrap=tk.WORD, width=80, height=12, font=("Arial", 11))
        self.texto_importacao.pack(fill="both", expand=True, pady=5)

        # Nível padrão e Processamento
        frame_rodape_imp = tk.Frame(container)
        frame_rodape_imp.pack(fill="x", pady=10)
        
        ttk.Label(frame_rodape_imp, text="Classificar novas questões como:", font=("Arial", 10, "bold")).pack(side="left", padx=(0,10))
        self.dif_importacao_var = tk.StringVar(value="Médio")
        ttk.Combobox(frame_rodape_imp, textvariable=self.dif_importacao_var, values=["Fácil", "Médio", "Difícil"], state="readonly", width=15).pack(side="left")

        ttk.Button(frame_rodape_imp, text="⚙️ Analisar Texto e Importar Questões", command=self.processar_importacao).pack(side="right")

    # ==========================================
    # LÓGICA DE FUNCIONAMENTO
    # ==========================================
    def carregar_arquivo(self):
        tipos = [
            ("Arquivos de Documento", "*.pdf *.docx *.odt *.txt"),
            ("Documentos Word Modernos", "*.docx"),
            ("Arquivos PDF", "*.pdf"),
            ("OpenDocument Text", "*.odt"),
            ("Arquivos de Texto", "*.txt"),
            ("Todos os Arquivos", "*.*")
        ]
        
        caminho = filedialog.askopenfilename(title="Selecione o arquivo com as questões", filetypes=tipos)
        
        if not caminho:
            return
            
        extensao = caminho.lower().split('.')[-1]
        texto_extraido = ""
        
        try:
            if extensao == "txt":
                with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
                    texto_extraido = f.read()
            elif extensao == "pdf":
                if not HAS_PDF:
                    messagebox.showerror("Erro de Dependência", "Para ler PDF, instale a biblioteca PyPDF2.")
                    return
                with open(caminho, "rb") as f:
                    leitor = PyPDF2.PdfReader(f)
                    for pagina in leitor.pages:
                        txt = pagina.extract_text()
                        if txt: texto_extraido += txt + "\n\n"
            elif extensao == "docx":
                if not HAS_DOCX:
                    messagebox.showerror("Erro de Dependência", "Para ler Word, instale a biblioteca python-docx.")
                    return
                doc = docx.Document(caminho)
                for paragrafo in doc.paragraphs:
                    texto_extraido += paragrafo.text + "\n"
            elif extensao == "odt":
                if not HAS_ODT:
                    messagebox.showerror("Erro de Dependência", "Para ler ODT, instale a biblioteca odfpy.")
                    return
                doc = opendocument.load(caminho)
                texto_extraido = teletype.extractText(doc)
            else:
                messagebox.showerror("Erro", "Formato não suportado.")
                return

            self.texto_importacao.delete("1.0", tk.END)
            self.texto_importacao.insert(tk.END, texto_extraido)
            messagebox.showinfo("Sucesso", "Arquivo lido! Revise o texto extraído na caixa abaixo e depois clique no botão de Analisar e Importar.")
            
        except Exception as e:
            messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo.\nDetalhe do erro: {str(e)}")

    def carregar_json(self):
        if not os.path.exists(ARQUIVO): return []
        try:
            with open(ARQUIVO, "r", encoding="utf-8") as f: return json.load(f)
        except: return []

    def salvar_json(self):
        with open(ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(self.dados, f, indent=4, ensure_ascii=False)

    def atualizar_lista(self):
        self.lista.delete(0, tk.END)
        for i, item in enumerate(self.dados):
            dif = item.get('dificuldade', 'Fácil')[:3]
            txt = f"{i+1}. [{dif}] {item['pergunta'][:40]}..." if len(item['pergunta']) > 40 else f"{i+1}. [{dif}] {item['pergunta']}"
            self.lista.insert(tk.END, txt)

    def selecionar(self, event):
        if not self.lista.curselection(): return
        index = self.lista.curselection()[0]
        self.indice_atual = index
        item = self.dados[index]

        self.pergunta_entry.delete(0, tk.END)
        self.pergunta_entry.insert(0, item["pergunta"])
        self.dificuldade_var.set(item.get("dificuldade", "Fácil"))

        for i in range(4):
            self.opcoes_entries[i].delete(0, tk.END)
            self.opcoes_entries[i].insert(0, item["opcoes"][i])
        self.resposta_var.set(item["resposta"])

    def novo(self):
        self.indice_atual = None
        self.lista.selection_clear(0, tk.END) 
        self.pergunta_entry.delete(0, tk.END)
        self.dificuldade_var.set("Fácil")
        for entry in self.opcoes_entries: entry.delete(0, tk.END)
        self.resposta_var.set(-1)

    def salvar(self):
        perg = self.pergunta_entry.get().strip()
        dif = self.dificuldade_var.get()
        opts = [e.get().strip() for e in self.opcoes_entries]
        resp = self.resposta_var.get()

        if not perg or "" in opts or resp == -1:
            messagebox.showwarning("Atenção", "Preencha todos os campos e marque a resposta correta.")
            return

        item = {"pergunta": perg, "dificuldade": dif, "opcoes": opts, "resposta": resp}
        
        if self.indice_atual is None:
            self.dados.append(item)
            messagebox.showinfo("Sucesso", "Pergunta adicionada!")
        else:
            self.dados[self.indice_atual] = item
            messagebox.showinfo("Sucesso", "Pergunta atualizada!")

        self.salvar_json()
        self.atualizar_lista()
        self.novo()

    def excluir(self):
        if self.indice_atual is None: return
        if messagebox.askyesno("Confirmar", "Deseja excluir esta pergunta?"):
            del self.dados[self.indice_atual]
            self.salvar_json()
            self.atualizar_lista()
            self.novo()

    # --- NOVA FUNÇÃO: REMOVER REPETIDAS ---
    def remover_duplicadas(self):
        if not self.dados:
            messagebox.showinfo("Aviso", "O banco de perguntas está vazio.")
            return

        perguntas_unicas = []
        textos_vistos = set()
        quantidade_removida = 0

        for item in self.dados:
            # Normaliza o texto (tudo em minúsculas e sem espaços extra nas pontas) para comparar melhor
            texto_normalizado = item["pergunta"].strip().lower()
            
            if texto_normalizado not in textos_vistos:
                textos_vistos.add(texto_normalizado)
                perguntas_unicas.append(item)
            else:
                quantidade_removida += 1

        if quantidade_removida > 0:
            self.dados = perguntas_unicas
            self.salvar_json()
            self.atualizar_lista()
            self.novo() # Limpa os campos da tela
            messagebox.showinfo("Limpeza Concluída", f"Sucesso! Foram encontradas e removidas {quantidade_removida} perguntas repetidas do seu banco de dados.")
        else:
            messagebox.showinfo("Verificação Concluída", "Ótimas notícias! O seu banco de dados não tem nenhuma pergunta repetida.")

    def gerar_relatorio(self):
        if not self.dados:
            messagebox.showwarning("Atenção", "Banco de perguntas vazio!")
            return
            
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8"><title>Gabarito Oficial</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; color: #333; }
                h1 { color: #003399; text-align: center; border-bottom: 2px solid #003399; padding-bottom: 10px; }
                .card { border: 1px solid #ddd; padding: 15px; margin-bottom: 20px; border-radius: 8px; background-color: #f9f9f9; }
                .nivel { font-weight: bold; color: #d9534f; font-size: 0.9em; margin-top: -10px; margin-bottom: 10px; }
                .correta { font-weight: bold; color: #28a745; }
                ul { list-style-type: none; padding-left: 0; }
                @media print { .card { page-break-inside: avoid; border: 1px solid #000; } }
            </style>
        </head><body>
            <h1>📚 Gabarito Oficial - Show do Milhão</h1>
        """
        for i, p in enumerate(self.dados):
            dif = p.get('dificuldade', 'Fácil')
            html += f"<div class='card'><h3>{i+1}. {p['pergunta']}</h3><div class='nivel'>Nível: {dif}</div><ul>"
            for j, opt in enumerate(p['opcoes']):
                if j == p['resposta']: html += f"<li class='correta'> ➡️ {chr(65+j)}) {opt} (CORRETA) </li>"
                else: html += f"<li> &nbsp;&nbsp;&nbsp; {chr(65+j)}) {opt} </li>"
            html += "</ul></div>"
        html += "</body></html>"

        caminho = os.path.abspath("relatorio_gabarito.html")
        with open(caminho, "w", encoding="utf-8") as f: f.write(html)
        webbrowser.open(f"file://{caminho}")

    # --- MOTOR DE IMPORTAÇÃO AUTOMÁTICA ---
    def processar_importacao(self):
        texto_bruto = self.texto_importacao.get("1.0", tk.END).strip()
        if not texto_bruto:
            messagebox.showwarning("Atenção", "Cole o texto formatado na caixa primeiro!")
            return

        perguntas_encontradas = []
        dificuldade_escolhida = self.dif_importacao_var.get()
        
        # Divide o texto do documento usando quebras de linha duplas
        blocos = re.split(r'\n\s*\n', texto_bruto)
        
        for bloco in blocos:
            # Pega todas as linhas que não são vazias dentro do bloco
            linhas = [l.strip() for l in bloco.split('\n') if l.strip()]
            
            # Condição básica: uma pergunta, 4 opções e 1 resposta (mínimo de 6 linhas no bloco)
            if len(linhas) >= 6:
                pergunta = linhas[0]
                pergunta = re.sub(r'^\d+[-\.)]\s*', '', pergunta) # Tira o número do começo (ex: "1. ")
                
                opcoes = []
                resposta_idx = -1
                
                for linha in linhas[1:]:
                    linha_low = linha.lower()
                    if linha_low.startswith(('a)', 'a-', 'a.')): opcoes.append(linha[2:].strip())
                    elif linha_low.startswith(('b)', 'b-', 'b.')): opcoes.append(linha[2:].strip())
                    elif linha_low.startswith(('c)', 'c-', 'c.')): opcoes.append(linha[2:].strip())
                    elif linha_low.startswith(('d)', 'd-', 'd.')): opcoes.append(linha[2:].strip())
                    elif linha_low.startswith('resposta'):
                        try:
                            letra = linha_low.split(':')[1].strip().lower()
                            mapa = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
                            resposta_idx = mapa.get(letra, -1)
                        except:
                            pass
                        
                if len(opcoes) == 4 and resposta_idx != -1:
                    perguntas_encontradas.append({
                        "pergunta": pergunta,
                        "dificuldade": dificuldade_escolhida,
                        "opcoes": opcoes,
                        "resposta": resposta_idx
                    })

        if not perguntas_encontradas:
            messagebox.showerror("Erro de Formatação", "Não consegui identificar as perguntas.\n\nVerifique se o texto na caixa tem uma linha em branco entre cada questão e se as respostas terminam com 'Resposta: a', por exemplo.")
            return

        confirma = messagebox.askyesno("Confirmar Importação", f"Consegui ler {len(perguntas_encontradas)} perguntas do seu arquivo.\nDeseja adicioná-las ao seu banco de dados oficial?")
        if confirma:
            self.dados.extend(perguntas_encontradas)
            self.salvar_json()
            self.atualizar_lista()
            self.texto_importacao.delete("1.0", tk.END)
            self.notebook.select(self.aba_manual)
            messagebox.showinfo("Sucesso", "Questões importadas com sucesso! Você já pode gerar o relatório ou ir para o jogo.")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppGerenciador(root)
    root.mainloop()