# Entrelinhas — Marcadores de página

Catálogo digital dos marcadores de página da Biblioteca do IFMG Campus Sabará.

**Site público:** https://bibliotecaifmgsabara.github.io/marcadores/

**Repositório:** https://github.com/BibliotecaIFMGSabara/marcadores

## Como adicionar um marcador

Coloque as imagens originais na pasta `imagens/`.

Os formatos aceitos são JPG, JPEG, PNG e WebP.

### Marcador somente com frente

Use, por exemplo:

`meu-marcador.png`

### Marcador com frente e verso

As duas imagens devem compartilhar o mesmo nome-base. O token `-verso-` pode aparecer em qualquer posição entre as partes do nome:

```text
meu-marcador.png
meu-marcador-verso.png
```

ou:

```text
meu-marcador-autoria-nome.png
meu-marcador-verso-autoria-nome.png
```

ou:

```text
meu-marcador-autoria-nome.png
meu-marcador-autoria-nome-verso.png
```

### Autoria e Instagram

A autoria pode ser informada no próprio nome do arquivo:

`meu-marcador-autoria-Nome-Sobrenome.png`

Também é possível incluir o Instagram usando uma URL codificada:

`meu-marcador-autoria-Nome-Sobrenome-link-https%3A%2F%2Fwww.instagram.com%2Fperfil%2F.png`

## Catálogo automático

O arquivo `catalogo.js` é uma reserva usada quando o carregamento principal da coleção não está disponível. Ele é atualizado automaticamente pelo GitHub Actions a partir da pasta `imagens/`.

A automação:

- reconhece frente e verso e os associa ao mesmo marcador;
- identifica autoria e link a partir do nome do arquivo;
- adiciona novas imagens ao catálogo;
- remove registros cuja imagem principal não existe mais;
- corrige referências de verso que apontem para uma imagem que foi renomeada;
- remove referências de verso quando a imagem correspondente deixou de existir;
- remove registros antigos de verso que tenham ficado separados da frente;
- preserva informações manuais já existentes quando elas continuam válidas.

**Não é necessário editar `catalogo.js` manualmente para adicionar imagens.**

## Impressão

O site possui um organizador para impressão em folhas A4, com frente e verso alinhados conforme as medidas escolhidas. O arquivo gerado deve ser impresso em **100% / tamanho real**, sem "ajustar à página".

## Arquivos principais

- `index.html`: estrutura e conteúdo da página.
- `style.css`: identidade visual e adaptação responsiva.
- `app.js`: carregamento da coleção, busca, interação, destaque e impressão.
- `catalogo.js`: catálogo de reserva atualizado automaticamente.
- `scripts/atualizar_catalogo.py`: rotina de sincronização do catálogo.
- `tests/test_atualizar_catalogo.py`: testes da automação.
- `imagens/`: imagens originais dos marcadores.

## Publicação

O site é publicado pelo GitHub Pages a partir da branch `main`.

O workflow de atualização do catálogo é executado quando há alterações relevantes na pasta `imagens/`, no script ou nos testes. 
