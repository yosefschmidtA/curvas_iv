import numpy as np
import re
import os
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import interp1d
from manim import *
from PIL import Image

# --- CAMINHO ABSOLUTO PARA A PASTA DE IMAGENS (A ÚNICA PARTE A SER AJUSTADA SE MUDAR DE MÁQUINA) ---
PASTA_LEED_IMAGENS = "/home/yosef/PycharmProjects/Curva_IV/curvas_iv/leed_imagens"
DIRETORIO_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


# =====================================================================
# FUNÇÕES AUXILIARES
# =====================================================================
def ler_iv_arquivo(caminho):
    try:
        with open(caminho, 'r') as f:
            linhas = f.readlines()
    except FileNotFoundError:
        print(f"ERRO: Arquivo de dados '{caminho}' não encontrado.")
        return None, None, None, None
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
                try:
                    ang, intensidade = map(float, partes)
                    exp_ang.append(ang)
                    exp_int.append(intensidade)
                except ValueError:
                    continue
    if not exp_ang: return None, None, None, None
    return np.array(exp_ang), np.array(exp_int), np.min(exp_ang), np.max(exp_ang)


def processar_dados(caminho_arquivo, passo=2.0, sigma_suavizacao=1.0):
    caminho_completo = os.path.join(DIRETORIO_DO_SCRIPT, caminho_arquivo)
    ang_exp, int_exp, min_E, max_E = ler_iv_arquivo(caminho_completo)
    if ang_exp is None or len(ang_exp) < 2: return None, None, None, None
    int_exp_norm = (int_exp - np.min(int_exp)) / (np.max(int_exp) - np.min(int_exp))
    inicio_energia = passo * round(min_E / passo)
    fim_energia = passo * round(max_E / passo)
    novo_eixo = np.arange(inicio_energia, fim_energia + passo, passo)
    interp_exp = interp1d(ang_exp, int_exp_norm, kind='linear', bounds_error=False,
                          fill_value=(int_exp_norm[0], int_exp_norm[-1]))
    int_exp_interp = interp_exp(novo_eixo)
    int_exp_smooth = gaussian_filter1d(int_exp_interp, sigma_suavizacao)
    return novo_eixo, int_exp_smooth, inicio_energia, fim_energia


# =====================================================================
# CENA MANIM COMPLETA
# =====================================================================
class AnimacaoCompleta(Scene):
    def construct(self):
        ARQUIVO_DE_DADOS = "exp.txt"

        energias, intensidades, E_INICIAL, E_FINAL = processar_dados(ARQUIVO_DE_DADOS)
        if energias is None:
            self.add(Text("Arquivo de dados não encontrado!", color=RED));
            return

        # --- Eixos e Títulos ---
        eixos = Axes(
            x_range=[E_INICIAL, E_FINAL, 20], y_range=[0, 1.1, 0.2],
            x_length=8, y_length=5, axis_config={"color": BLUE},
            x_axis_config={"numbers_to_include": np.arange(round(E_INICIAL, -1), E_FINAL + 21, 40)},
            y_axis_config={"numbers_to_include": np.arange(0, 1.1, 0.5)}
        ).add_coordinates().to_edge(DL, buff=0.8)

        rotulo_x = eixos.get_x_axis_label(Text("Energy (eV)"), edge=DOWN, direction=DOWN)
        rotulo_y = eixos.get_y_axis_label(Text("Intensity (a.u.)").rotate(90 * DEGREES), edge=LEFT, direction=LEFT)
        titulo = Text("Curva I-V e Padrão de LEED", font_size=36).to_edge(UP)

        # --- Objetos Dinâmicos ---
        image_container = VGroup().to_edge(RIGHT, buff=1)  # Container para a imagem
        energia_tracker = ValueTracker(E_INICIAL)

        rotulo_energia = VGroup(
            Text("Energia: ", font_size=24),
            DecimalNumber(energia_tracker.get_value(), num_decimal_places=0, font_size=24),
            Text(" eV", font_size=24)
        ).arrange(RIGHT).to_edge(UR)
        rotulo_energia.add_updater(lambda m: m[1].set_value(energia_tracker.get_value()))

        # --- Lógica de Atualização de Imagem (Robusta) ---
        self.imagem_atual = ""

        def atualizar_imagem(mob):
            E_val = energia_tracker.get_value()
            E_atual = int(2 * round(E_val / 2))
            nome_arquivo = os.path.join(PASTA_LEED_IMAGENS, f"{E_atual}.jpg")

            if nome_arquivo != self.imagem_atual and os.path.exists(nome_arquivo):
                self.imagem_atual = nome_arquivo
                try:
                    pil_img = Image.open(nome_arquivo).convert("RGBA")
                    nova_imagem = ImageMobject(np.array(pil_img)).scale(0.8)
                    # Define o conteúdo do container para ser a nova imagem
                    mob.set_submobjects([nova_imagem])
                except Exception as e:
                    print(f"Erro ao carregar {nome_arquivo}: {e}")

        image_container.add_updater(atualizar_imagem)

        # --- Gráfico Dinâmico ---
        grafico_dinamico = always_redraw(
            lambda: eixos.plot_line_graph(
                x_values=energias[energias <= energia_tracker.get_value()],
                y_values=intensidades[energias <= energia_tracker.get_value()],
                line_color=YELLOW, add_vertex_dots=False
            )
        )

        # --- Animação Principal ---
        self.play(Write(titulo), Create(eixos), Write(rotulo_x), Write(rotulo_y))
        self.add(rotulo_energia, image_container, grafico_dinamico)

        # Chama a atualização uma vez para carregar a imagem inicial
        atualizar_imagem(image_container)

        self.wait(0.5)

        self.play(
            energia_tracker.animate.set_value(E_FINAL),
            run_time=20,  # Aumentei para 20 segundos para dar tempo de ver melhor
            rate_func=linear
        )

        self.wait(3)