import unittest

from scripts.atualizar_catalogo import atualizar_catalogo


class AtualizarCatalogoTests(unittest.TestCase):
    def test_adiciona_marcador_e_preserva_metadados_existentes(self):
        catalogo = '''window.MARCADORES = [
  { titulo: "Existente", imagem: "imagens/existente.jpg", autoria: "Pontos de Luta", autorUrl: "https://www.instagram.com/pontosdeluta/" }
];
'''
        imagens = [
            "imagens/existente.jpg",
            "imagens/existente-verso.png",
            "imagens/novo-marcador-6x1.jpg",
            "imagens/novo-marcador-6x1-verso.jpg",
        ]

        atualizado, resumo = atualizar_catalogo(
            catalogo,
            imagens,
            ["imagens/existente-verso.png", "imagens/novo-marcador-6x1.jpg"],
        )

        self.assertIn('autoria: "Pontos de Luta"', atualizado)
        self.assertIn('autorUrl: "https://www.instagram.com/pontosdeluta/"', atualizado)
        self.assertIn('verso: "imagens/existente-verso.png"', atualizado)
        self.assertIn('titulo: "Novo marcador 6x1"', atualizado)
        self.assertIn('imagem: "imagens/novo-marcador-6x1.jpg"', atualizado)
        self.assertIn('verso: "imagens/novo-marcador-6x1-verso.jpg"', atualizado)
        self.assertEqual(resumo["adicionados"], 1)
        self.assertEqual(resumo["versos_associados"], 1)

    def test_execucao_repetida_nao_cria_duplicatas(self):
        catalogo = '''window.MARCADORES = [
  { titulo: "Existente", imagem: "imagens/existente.jpg" }
];
'''
        imagens = ["imagens/existente.jpg", "imagens/novo.jpg"]
        primeira, _ = atualizar_catalogo(catalogo, imagens, ["imagens/novo.jpg"])
        segunda, resumo = atualizar_catalogo(primeira, imagens, ["imagens/novo.jpg"])

        self.assertEqual(segunda, primeira)
        self.assertEqual(resumo["adicionados"], 0)
        self.assertEqual(resumo["versos_associados"], 0)

    def test_verso_sem_frente_nao_cria_marcador(self):
        catalogo = "window.MARCADORES = [\n];\n"
        atualizado, resumo = atualizar_catalogo(
            catalogo,
            ["imagens/so-verso-verso.jpg"],
            ["imagens/so-verso-verso.jpg"],
        )

        self.assertEqual(atualizado, catalogo)
        self.assertEqual(resumo["adicionados"], 0)
        self.assertEqual(resumo["versos_sem_frente"], 1)

    def test_arquivo_frente_e_verso_seguem_a_logica_do_site(self):
        catalogo = "window.MARCADORES = [\n];\n"
        imagens = [
            "imagens/projeto-frente.jpg",
            "imagens/projeto.jpg",
            "imagens/projeto-verso.jpg",
        ]
        atualizado, resumo = atualizar_catalogo(
            catalogo,
            imagens,
            ["imagens/projeto-frente.jpg"],
        )

        self.assertIn('imagem: "imagens/projeto.jpg"', atualizado)
        self.assertIn('verso: "imagens/projeto-verso.jpg"', atualizado)
        self.assertEqual(resumo["adicionados"], 1)


if __name__ == "__main__":
    unittest.main()
