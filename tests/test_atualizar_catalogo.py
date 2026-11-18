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
        self.assertIn('titulo: "Novo Marcador 6x1"', atualizado)
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


    def test_reconhece_autoria_e_link_no_nome_do_arquivo(self):
        catalogo = "window.MARCADORES = [\n];\n"
        imagem = (
            "imagens/totoro-autoria-maria-laura-pedrosa-"
            "link-https%3A%2F%2Fwww.instagram.com%2Fmaria.laura%2F.png"
        )

        atualizado, resumo = atualizar_catalogo(catalogo, [imagem], [imagem])

        self.assertIn('titulo: "Totoro"', atualizado)
        self.assertIn('autoria: "Maria Laura Pedrosa"', atualizado)
        self.assertIn('autorUrl: "https://www.instagram.com/maria.laura/"', atualizado)
        self.assertEqual(resumo["adicionados"], 1)

    def test_corrige_titulo_antigo_e_completa_autoria_no_catalogo_existente(self):
        catalogo = '''window.MARCADORES = [
  { titulo: "Totoro Autoria Maria Laura Pedrosa", imagem: "imagens/totoro-autoria-maria-laura-pedrosa.png" }
];
'''
        imagem = "imagens/totoro-autoria-maria-laura-pedrosa.png"

        atualizado, resumo = atualizar_catalogo(catalogo, [imagem])

        self.assertIn('titulo: "Totoro"', atualizado)
        self.assertIn('autoria: "Maria Laura Pedrosa"', atualizado)
        self.assertNotIn('titulo: "Totoro Autoria Maria Laura Pedrosa"', atualizado)
        self.assertEqual(resumo["titulos_corrigidos"], 1)
        self.assertEqual(resumo["metadados_atualizados"], 1)

    def test_nao_substitui_autoria_ou_link_manual(self):
        catalogo = '''window.MARCADORES = [
  {
    titulo: "Título escolhido manualmente",
    imagem: "imagens/marcador-autoria-nome-do-arquivo-link-https%3A%2F%2Fwww.instagram.com%2Fperfil.automatico%2F.png",
    autoria: "Crédito manual",
    autorUrl: "https://www.instagram.com/perfil.manual/"
  }
];
'''
        imagem = (
            "imagens/marcador-autoria-nome-do-arquivo-"
            "link-https%3A%2F%2Fwww.instagram.com%2Fperfil.automatico%2F.png"
        )

        atualizado, resumo = atualizar_catalogo(catalogo, [imagem])

        self.assertIn('titulo: "Título escolhido manualmente"', atualizado)
        self.assertIn('autoria: "Crédito manual"', atualizado)
        self.assertIn('autorUrl: "https://www.instagram.com/perfil.manual/"', atualizado)
        self.assertNotIn("perfil.automatico", atualizado)
        self.assertEqual(resumo["titulos_corrigidos"], 0)
        self.assertEqual(resumo["metadados_atualizados"], 0)

    def test_preenche_campos_de_metadados_vazios(self):
        catalogo = '''window.MARCADORES = [
  {
    titulo: "Meu marcador",
    imagem: "imagens/meu-marcador-autoria-ana-clara.png",
    autoria: "",
    autorUrl: ""
  }
];
'''
        imagem = "imagens/meu-marcador-autoria-ana-clara.png"

        atualizado, resumo = atualizar_catalogo(catalogo, [imagem])

        self.assertIn('autoria: "Ana Clara"', atualizado)
        self.assertEqual(resumo["metadados_atualizados"], 1)

if __name__ == "__main__":
    unittest.main()
