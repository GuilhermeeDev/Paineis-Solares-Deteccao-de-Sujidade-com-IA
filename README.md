# ☀ Painéis Solares: Detecção de Sujidade com IA

Bem-vindo(a) ao repositório do projeto de detecção automática de sujidade em painéis solares utilizando Inteligência Artificial.

Este software tem como objetivo **automatizar a identificação de sujeira em placas solares**, auxiliando na manutenção preventiva e no aumento da eficiência energética. A solução foi desenvolvida com técnicas de **aprendizado de máquina**, empregando modelos treinados sobre datasets cuidadosamente preparados.

Para mais detalhes sobre a estrutura, funcionamento e componentes do projeto, [acesse a documentação completa](./docs/documentacao.md).

## Dependências
- Python 3.9^
- Pip 24^
## Instalação
1 - Clonando o Repositorio:
```bash
git clone https://github.com/GuilhermeeDev/Paineis-Solares-Deteccao-de-Sujidade-com-IA.git
cd Paineis-Solares-Deteccao-de-Sujidade-com-IA
```
2 - Instalando as dependencias do software:
```bash
cd Software
pip --version
pip install -r requirements.txt
```
## Funcionamento do Software
Este projeto é composto por duas APIs desenvolvidas com **FastAPI** que trabalham em conjunto para automatizar o fluxo de envio, processamento e registro das imagens das placas solares.

A primeira API *(cliente_rbpi.py)* permite que o usuário envie uma ou mais imagens. Cada imagem é convertida para base64 e enviada para um repositório no GitHub, utilizando a API pública do GitHub. Após o envio, a URL da imagem é passada como parâmetro para a segunda API.

A segunda API *(main_process.py)* realiza o processamento da imagem usando modelos de deep learning pré-treinados (**AlexNet**, **ResNet50** e **VGG16**). O sistema classifica a imagem como "clean" ou "dirty", renomeia o arquivo com a classificação, e salva os resultados (incluindo a nova URL da imagem, a data e a hora do processamento) em um banco de dados **MySQL**. Todo o processo é feito de forma assíncrona e individual para cada imagem, mesmo quando múltiplas imagens são enviadas.

Este sistema todo foi construido para ser utilizado no Seguinte contexto:
