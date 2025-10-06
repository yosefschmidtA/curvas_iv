import os
from manim import *
from PIL import Image

# --- Caminho para a pasta de imagens (USANDO O CAMINHO ABSOLUTO DIRETO) ---
PASTA_LEED_IMAGENS = "/home/yosef/PycharmProjects/Curva_IV/curvas_iv/leed_imagens"

# (O script 'animacao_grafico.py' não precisa de nenhuma alteração e deve funcionar)

# =====================================================================
# CENA MANIM PARA AS IMAGENS (VERSÃO CORRIGIDA)
# =====================================================================
class AnimacaoImagens(Scene):
    def construct(self):
        # --- Parâmetros de Sincronização ---
        E_INICIAL = 46
        E_FINAL = 174
        DURACAO_TOTAL = 15.0

        energias_das_imagens = np.arange(E_INICIAL, E_FINAL + 2, 2)
        num_imagens = len(energias_das_imagens)
        tempo_por_imagem = DURACAO_TOTAL / num_imagens

        # --- Objetos da Cena ---
        titulo = Text("Padrão de LEED", font_size=48).to_edge(UP)

        energia_label = Text("Energia: ", font_size=36)
        energia_valor = DecimalNumber(E_INICIAL, num_decimal_places=0, font_size=36)
        ev_label = Text(" eV", font_size=36)

        contador_energia = VGroup(energia_label, energia_valor, ev_label).arrange(RIGHT)
        contador_energia.to_edge(DOWN, buff=1)

        # --- Animação ---
        self.add(titulo, contador_energia)

        # --- LÓGICA DE CARREGAMENTO MANUAL DE IMAGEM ---
        nome_arquivo_inicial = os.path.join(PASTA_LEED_IMAGENS, f"{E_INICIAL}.jpg")

        # Verifica se a primeira imagem existe
        if not os.path.exists(nome_arquivo_inicial):
            aviso = Text("Imagem inicial não encontrada!", color=RED)
            self.play(Write(aviso))
            self.wait()
            return

        # Carrega a imagem inicial usando Pillow e a converte para um formato que Manim entende
        pil_img = Image.open(nome_arquivo_inicial).convert("RGBA")
        imagem_atual = ImageMobject(np.array(pil_img)).scale(1.2)

        self.add(imagem_atual)
        self.wait(tempo_por_imagem)

        # Loop para trocar as imagens
        for i in range(1, num_imagens):
            energia = energias_das_imagens[i]
            nome_arquivo = os.path.join(PASTA_LEED_IMAGENS, f"{energia}.jpg")

            if os.path.exists(nome_arquivo):
                pil_img_nova = Image.open(nome_arquivo).convert("RGBA")
                imagem_nova = ImageMobject(np.array(pil_img_nova)).scale(1.2)

                self.play(
                    ReplacementTransform(imagem_atual, imagem_nova),
                    energia_valor.animate.set_value(energia),
                    run_time=tempo_por_imagem,
                    rate_func=linear
                )
                imagem_atual = imagem_nova
            else:
                # Se uma imagem faltar, apenas atualiza o número
                self.play(
                    energia_valor.animate.set_value(energia),
                    run_time=tempo_por_imagem,
                    rate_func=linear
                )
        self.wait(2)