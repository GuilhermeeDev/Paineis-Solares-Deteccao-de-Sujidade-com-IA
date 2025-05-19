from fastapi import FastAPI, File, UploadFile, HTTPException# type: ignore
import requests # type: ignore
import base64
import logging
import time
import uvicorn # type: ignore

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# Configurações do repositório no GitHub
GITHUB_TOKEN = "github_pat_SEUTOKENAQUI"
REPO_OWNER = "Nome_de_Usuario"
REPO_NAME = "Nome_do_Repositorio"
BRANCH = "main" 
UPLOAD_PATH = "imagens"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# URL da API de processamento
porta = 8001
URL_API_PROCESSAMENTO = f"http://127.0.0.1:{porta}/processar_imagem/" #Lembre-se de substituir o xxxx pela porta escolhida para a API de processamento padrao = 8000

@app.get("/")
def read_root():
    return {"Mensagem": "A API está pronta para receber as imagens!"}

def esperar_disponibilidade_imagem(url, tentativas=3, intervalo=1):
    for _ in range(tentativas):
        response = requests.get(url)
        if response.status_code == 200:
            return True
        time.sleep(intervalo)
    return False

@app.post("/envia_git/")
async def upload_image(files: list[UploadFile] = File(...)):
    resultados = []

    try:
        for file in files:
            image_data = await file.read()
            image_b64 = base64.b64encode(image_data).decode("utf-8")
            github_file_path = f"{UPLOAD_PATH}/{file.filename}"
            github_api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{github_file_path}"

            # Verifica se o arquivo já existe no GitHub
            response = requests.get(github_api_url, headers=HEADERS)
            sha = response.json().get("sha") if response.status_code == 200 else None

            payload = {
                "message": f"Upload de {file.filename}",
                "content": image_b64,
                "branch": BRANCH
            }
            if sha:
                payload["sha"] = sha

            response = requests.put(github_api_url, json=payload, headers=HEADERS)
            if response.status_code not in [200, 201]:
                raise HTTPException(status_code=400, detail=f"Erro ao enviar {file.filename} para o GitHub")

            # Sleep forçado antes de continuar (ex: 1 segundo)
            time.sleep(1)

            
            url_imagem_github = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{github_file_path}"

            # Verifica se a imagem já está disponível no GitHub
            if not esperar_disponibilidade_imagem(url_imagem_github):
                resultados.append({
                    "arquivo": file.filename,
                    "erro": "Imagem não disponível no GitHub após múltiplas tentativas"
                })
                continue
            
            # Enviando para a API de processamento
            try:
                response = requests.post(f"{URL_API_PROCESSAMENTO}?image_url={url_imagem_github}")
                if response.status_code == 200:
                    resultado = response.json()
                    resultados.append({
                        "arquivo": file.filename,
                        "resultado_inferencia": resultado
                    })
                else:
                    resultados.append({
                        "arquivo": file.filename,
                        "erro": response.text
                    })
            except Exception as e:
                resultados.append({
                    "arquivo": file.filename,
                    "erro": str(e)
                })

        return {"Resultados": resultados}

    except Exception as e:
        logging.error(f"Erro interno: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno no servidor")

#if __name__ == "__main__":
#    uvicorn.run(app, host="127.0.0.1", port=8000)

# python3 -m uvicorn cliente_rbpi:app --host 127.0.0.1 --port 8000 --reload
# Ou
# #python.exe -m uvicorn cliente_rbpi:app --host 127.0.0.1 --port 8000 --reload