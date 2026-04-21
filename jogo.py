import pygame
import sys
import random
import json
import os

# Tenta importar o OpenCV para rodar o vídeo
try:
    import cv2
    TEM_CV2 = True
except ImportError:
    TEM_CV2 = False
    print("Aviso: 'opencv-python' não instalado. Instale com: pip install opencv-python")

pygame.init()
pygame.mixer.init()

# ===== CONFIGURAÇÕES DA TELA =====
largura, altura = 1050, 700
tela = pygame.display.set_mode((largura, altura))
pygame.display.set_caption("Show do Milhão - Edição Escola Augusto Bahls")

# Fontes
fonte_pergunta = pygame.font.SysFont("Arial", 26, bold=True)
fonte_opcao = pygame.font.SysFont("Arial", 24, bold=True)
fonte_ajuda = pygame.font.SysFont("Arial", 20, bold=True)
fonte_premios = pygame.font.SysFont("Arial", 22, bold=True)
fonte_pequena = pygame.font.SysFont("Arial", 16, bold=True)
fonte_titulo_ajuda = pygame.font.SysFont("Arial", 40, bold=True)
fonte_cronometro = pygame.font.SysFont("Arial", 40, bold=True)

# Cores
COR_FUNDO = (0, 0, 80)
COR_VERMELHO = (180, 0, 0)
COR_AZUL_BOTAO = (0, 50, 180)
COR_AMARELO = (255, 215, 0)
COR_PRATA = (200, 200, 200)
COR_TEXTO = (255, 255, 255)
COR_DESATIVADO = (80, 80, 80)
COR_SELECAO = (255, 215, 0)  # Amarelo para sinalizar o 1º clique (seleção pendente)  
COR_ACERTO = (0, 200, 0)     # Verde claro para acerto confirmado
COR_ERRO = (255, 50, 50)     

premios = ["1 MIL", "2 MIL", "3 MIL", "4 MIL", "5 MIL", "10 MIL", "20 MIL", "30 MIL", "40 MIL", "50 MIL", "100 MIL", "500 MIL", "1 MILHÃO"]

# ===== CARREGAR MÍDIAS =====
arquivos_som = {
    "abertura_video": "silvio-santos-abertura-show-do-milhao.mp3", 
    "encerra": "encerra.mp3",
    "acerto": "silvio-santos-certa-resposta.mp3",
    "erro": "erro.mp3", 
    "posso_perguntar": "silvio-santos-posso-perguntar.mp3",
    "certeza": "silvio-santos-esta-certo-disso.mp3",
    "tempo_acabou": "silvio-santos-o-seu-tempo-acabou.mp3",
    "milhao": "silvio-santos-parabens-voce-acaba-de-ganhar-1-milhao-de-reais.mp3",
    "perdeu": "voce_perdeu.mp3"
}

sons = {ch: pygame.mixer.Sound(arq) for ch, arq in arquivos_som.items() if os.path.exists(arq)}

def tocar_som(nome):
    if nome in sons: sons[nome].play()

def reproduzir_video(caminho):
    if not TEM_CV2 or not os.path.exists(caminho): return
    cap = cv2.VideoCapture(caminho)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    relogio_v = pygame.time.Clock()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_py = pygame.image.frombuffer(frame.tobytes(), (frame.shape[1], frame.shape[0]), "RGB")
        tela.blit(pygame.transform.scale(frame_py, (largura, altura)), (0, 0))
        pygame.display.flip()
        for ev in pygame.event.get():
            if ev.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]: cap.release(); return
        relogio_v.tick(fps)
    cap.release()

# Imagens
try:
    imagem_fundo_inicio = pygame.transform.scale(pygame.image.load("Show do Milhao Digit.jpg"), (largura, altura))
except: imagem_fundo_inicio = None

try:
    carta_verso = pygame.transform.scale(pygame.image.load("card4.jpg"), (80, 110))
except: carta_verso = None

cartas_frentes = []
for i in range(1, 4):
    arq = f"card{i}.jpg"
    if os.path.exists(arq): cartas_frentes.append(pygame.transform.scale(pygame.image.load(arq), (80, 110)))

# ===== LÓGICA DE JOGO =====
def carregar_perguntas(arq):
    try:
        with open(arq, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

todas_perguntas = carregar_perguntas("perguntas.json")
random.shuffle(todas_perguntas)

# Variáveis Globais
estado_jogo = "INICIO" 
indice_pergunta = 0
nivel_premio = 0
jogadores = []
convidados_nomes = []
jogador_ativo = 0
texto_input = ""
aba_cadastro = "EQUIPES" 
tempo_restante_ms = 60000

alternativa_selecionada = None
som_alternancia = True
botao_clicado = None
cor_feedback = None
motivo_fim = ""

# Ajudas e Sistema de Rodadas
opcoes_ocultas = []
exibir_cartas_modo = False
valores_cartas_sorteados = []
texto_ajuda_convidados = "" 
dados_placas = None

# Configuração dos Blocos (Rodadas)
limites_blocos = [50, 30, 20, 20]
nomes_blocos = ["1ª RODADA (50 Questões)", "2ª RODADA (30 Questões)", "3ª RODADA (20 Questões)", "DESEMPATE (20 Questões)"]
bloco_atual = 0
perguntas_no_bloco = 0
equipe_editando = None
origem_reconfig = "" 

def avancar_pergunta(acertou=False):
    global indice_pergunta, perguntas_no_bloco, estado_jogo, nivel_premio
    global opcoes_ocultas, alternativa_selecionada, botao_clicado, cor_feedback
    global tempo_restante_ms, dados_placas, texto_ajuda_convidados, motivo_fim
    
    if acertou: nivel_premio += 1
    indice_pergunta += 1
    perguntas_no_bloco += 1
    
    opcoes_ocultas = []
    alternativa_selecionada = None
    botao_clicado = None
    cor_feedback = None
    tempo_restante_ms = 60000
    dados_placas = None
    texto_ajuda_convidados = ""

    if indice_pergunta >= len(todas_perguntas):
        estado_jogo = "FIM"
        motivo_fim = "O BANCO DE PERGUNTAS ESGOTOU!"
    elif bloco_atual < len(limites_blocos) and perguntas_no_bloco >= limites_blocos[bloco_atual]:
        estado_jogo = "FIM_BLOCO"
    else:
        estado_jogo = "JOGANDO"

# ===== FUNÇÕES DE DESENHO =====
def desenhar_botao(x, y, w, h, cor, texto, fonte, cor_txt=COR_TEXTO, numero=None):
    pygame.draw.rect(tela, (100, 100, 100), (x, y, w, h), border_radius=15)
    pygame.draw.rect(tela, cor, (x+4, y+4, w-8, h-8), border_radius=10)
    if numero:
        pygame.draw.circle(tela, COR_FUNDO, (x + 35, y + h//2), 18)
        n_surf = fonte_pergunta.render(str(numero), True, COR_TEXTO)
        tela.blit(n_surf, n_surf.get_rect(center=(x + 35, y + h//2)))
        t_surf = fonte.render(texto, True, cor_txt)
        tela.blit(t_surf, (x + 70, y + h//2 - t_surf.get_height()//2))
    else:
        t_surf = fonte.render(texto, True, cor_txt)
        tela.blit(t_surf, t_surf.get_rect(center=(x + w/2, y + h/2)))
    return pygame.Rect(x, y, w, h)

def formatar_premio(indice):
    if indice < len(premios): return premios[indice]
    return "1 MILHÃO"

def quebrar_texto(texto, fonte, largura_maxima):
    palavras = texto.split(' ')
    linhas, linha_atual = [], ""
    for p in palavras:
        teste = linha_atual + p + " "
        if fonte.size(teste)[0] < largura_maxima: linha_atual = teste
        else: linhas.append(linha_atual); linha_atual = p + " "
    linhas.append(linha_atual)
    return linhas

# ===== LOOP PRINCIPAL =====
clock = pygame.time.Clock()
while True:
    dt = clock.tick(60)
    eventos = pygame.event.get()
    for ev in eventos:
        if ev.type == pygame.QUIT: pygame.quit(); sys.exit()

    if estado_jogo == "INICIO":
        pygame.mixer.stop()
        if imagem_fundo_inicio: tela.blit(imagem_fundo_inicio, (0, 0))
        btn_config = desenhar_botao(largura//2 - 150, altura - 120, 300, 80, COR_AZUL_BOTAO, "CADASTRAR E JOGAR", fonte_ajuda)
        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN and btn_config.collidepoint(ev.pos): estado_jogo = "CADASTRO"

    elif estado_jogo == "CADASTRO":
        tela.fill(COR_FUNDO)
        titulo = fonte_titulo_ajuda.render("CADASTRO DE PARTICIPANTES", True, COR_AMARELO)
        tela.blit(titulo, titulo.get_rect(center=(largura/2, 50)))
        
        c_eq = (0, 150, 0) if aba_cadastro == "EQUIPES" else (80, 80, 80)
        c_cv = (0, 150, 0) if aba_cadastro == "CONVIDADOS" else (80, 80, 80)
        btn_eq = desenhar_botao(largura/2-250, 100, 240, 40, c_eq, "Destino: EQUIPES", fonte_pequena)
        btn_cv = desenhar_botao(largura/2+10, 100, 240, 40, c_cv, "Destino: CONVIDADOS", fonte_pequena)
        
        pygame.draw.rect(tela, (255, 255, 255), (largura/2-250, 150, 500, 45), border_radius=10)
        tela.blit(fonte_pergunta.render(texto_input, True, (0, 0, 0)), (largura/2-240, 158))
        
        tela.blit(fonte_pequena.render("LISTA DE EQUIPES (Máx 9):", True, COR_AMARELO), (80, 220))
        for i, j in enumerate(jogadores):
            desenhar_botao(80 + (i%2)*250, 250 + (i//2)*45, 240, 35, (50,50,50), f"{i+1}. {j['nome']}", fonte_pequena)

        tela.blit(fonte_pequena.render("LISTA DE UNIVERSITÁRIOS (Máx 3):", True, COR_AMARELO), (650, 220))
        for i, c in enumerate(convidados_nomes):
            desenhar_botao(650, 250 + i*45, 300, 35, (50,50,50), f"Univ {i+1}: {c}", fonte_pequena)

        btn_go = None
        if jogadores: btn_go = desenhar_botao(largura/2-150, altura-100, 300, 60, (0,150,0), "INICIAR JOGO", fonte_pergunta)
        
        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if btn_eq.collidepoint(ev.pos): aba_cadastro = "EQUIPES"; texto_input = ""
                if btn_cv.collidepoint(ev.pos): aba_cadastro = "CONVIDADOS"; texto_input = ""
                
                if btn_go and btn_go.collidepoint(ev.pos):
                    pygame.mixer.stop()
                    if TEM_CV2 and os.path.exists("abertura.mp4"):
                        tocar_som("abertura_video"); reproduzir_video("abertura.mp4"); pygame.mixer.stop() 
                    estado_jogo = "JOGANDO"
                    tempo_restante_ms = 60000
            
            if ev.type == pygame.TEXTINPUT:
                if len(texto_input) < 18: texto_input += ev.text
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN and texto_input.strip():
                    if aba_cadastro == "EQUIPES" and len(jogadores) < 9: 
                        jogadores.append({"nome": texto_input.strip(), "pontos": 0, "pulos": 3, "cartas": False, "placas": False, "convidados": False})
                    elif aba_cadastro == "CONVIDADOS" and len(convidados_nomes) < 3: 
                        convidados_nomes.append(texto_input.strip())
                    texto_input = ""
                elif ev.key == pygame.K_BACKSPACE: texto_input = texto_input[:-1]

    elif estado_jogo == "FIM_BLOCO":
        tela.fill(COR_FUNDO)
        txt = fonte_titulo_ajuda.render(f"FIM DA {nomes_blocos[bloco_atual]}", True, COR_AMARELO)
        tela.blit(txt, txt.get_rect(center=(largura/2, 150)))
        
        btn_next = None
        if bloco_atual + 1 < len(limites_blocos):
            btn_next = desenhar_botao(largura/2-250, 250, 500, 60, (0,150,0), f"INICIAR {nomes_blocos[bloco_atual+1]}", fonte_pergunta)
        
        btn_rank_fim = desenhar_botao(largura/2-250, 350, 500, 60, COR_AMARELO, "IR PARA O RANKING", fonte_pergunta, (0,0,0))
        btn_editar = desenhar_botao(largura/2-250, 450, 500, 60, COR_AZUL_BOTAO, "RECONFIGURAR EQUIPES", fonte_pergunta)
        
        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if btn_next and btn_next.collidepoint(ev.pos):
                    bloco_atual += 1
                    perguntas_no_bloco = 0
                    estado_jogo = "JOGANDO"
                if btn_rank_fim.collidepoint(ev.pos):
                    origem_reconfig = "FIM_BLOCO"
                    estado_jogo = "RANKING_PAUSA"
                if btn_editar.collidepoint(ev.pos):
                    origem_reconfig = "FIM_BLOCO"
                    texto_input = ""
                    equipe_editando = None
                    estado_jogo = "RECONFIGURAR"

    elif estado_jogo == "RECONFIGURAR":
        tela.fill(COR_FUNDO)
        titulo = fonte_titulo_ajuda.render("RECONFIGURAR PARTICIPANTES", True, COR_AMARELO)
        tela.blit(titulo, titulo.get_rect(center=(largura/2, 50)))
        tela.blit(fonte_ajuda.render("Selecione uma equipe para editar ou excluir, ou digite uma nova.", True, COR_PRATA), (150, 100))
        
        pygame.draw.rect(tela, (255, 255, 255), (largura/2 - 250, 140, 500, 40), border_radius=5)
        tela.blit(fonte_pergunta.render(texto_input, True, (0,0,0)), (largura/2 - 240, 145))
        
        botoes_edicao = []
        for i, jog in enumerate(jogadores):
            cor_ed = COR_SELECAO if i == equipe_editando else (50,50,50)
            r_ed = desenhar_botao(50 + (i%3)*320, 210 + (i//3)*50, 300, 40, cor_ed, f"{jog['nome']} ({jog['pontos']} pts)", fonte_pequena)
            botoes_edicao.append(r_ed)
            
        btn_add = desenhar_botao(largura/2 - 320, 450, 200, 50, (0, 150, 0), "NOVA EQUIPE", fonte_pequena)
        btn_salvar = desenhar_botao(largura/2 - 100, 450, 200, 50, COR_AZUL_BOTAO, "ATUALIZAR NOME", fonte_pequena)
        btn_del = desenhar_botao(largura/2 + 120, 450, 200, 50, COR_VERMELHO, "EXCLUIR EQUIPE", fonte_pequena)
        
        btn_voltar = desenhar_botao(largura/2 - 150, 550, 300, 60, COR_AZUL_BOTAO, "VOLTAR", fonte_pergunta)
        
        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if btn_voltar.collidepoint(ev.pos): estado_jogo = origem_reconfig
                
                for i, r_ed in enumerate(botoes_edicao):
                    if r_ed.collidepoint(ev.pos):
                        equipe_editando = i
                        texto_input = jogadores[i]['nome']
                        
                if btn_add.collidepoint(ev.pos) and texto_input.strip() != "":
                    if len(jogadores) < 9:
                        jogadores.append({"nome": texto_input.strip(), "pontos": 0, "pulos": 3, "cartas": False, "placas": False, "convidados": False})
                        texto_input = ""; equipe_editando = None
                    
                if btn_salvar.collidepoint(ev.pos) and equipe_editando is not None and texto_input.strip() != "":
                    jogadores[equipe_editando]['nome'] = texto_input.strip()
                    texto_input = ""; equipe_editando = None
                    
                if btn_del.collidepoint(ev.pos) and equipe_editando is not None:
                    jogadores.pop(equipe_editando)
                    texto_input = ""; equipe_editando = None
                    if jogador_ativo >= len(jogadores): jogador_ativo = 0

            if ev.type == pygame.TEXTINPUT:
                if len(texto_input) < 18: texto_input += ev.text
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_BACKSPACE: texto_input = texto_input[:-1]

    elif estado_jogo == "RANKING_PAUSA":
        tela.fill(COR_FUNDO)
        tela.blit(fonte_titulo_ajuda.render("📊 RANKING ATUAL E RECURSOS USADOS 📊", True, COR_AMARELO), (largura/2 - 380, 40))
        
        rank = sorted(jogadores, key=lambda x: x["pontos"], reverse=True)
        y_r = 120
        for i, j in enumerate(rank):
            cor = COR_ACERTO if i == 0 else COR_TEXTO
            usados = []
            if j['cartas']: usados.append("Cartas")
            if j['placas']: usados.append("Placas")
            if j['convidados']: usados.append("Univ")
            str_usados = ", ".join(usados) if usados else "Nenhum"
            
            txt_status = f"{i+1}º {j['nome']}: {j['pontos']} pts  |  Pulos Restantes: {j['pulos']}  |  Ajudas Usadas: {str_usados}"
            tela.blit(fonte_ajuda.render(txt_status, True, cor), (50, y_r))
            y_r += 45
            
        btn_b = desenhar_botao(largura/2-400, altura-100, 250, 60, COR_AZUL_BOTAO, "VOLTAR", fonte_pergunta)
        btn_edit = desenhar_botao(largura/2-125, altura-100, 250, 60, COR_AMARELO, "EDITAR EQUIPES", fonte_pergunta, (0,0,0))
        btn_d = desenhar_botao(largura/2+150, altura-100, 250, 60, COR_VERMELHO, "DESCLASSIFICAR", fonte_pergunta)
        
        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                if btn_b.collidepoint(ev.pos): 
                    estado_jogo = "JOGANDO" if origem_reconfig != "FIM_BLOCO" else "FIM_BLOCO"
                if btn_edit.collidepoint(ev.pos):
                    origem_reconfig = "RANKING_PAUSA"
                    texto_input = ""; equipe_editando = None
                    estado_jogo = "RECONFIGURAR"
                if btn_d.collidepoint(ev.pos) and len(jogadores) > 1:
                    pygame.mixer.stop()
                    tocar_som("perdeu")
                    reproduzir_video("voce_perdeu.avi")
                    pygame.mixer.stop()
                    jogadores.remove(rank[-1])
                    if jogador_ativo >= len(jogadores): jogador_ativo = 0

    elif estado_jogo in ["JOGANDO", "MOSTRANDO_RESPOSTA"]:
        tela.fill(COR_FUNDO)
        
        if estado_jogo == "JOGANDO" and not exibir_cartas_modo:
            tempo_restante_ms -= dt
            if tempo_restante_ms <= 0:
                tempo_restante_ms = 0
                pygame.mixer.stop()
                tocar_som("tempo_acabou")
                reproduzir_video("voce_perdeu.avi")
                pygame.mixer.stop()
                avancar_pergunta(acertou=False) 

        botoes_jogadores = []
        if len(jogadores) > 0:
            row0 = jogadores[:5]
            row1 = jogadores[5:]
            for idx, jog in enumerate(jogadores):
                w = largura / len(row0) if idx < 5 else largura / len(row1)
                x = idx * w if idx < 5 else (idx - 5) * w
                y = 0 if idx < 5 else 45
                
                cor_jog = COR_ACERTO if idx == jogador_ativo else (50, 50, 50) 
                rect_jog = pygame.draw.rect(tela, cor_jog, (x, y, w, 45))
                pygame.draw.rect(tela, COR_PRATA, (x, y, w, 45), 2)
                nome_exibido = jog['nome'] if len(jog['nome']) <= 15 else jog['nome'][:12] + "..."
                txt_jog = fonte_pequena.render(f"{nome_exibido}: {jog['pontos']}", True, COR_TEXTO)
                tela.blit(txt_jog, txt_jog.get_rect(center=(x + w/2, y + 22)))
                botoes_jogadores.append(rect_jog)

        if indice_pergunta < len(todas_perguntas):
            p = todas_perguntas[indice_pergunta]
            
            pygame.draw.rect(tela, (100,100,100), (20, 100, 680, 130), border_radius=15)
            pygame.draw.rect(tela, COR_PRATA, (22, 102, 676, 126), border_radius=13)
            pygame.draw.rect(tela, COR_VERMELHO, (26, 106, 668, 118), border_radius=10)
            
            segundos = tempo_restante_ms // 1000
            cor_relogio = COR_ACERTO if segundos > 15 else (COR_AMARELO if segundos > 5 else COR_ERRO)
            cx, cy = 870, 620
            pygame.draw.circle(tela, (30, 30, 30), (cx, cy), 50)
            pygame.draw.circle(tela, cor_relogio, (cx, cy), 50, 6)
            txt_cron = fonte_cronometro.render(str(segundos), True, cor_relogio)
            tela.blit(txt_cron, txt_cron.get_rect(center=(cx, cy)))

            texto_pergunta = f"P. {indice_pergunta + 1} - {p['pergunta']}"
            linhas_pergunta = quebrar_texto(texto_pergunta, fonte_pergunta, 640) 
            y_texto = 115
            for linha in linhas_pergunta:
                tela.blit(fonte_pergunta.render(linha, True, COR_TEXTO), (40, y_texto))
                y_texto += 35

            b_res = []
            for i, opt in enumerate(p['opcoes']):
                c = COR_VERMELHO
                cor_txt_opt = COR_TEXTO
                
                if estado_jogo == "MOSTRANDO_RESPOSTA" and i == botao_clicado: 
                    c = cor_feedback
                elif i == alternativa_selecionada: 
                    c = COR_SELECAO     
                    cor_txt_opt = (0, 0, 0) 
                    
                if i in opcoes_ocultas: 
                    c = COR_DESATIVADO
                    cor_txt_opt = COR_TEXTO
                    
                b_res.append(desenhar_botao(20, 240+i*80, 680, 70, c, opt if i not in opcoes_ocultas else "", fonte_opcao, cor_txt_opt, numero=i+1))

            if dados_placas:
                pygame.draw.rect(tela, (255,255,255), (20, 565, 680, 125), border_radius=10)
                cp = [(0,0,180), (180,0,0), (0,150,0), (180,100,0)]
                for k, v in enumerate(dados_placas):
                    pygame.draw.rect(tela, cp[k], (50+k*150, 685 - v, 80, v))
                    tela.blit(fonte_pergunta.render(f"{k+1}: {v}%", True, cp[k]), (50+k*150, 685 - v - 30))
            elif texto_ajuda_convidados:
                pygame.draw.rect(tela, (255,255,255), (20, 565, 680, 125), border_radius=10)
                y_v = 575
                for l in texto_ajuda_convidados.split('\n'):
                    tela.blit(fonte_ajuda.render(l, True, (0,0,100)), (30, y_v)); y_v += 30

            x_d = 720
            jog_atual = jogadores[jogador_ativo] if jogadores else None
            btn_r = desenhar_botao(x_d, 100, 300, 45, COR_AMARELO, "RANKING", fonte_ajuda, (0,0,0))
            
            c_cartas = COR_AZUL_BOTAO if jog_atual and not jog_atual['cartas'] else COR_DESATIVADO
            c_placas = COR_AZUL_BOTAO if jog_atual and not jog_atual['placas'] else COR_DESATIVADO
            c_convid = COR_AZUL_BOTAO if jog_atual and not jog_atual['convidados'] else COR_DESATIVADO
            
            btn_c = desenhar_botao(x_d+10, 160, 85, 75, c_cartas, "Cartas", fonte_ajuda)
            btn_p = desenhar_botao(x_d+105, 160, 85, 75, c_placas, "Placas", fonte_ajuda)
            btn_v = desenhar_botao(x_d+200, 160, 85, 75, c_convid, "Univ.", fonte_ajuda)
            
            # --- DESENHO DOS PULOS DA ESQUERDA PARA A DIREITA ---
            b_p = []
            pulos_jog = jog_atual['pulos'] if jog_atual else 0
            for j in range(3):
                # A lógica j >= (3 - pulos_jog) faz com que o Pulo 1 (esquerda) seja desativado primeiro
                c_pulo = COR_AZUL_BOTAO if j >= (3 - pulos_jog) else COR_DESATIVADO
                b_p.append(desenhar_botao(x_d+10+(j*95), 245, 85, 70, c_pulo, f"Pulo {j+1}", fonte_pequena))
            
            premio_errar = formatar_premio(nivel_premio // 2) if nivel_premio > 0 else "0"
            desenhar_botao(x_d+10, 330, 85, 80, COR_AMARELO, premio_errar, fonte_ajuda, (0,0,0))
            desenhar_botao(x_d+105, 330, 100, 80, COR_AMARELO, formatar_premio(nivel_premio), fonte_premios, (0,0,0))
            desenhar_botao(x_d+215, 330, 85, 80, COR_AMARELO, formatar_premio(nivel_premio + 1), fonte_ajuda, (0,0,0))
            
            btn_parar_jogo = desenhar_botao(x_d, 430, 300, 50, COR_VERMELHO, "PARAR O JOGO", fonte_ajuda)

            btn_avancar = None
            if estado_jogo == "MOSTRANDO_RESPOSTA":
                btn_avancar = desenhar_botao(x_d, 500, 300, 60, (0, 150, 0), "PRÓXIMA PERGUNTA ->", fonte_ajuda)

            if exibir_cartas_modo:
                s = pygame.Surface((largura, altura)); s.set_alpha(220); s.fill((0,0,0)); tela.blit(s, (0,0))
                tela.blit(fonte_titulo_ajuda.render("ESCOLHA UMA CARTA", True, COR_AMARELO), (largura/2-180, altura/2 - 150))
                rects_c = []
                for k in range(3):
                    r = pygame.Rect(largura//2 - 160 + k*120, altura//2 - 60, 80, 110)
                    if carta_verso: tela.blit(carta_verso, r.topleft)
                    else: pygame.draw.rect(tela, (255,255,255), r)
                    rects_c.append(r)
                    
                for ev in eventos:
                    if ev.type == pygame.MOUSEBUTTONDOWN:
                        for i_c, r_c in enumerate(rects_c):
                            if r_c.collidepoint(ev.pos):
                                q = valores_cartas_sorteados[i_c]
                                if len(cartas_frentes) >= q: tela.blit(cartas_frentes[q-1], r_c)
                                pygame.display.flip(); pygame.time.delay(1500)
                                opcoes_ocultas = random.sample([idx for idx in range(4) if idx != p['resposta']], q)
                                exibir_cartas_modo = False

            if estado_jogo == "JOGANDO" and not exibir_cartas_modo:
                for ev in eventos:
                    if ev.type == pygame.MOUSEBUTTONDOWN:
                        if btn_r.collidepoint(ev.pos): origem_reconfig = "JOGANDO"; estado_jogo = "RANKING_PAUSA"
                        
                        if btn_parar_jogo.collidepoint(ev.pos): 
                            pygame.mixer.stop()
                            tocar_som("encerra")
                            reproduzir_video("encerra.avi")
                            pygame.mixer.stop()
                            motivo_fim = "JOGO PARADO PELO APRESENTADOR!"; estado_jogo = "FIM"
                            
                        for idx, rect_jog in enumerate(botoes_jogadores):
                            if rect_jog.collidepoint(ev.pos): jogador_ativo = idx
                            
                        if btn_c.collidepoint(ev.pos) and jog_atual and not jog_atual['cartas']: 
                            jog_atual['cartas'] = True; exibir_cartas_modo = True
                            valores_cartas_sorteados = [1, 2, 3]
                            random.shuffle(valores_cartas_sorteados)
                            
                        if btn_p.collidepoint(ev.pos) and jog_atual and not jog_atual['placas']:
                            jog_atual['placas'] = True
                            # Removido: tocar_som("posso_perguntar")
                            d = [random.randint(5,15) for _ in range(4)]; d[p['resposta']] = random.randint(50,70)
                            dados_placas = [int((x/sum(d))*100) for x in d]
                            
                        if btn_v.collidepoint(ev.pos) and jog_atual and not jog_atual['convidados']:
                            jog_atual['convidados'] = True
                            # Removido: tocar_som("posso_perguntar")
                            u1 = convidados_nomes[0] if len(convidados_nomes) > 0 else "Univ 1"
                            u2 = convidados_nomes[1] if len(convidados_nomes) > 1 else "Univ 2"
                            u3 = convidados_nomes[2] if len(convidados_nomes) > 2 else "Univ 3"
                            texto_ajuda_convidados = f"{u1}: É a {p['resposta']+1}\n{u2}: Fico com a {p['resposta']+1}\n{u3}: Tenho certeza da {p['resposta']+1}"
                        
                        for j, bp in enumerate(b_p):
                            # Garante que o clique só funciona nos botões ativos (da direita para a esquerda internamente, desativando da esquerda para a direita visualmente)
                            if bp.collidepoint(ev.pos) and jog_atual and j >= (3 - jog_atual['pulos']):
                                jog_atual['pulos'] -= 1
                                avancar_pergunta(acertou=False) 
                                break
                        
                        for i, rb in enumerate(b_res):
                            if rb.collidepoint(ev.pos) and i not in opcoes_ocultas:
                                if alternativa_selecionada == i:
                                    botao_clicado = i; estado_jogo = "MOSTRANDO_RESPOSTA"
                                    tempo_resposta = pygame.time.get_ticks()
                                    if i == p['resposta']: tocar_som("acerto"); cor_feedback = COR_ACERTO
                                    else: tocar_som("erro"); cor_feedback = COR_ERRO
                                else: 
                                    alternativa_selecionada = i; tocar_som("posso_perguntar" if som_alternancia else "certeza"); som_alternancia = not som_alternancia

            elif estado_jogo == "MOSTRANDO_RESPOSTA":
                for ev in eventos:
                    if ev.type == pygame.MOUSEBUTTONDOWN and btn_avancar and btn_avancar.collidepoint(ev.pos):
                        if botao_clicado == p['resposta']: 
                            jogadores[jogador_ativo]['pontos'] += 10
                            avancar_pergunta(acertou=True)
                        else:
                            avancar_pergunta(acertou=False)
        else:
            pygame.mixer.stop()
            motivo_fim = "O BANCO DE PERGUNTAS ESGOTOU!"
            estado_jogo = "FIM"

    elif estado_jogo == "FIM":
        tela.fill((0, 0, 0))
        titulo_fim = fonte_titulo_ajuda.render(motivo_fim, True, COR_AMARELO)
        tela.blit(titulo_fim, titulo_fim.get_rect(center=(largura/2, 100)))
        
        r = sorted(jogadores, key=lambda x: x["pontos"], reverse=True)
        for i, j in enumerate(r[:5]):
            tela.blit(fonte_pergunta.render(f"{i+1}º {j['nome']}: {j['pontos']} pts", True, COR_AMARELO), (largura/2-100, 200+i*50))
        btn_exit = desenhar_botao(largura/2-150, altura-100, 300, 60, (0,150,0), "NOVO JOGO", fonte_pergunta)
        if any(ev.type == pygame.MOUSEBUTTONDOWN and btn_exit.collidepoint(ev.pos) for ev in eventos):
            os.execv(sys.executable, ['python'] + sys.argv)

    pygame.display.flip()