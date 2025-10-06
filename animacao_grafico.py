import numpy as np
import re
import os
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import interp1d
from manim import *

# --- Funções Auxiliares (sem alterações) ---
DIRETORIO_DO_SCRIPT = os.path.dirname(os.path.abspath(__file__))


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


# --- Cena Manim para o Gráfico ---
class AnimacaoGrafico(Scene):
    def construct(self):
        ARQUIVO_DE_DADOS = "exp.txt"
        energias, intensidades, E_INICIAL, E_FINAL = processar_dados(ARQUIVO_DE_DADOS)
        if energias is None:
            self.add(Text("Arquivo de dados não encontrado ou inválido.", color=RED));
            return

        eixos = Axes(
            x_range=[E_INICIAL, E_FINAL, 20], y_range=[0, 1.1, 0.2],
            x_length=10, y_length=6, axis_config={"color": BLUE},
            x_axis_config={"numbers_to_include": np.arange(round(E_INICIAL, -1), E_FINAL + 21, 40)},
            y_axis_config={"numbers_to_include": np.arange(0, 1.1, 0.5)}
        ).add_coordinates()

        rotulo_x = eixos.get_x_axis_label(Text("Energy (eV)"), edge=DOWN, direction=DOWN)
        rotulo_y = eixos.get_y_axis_label(Text("Intensity (a.u.)").rotate(90 * DEGREES), edge=LEFT, direction=LEFT)
        titulo = Text("Curva I-V Experimental", font_size=48).to_edge(UP)

        energia_tracker = ValueTracker(E_INICIAL)

        grafico_dinamico = always_redraw(
            lambda: eixos.plot_line_graph(
                x_values=energias[energias <= energia_tracker.get_value()],
                y_values=intensidades[energias <= energia_tracker.get_value()],
                line_color=YELLOW, add_vertex_dots=False
            )
        )

        self.add(titulo, eixos, rotulo_x, rotulo_y, grafico_dinamico)

        self.play(
            energia_tracker.animate.set_value(E_FINAL),
            run_time=15,  # Duração total: 15 segundos
            rate_func=linear
        )
        self.wait(2)