import numpy as np
import re
import os  # Importa a biblioteca 'os' para verificar a existência de arquivos
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import interp1d
from manim import *


# =====================================================================
# 1. FUNÇÕES AUXILIARES (sem alterações)
# =====================================================================
def ler_iv_arquivo(caminho):
    try:
        with open(caminho, 'r') as f:
            linhas = f.readlines()
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{caminho}' não encontrado.")
        return None, None
    exp_ang, exp_int = [], []
    modo = None
    for linha in linhas:
        linha = linha.strip()
        if linha.startswith('"IV exp'):
            modo = 'exp'
            continue
        if linha.startswith('"IV theory') or linha == '':
            modo = None
            continue
        if modo == 'exp':
            partes = linha.split()
            if len(partes) == 2:
                ang, intensidade = map(float, partes)
                exp_ang.append(ang)
                exp_int.append(intensidade)
    return np.array(exp_ang), np.array(exp_int)


def processar_dados(caminho_arquivo, inicio_energia=40, fim_energia=200, passo=2.0, sigma_suavizacao=1.0):
    ang_exp, int_exp = ler_iv_arquivo(caminho_arquivo)
    if ang_exp is None or len(ang_exp) < 2:
        return None, None
    int_exp_norm = (int_exp - np.min(int_exp)) / (np.max(int_exp) - np.min(int_exp))
    novo_eixo = np.arange(inicio_energia, fim_energia + passo, passo)
    interp_exp = interp1d(ang_exp, int_exp_norm, kind='linear', bounds_error=False,
                          fill_value=(int_exp_norm[0], int_exp_norm[-1]))
    int_exp_interp = interp_exp(novo_eixo)
    int_exp_smooth = gaussian_filter1d(int_exp_interp, sigma_suavizacao)
    return novo_eixo, int_exp_smooth


# =====================================================================
# 2. CENA MANIM
# =====================================================================
class AnimacaoCurvaIV(Scene):
    def construct(self):
        # --- Configurações da Animação ---
        ARQUIVO_DE_DADOS = "exp.txt"  # <--- Nome do seu arquivo de dados
        ENERGIA_INICIAL = 40
        ENERGIA_FINAL = 200

        # --- Carregar e Processar os Dados ---
        energias, intensidades = processar_dados(ARQUIVO_DE_DADOS, ENERGIA_INICIAL, ENERGIA_FINAL)
        if energias is None:
            self.add(Text("Arquivo de dados não encontrado ou inválido.", color=RED))
            return

        # --- Criar os Eixos do Gráfico ---
        eixos = Axes(
            x_range=[ENERGIA_INICIAL, ENERGIA_FINAL, 20], y_range=[0, 1.1, 0.2],
            x_length=8, y_length=5, axis_config={"color": BLUE},
            x_axis_config={"numbers_to_include": np.arange(40, 201, 40)},
            y_axis_config={"numbers_to_include": np.arange(0, 1.1, 0.5)}
        ).add_coordinates()
        eixos.to_edge(DL, buff=0.8)
        rotulo_x = eixos.get_x_axis_label(Text("Energy (eV)"), edge=DOWN, direction=DOWN)
        rotulo_y = eixos.get_y_axis_label(Text("Intensity (a.u.)").rotate(90 * DEGREES), edge=LEFT, direction=LEFT)
        titulo = Text("Curva I-V Experimental", font_size=36).to_edge(UP)

        # --- Placeholder para a imagem LEED ---
        leed_imagem = Square(side_length=3.0, stroke_opacity=0, fill_opacity=0).to_edge(RIGHT, buff=1)

        # --- Objetos Dinâmicos ---
        energia_tracker = ValueTracker(ENERGIA_INICIAL)
        rotulo_energia = VGroup(
            Text("Energia: ", font_size=24),
            DecimalNumber(energia_tracker.get_value(), num_decimal_places=0, font_size=24),
            Text(" eV", font_size=24)
        ).arrange(RIGHT).to_edge(UR)
        rotulo_energia.add_updater(lambda m: m[1].set_value(energia_tracker.get_value()))

        # --- LÓGICA DE ATUALIZAÇÃO DA IMAGEM (CORRIGIDA) ---
        self.imagem_atual = ""  # Variável para guardar o caminho da imagem atual

        def atualizar_imagem(img):
            E_val = energia_tracker.get_value()
            E_atual = int(2 * round(E_val / 2))  # Arredonda para o número par mais próximo
            nome_arquivo = f"leed_imagens/{E_atual}.jpg"

            # Apenas atualiza se o nome do arquivo mudou E o arquivo existe
            if nome_arquivo != self.imagem_atual and os.path.exists(nome_arquivo):
                try:
                    nova_imagem = ImageMobject(nome_arquivo).scale(0.8).move_to(img.get_center())
                    img.become(nova_imagem)
                    self.imagem_atual = nome_arquivo
                except Exception as e:
                    print(f"Não foi possível carregar a imagem: {nome_arquivo}. Erro: {e}")

        leed_imagem.add_updater(atualizar_imagem)

        # --- Animação Principal ---
        self.play(Write(titulo), Create(eixos), Write(rotulo_x), Write(rotulo_y))
        self.wait(0.5)
        self.add(rotulo_energia, leed_imagem)

        grafico_dinamico = always_redraw(
            lambda: eixos.plot_line_graph(
                x_values=energias[energias <= energia_tracker.get_value()],
                y_values=intensidades[energias <= energia_tracker.get_value()],
                line_color=YELLOW, add_vertex_dots=False
            )
        )
        self.add(grafico_dinamico)

        self.play(
            energia_tracker.animate.set_value(ENERGIA_FINAL),
            run_time=15,
            rate_func=linear
        )

        self.wait(2)