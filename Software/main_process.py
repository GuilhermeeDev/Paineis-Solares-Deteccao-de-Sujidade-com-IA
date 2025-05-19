from fastapi import FastAPI, HTTPException, Query   # type: ignore
import requests                             # type: ignore
from io import BytesIO                      # type: ignore
from PIL import Image                       # type: ignore
import torch                                # type: ignore
from torchvision import models,transforms   # type: ignore
from datetime import datetime               # type: ignore
import logging                              # type: ignore
import torch.nn as nn                       # type: ignore
import json                                 # type: ignore
import os                                   # type: ignore
import uvicorn                              # type: ignore
from datetime import datetime               # type: ignore
from database import get_db_connection      # type: ignore
import mysql.connector                      # type: ignore
import base64                               # type: ignore
import time                                 # type: ignore

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Classes
num_classes = 2
class_names = ['clean', 'dirty']
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Configurações do repositório no GitHub
GITHUB_TOKEN = "github_pat_SEUTOKENAQUI"
REPO_OWNER = "Nome_de_Usuario"
REPO_NAME = "Nome_do_Repositorio"
BRANCH = "main" 

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def aguardar_imagem_github(github_api_url, tentativas=3, intervalo=1):
    for _ in range(tentativas):
        resp = requests.get(github_api_url, headers=HEADERS)
        if resp.status_code == 200:
            return resp
        time.sleep(intervalo)
    return None

    
def edita_git(image_url: str, caracteristica: str):
    try:
        # Pegando a hora e data para incrementar no nome
        agora = datetime.now()
        hora_data = f"{agora.strftime('%d%m%Y_%H%M')}"
        
        # Extrai o nome do arquivo da URL
        nome_original = image_url.split("/")[-1]
        caminho_arquivo = "/".join(image_url.split("/")[-2:])
        extensao = os.path.splitext(nome_original)[-1]
        novo_nome = f"{caracteristica}_{hora_data}{extensao}"
        novo_caminho = image_url.replace(nome_original, novo_nome)

        # Constrói a URL da API para o arquivo atual
        github_api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/imagens/{nome_original}"

        # Espera antes de tentar editar a imagem (ex: 3 segundos)
        #time.sleep(2)
        
        # Obtém o conteúdo atual do arquivo
        get_response = aguardar_imagem_github(github_api_url)
        if not get_response:
            logging.error(f"Erro ao acessar a imagem no GitHub após várias tentativas.")
            return None


        file_sha = get_response.json()["sha"]
        file_content_encoded = get_response.json()["content"]
        file_content_decoded = base64.b64decode(file_content_encoded)

        # Cria o novo arquivo com o nome atualizado
        upload_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/imagens/{novo_nome}"
        
        
        # Verifica se o novo nome já existe para pegar o sha
        check_response = requests.get(upload_url, headers=HEADERS)
        if check_response.status_code == 200:
            sha_novo = check_response.json().get("sha")
        else:
            sha_novo = None

        # Monta o payload com ou sem sha
        payload_upload = {
            "message": f"Renomeando imagem para {novo_nome}",
            "content": base64.b64encode(file_content_decoded).decode("utf-8"),
            "branch": BRANCH
        }
        if sha_novo:
            payload_upload["sha"] = sha_novo

        put_response = requests.put(upload_url, headers=HEADERS, json=payload_upload)
        if put_response.status_code not in [200, 201]:
            logging.error(f"Erro ao renomear a imagem: {put_response.text}")
            return None

        # Deleta o arquivo antigo
        delete_payload = {
            "message": f"Removendo imagem antiga {nome_original}",
            "sha": file_sha,
            "branch": BRANCH
        }

        delete_response = requests.delete(github_api_url, headers=HEADERS, json=delete_payload)
        if delete_response.status_code != 200:
            logging.warning(f"Imagem renomeada, mas não foi possível excluir a antiga: {delete_response.text}")

        link_imagem = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/imagens/{novo_nome}"
        logging.info(f"Imagem renomeada com sucesso: {link_imagem}")
        # Retorna o novo link da imagem
        return link_imagem

    except Exception as e:
        logging.error(f"Erro ao atualizar o nome da imagem: {str(e)}")
        return None
    
