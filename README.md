# The Fast and the Furious — ROG Ally / Bazzite

Versão 0.1.0. Adaptação independente para jogar uma cópia própria do arcade de 2004 no ROG Ally com Bazzite e Proton 11.0.

Somente código próprio e documentação. Traga seus próprios dados do jogo. Este projeto não distribui jogo, executável modificado, DLLs, artes, capturas ou saves e não possui afiliação com os titulares da marca.

## Recursos

- Corridas renderizadas em **1920×1080, 16:9**, com perspectiva corrigida, sem esticar ou recortar a cena. Menus, vídeos e HUD preservam suas proporções; telas 2D têm barras laterais.
- Controles analógicos do Ally, usando o controle Xbox One Elite 2 exposto pelo InputPlumber.
- Menu de pausa em inglês, com **Infinite Boost ON/OFF**. O cheat repõe as cargas de nitro; A ativa uma carga. A duração normal de cada acionamento permanece.
- Pausa com relógios virtuais: o tempo suspenso não é contado pela simulação.
- Opção nativa de velocidade em **KPH (km/h)**.
- PIN local preenchido automaticamente após iniciar uma partida; perfil carregado pelo sistema original do jogo.
- Salvamento nativo automático do perfil quando há mudanças e antes da pausa; cópias versionadas dos arquivos de progresso.

O salvamento mantém as informações que o jogo registra no perfil: carros, melhorias, dinheiro e histórico. Uma corrida interrompida não é retomada no mesmo ponto; recompensas e recordes dependem da conclusão e do registro pelo jogo.

## Preparação

Use Python 3 com Pillow, SDL2, Fontconfig, GCC/binutils com saída x86 de 32 bits e Proton 11.0 já disponíveis. O código C não precisa de SDK Windows, biblioteca C de 32 bits ou compilador MinGW. Nenhum script instala pacotes do sistema.

1. Coloque este projeto em `~/Games/FastAndFurious`.
2. Coloque os arquivos da sua cópia na pasta `game`, com `sdaemon.exe` diretamente dentro dela. Não substitua seus saves ao atualizar.
3. Forneça `dependencias/wal-loader.exe` e `dependencias/wal_rawthrills.dll` do [Windows Arcade Loader](https://github.com/aderumier/windowsarcadeloader). A dependência externa e sua licença são distribuídas pelo respectivo projeto, não por este repositório.
4. Com o jogo fechado, execute:

```bash
python3 build.py
chmod +x jogar.sh
```

5. Adicione `jogar.sh` ao Steam como jogo externo. Deixe a compatibilidade forçada desativada nesse atalho: o script inicia o Proton. Abra pelo Steam no modo jogo.

O build aceita apenas o `sdaemon.exe` com SHA-256 `16663d2e79b21de16901082929512ecc8af6ec3a13db9b6650c3d7abfd41ade6`. Cria `game/fnf-ally.exe` localmente e preserva o original. O launcher confere o hash da cópia adaptada antes de executá-la.

## Controles

| Controle | Função |
|---|---|
| Analógico esquerdo | Direção / seleção |
| RT | Acelerar / confirmar nos menus do jogo |
| LT | Frear |
| A | Iniciar / nitro durante a corrida |
| B | Freio de mão |
| X | Câmera |
| Y | Música / pular melhorias |
| LB / RB | Reduzir / aumentar marcha |
| View | Crédito |
| Menu | Pausar / retomar |
| Direcional no pause | Selecionar opção |
| A no pause | Confirmar / alternar cheat |
| B no pause | Retomar |

## Progresso e atualização

`state/profile.json` guarda o PIN local e a escolha do cheat. Preserve esse arquivo: ele identifica o perfil carregado automaticamente. O jogo mantém seus dados em `game/money_players.pdt`, `game/cops2.hst` e nos arquivos de preferências/auditoria. `saves/latest` contém a cópia mais recente; `saves/history` mantém até 20 versões por arquivo.

A atualização deve substituir somente código e documentação. Preserve `game`, `state`, `saves`, `compatdata` e as dependências. Refaça `python3 build.py` quando os hooks mudarem. Feche jogos abertos antes de iniciar testes.

Arte personalizada pode ser aplicada pelo Steam usando imagens fornecidas pelo próprio usuário. As artes da instalação privada não integram a distribuição pública.

## Limites

Validado no Ally com Bazzite, Proton 11.0 e DXVK D3D8. O alvo é 1080p a 60 FPS; isso não garante desempenho idêntico em todas as pistas, configurações de energia ou máquinas. Esta versão não oferece modo online, save state ou suporte a outras revisões do executável.

The native game difficulty is set to **1 (easiest)** on every launch.