def process_image(image_url: str):
    try:
        response = requests.get(image_url)  # Baixando a imagem do repositório do GitHub
        if response.status_code != 200:
            raise HTTPException(status_code=404, detail="Imagem não encontrada no repositório GitHub")

        img = Image.open(BytesIO(response.content))

        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        img_tensor = transform(img).unsqueeze(0).to(device)  # Adicionando batch dimension

        resul_inferencias = [] #Lista de results - sem media 
        resul_final = [] #lista resultados final - ja com media
        
        #inferencia CNN
        for model_name, model_instance in loaded_models:
            logging.info(f"Rodando inferência com o modelo {model_name}")
            with torch.no_grad():
                output = model_instance(img_tensor)

            _, predicted = torch.max(output, 1)
            class_id = predicted.item()
            resul_inferencias.append(["clean" if class_id == 0 else "dirty"])

        logging.info(f"Log da Matriz inferencia: {resul_inferencias}")
        
        #Logica de media dos valores
        cont_clean = 0
        cont_dirty = 0

        for pos in resul_inferencias:
            valor = pos[0]
            if valor == "clean":
                cont_clean += 1
            else:
                cont_dirty += 1

        if cont_clean > cont_dirty:
            resul_final.append("clean")
            caracteristica = 'clean'
        else:
            resul_final.append("dirty")
            caracteristica = 'dirty'
        logging.info(f"clean: {cont_clean}")
        logging.info(f"dirty: {cont_dirty}")

        # Apos a inferecia, ele edita o arquivo dono da URL que foi passado para a inferencia, adicionando a caracteristica no nome da imagem
        link = edita_git(image_url,caracteristica)

        return resul_final[0], link

           
    except Exception as e:
        logging.error(f"Erro ao processar a imagem: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao processar a imagem")

def create_custom_alexnet(num_classes):
    model = models.alexnet(weights=None)
    num_ftrs = model.classifier[6].in_features
    model.classifier[6] = nn.Linear(num_ftrs, num_classes)
    return model

def create_custom_resnet50(num_classes, in_channels=3):
    model = models.resnet50(weights=None)
    model.conv1 = nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    return model

def create_custom_vgg16(num_classes):
    model = models.vgg16(weights=None)
    num_ftrs = model.classifier[6].in_features
    model.classifier[6] = nn.Linear(num_ftrs, num_classes)
    return model

model_names = [
    "alexnet_sgd_best_model_D.pth",
    "resnet_sgd_best_model_D.pth",
    "vgg_sgd_best_model_D.pth",
    "alexnet_sgd_best_model_DC.pth",
    "resnet_sgd_best_model_DC.pth",
    "vgg_sgd_best_model_DC.pth"
]

loaded_models = []
models_folder = os.path.join("Models")

for model_file_name in model_names:
    model_path = os.path.join(models_folder, model_file_name)

    if "alexnet" in model_file_name:
        model_instance = create_custom_alexnet(num_classes)
    elif "resnet" in model_file_name:
        model_instance = create_custom_resnet50(num_classes, in_channels=3)
    elif "vgg" in model_file_name:
        model_instance = create_custom_vgg16(num_classes)
    else:
        continue

    try:
        model_instance.load_state_dict(torch.load(model_path, map_location=device))
        model_instance.to(device)
        model_instance.eval()
        loaded_models.append((model_file_name, model_instance))
        logging.info(f"Modelo {model_file_name} carregado com sucesso.")
    except Exception as e:
        logging.error(f"Erro ao carregar {model_file_name}: {e}")

@app.post("/processar_imagem/")
async def processar_imagem(image_url: str = Query(...)):
    try:
        # Processando a imagem e variaveis q serao add no BD
        processar = process_image(image_url)
        plate_status = processar[0]
        data_atual = datetime.now().strftime("%Y-%m-%d")
        hora_atual = datetime.now().strftime("%H:%M:%S")
        link = processar[1]
        
        # SALVANDO NO BANCO
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_query = """
            INSERT INTO resultados_placas (caracteristica, data_processamento, hora_processamento, link_imagem)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (plate_status, data_atual, hora_atual, link))
        conn.commit()
        cursor.close()
        conn.close()

        result = {
            "caracteristica_da_placa": plate_status,
            "data_do_processamento": data_atual,
            "hora_do_processamento": hora_atual,
            "link_da_imagem": link
        }

        logging.info(f"Resultado da inferência: {json.dumps(result)}")

        return result

    except Exception as e:
        logging.error(f"Erro ao processar a imagem: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro ao processar a imagem")

# -- Comandos para Iniciar o App --
# python.exe -m uvicorn main_process:app --host 127.0.0.1 --port 8001 --reload
# ou
# python3 -m uvicorn main_process:app --host 127.0.0.1 --port 8001 --reload

# A porta pode ser alterada de acordo com a sua preferencia!