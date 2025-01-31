from fastapi import FastAPI, BackgroundTasks, HTTPException, Query
from typing import List, Optional
import os
import json
import requests
import hashlib
import yaml
from pydantic import BaseModel
from time import time

app = FastAPI()

# Caminho padrão para o arquivo de configuração YAML
CONFIG_PATH = "config.yaml"
CONFIG_ENV_VAR = "CONFIG_FILE_PATH"

class RepositoryAddRequest(BaseModel):
    path: str

class RepositoryDeleteRequest(BaseModel):
    path: str

# Variáveis de controle de modificação
last_config_check_time = time()
config_file_mtime = os.path.getmtime(CONFIG_PATH)
repo_hashes = {}

def load_config():
    """
    Carrega o arquivo de configuração YAML automaticamente.
    Primeiro tenta carregar do caminho local, depois de uma variável de ambiente.
    """
    config_path = os.getenv(CONFIG_ENV_VAR, CONFIG_PATH)
    if not os.path.exists(config_path):
        raise HTTPException(status_code=404, detail="Configuration file not found.")
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def save_config(config):
    """
    Salva o arquivo de configuração YAML no caminho local.
    """
    with open(CONFIG_PATH, 'w', encoding='utf-8') as file:
        yaml.dump(config, file)

def validate_repository(repo: str):
    """
    Valida um repositório (URL ou arquivo local).
    """
    try:
        if repo.startswith("http://") or repo.startswith("https://"):
            response = requests.get(repo)
            response.raise_for_status()
            data = response.json()
            return True, data
        else:
            if not os.path.exists(repo):
                return False, "File not found"
            with open(repo, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return True, data
    except Exception as e:
        return False, f"Invalid format: {str(e)}"

def get_repo_hash(data):
    """
    Gera o hash MD5 de um conteúdo para detectar alterações.
    """
    content = json.dumps(data, sort_keys=True).encode('utf-8')
    return hashlib.md5(content).hexdigest()

def check_config_changes():
    """
    Verifica se houve alteração no arquivo de configuração.
    """
    global config_file_mtime, last_config_check_time
    current_mtime = os.path.getmtime(CONFIG_PATH)
    if current_mtime != config_file_mtime:
        config_file_mtime = current_mtime
        last_config_check_time = time()
        return True
    return False

def check_repo_changes(config):
    """
    Verifica se algum repositório teve alterações.
    """
    global repo_hashes
    for repo in config.get("local_files", []):
        is_valid, message = validate_repository(repo)
        if is_valid:
            repo_hash = get_repo_hash(message)
            if repo not in repo_hashes:
                repo_hashes[repo] = repo_hash
            elif repo_hashes[repo] != repo_hash:
                repo_hashes[repo] = repo_hash
                return True
    return False

def background_task():
    """
    Tarefa em segundo plano para checar alterações de configuração e repositórios.
    """
    if check_config_changes():
        print("Arquivo de configuração foi alterado.")
    if check_repo_changes(load_config()):
        print("Algum repositório teve alteração.")

@app.post("/repositories/add")
def add_repository(repo: RepositoryAddRequest):
    """
    Adiciona um repositório à lista de repositórios no arquivo de configuração YAML.
    """
    config = load_config()
    if repo.path in config.get("local_files", []):
        raise HTTPException(status_code=400, detail="Repository already exists.")
    config.setdefault("local_files", []).append(repo.path)
    save_config(config)
    return {"message": "Repository added successfully."}

@app.post("/repositories/delete")
def delete_repository(repo: RepositoryDeleteRequest):
    """
    Remove um repositório da lista de repositórios no arquivo de configuração YAML.
    """
    config = load_config()
    if repo.path not in config.get("local_files", []):
        raise HTTPException(status_code=404, detail="Repository not found.")
    config["local_files"].remove(repo.path)
    save_config(config)
    return {"message": "Repository deleted successfully."}

@app.get("/repositories/list")
def list_repositories():
    """
    Lista todos os repositórios configurados no arquivo de configuração YAML.
    """
    config = load_config()
    return {"repositories": config.get("local_files", [])}

@app.get("/search")
def search(
    keyword: Optional[str] = Query(None, description="Palavra-chave para busca"),
    repository: Optional[str] = Query(None, description="Filtrar por repositório específico"),
    field: Optional[str] = Query(None, description="Campo específico para busca")
):
    """
    Realiza uma busca nos repositórios configurados.
    """
    config = load_config()
    repositories = config.get("local_files", [])
    results = []

    for repo in repositories:
        is_valid, message = validate_repository(repo)
        if not is_valid:
            continue

        if repo.startswith("http://") or repo.startswith("https://"):
            response = requests.get(repo)
            data = response.json()
        else:
            with open(repo, 'r', encoding='utf-8') as file:
                data = json.load(file)

        # Filtra os dados com base nos parâmetros
        if keyword and field:
            if field == "tags":
                filtered = [entry for entry in data if field in entry and any(keyword.lower() in tag.lower() for tag in entry[field])]
            else:
                filtered = [entry for entry in data if field in entry and keyword.lower() in str(entry[field]).lower()]
        elif keyword:
            filtered = [entry for entry in data if any(keyword.lower() in str(entry[f]).lower() for f in entry)]
        else:
            filtered = data

        if repository:
            filtered = [entry for entry in filtered if entry.get("repository") == repository]

        results.extend(filtered)

    return {"results": results}

@app.on_event("startup")
async def startup_event():
    """
    Executa tarefas em background assim que a aplicação é iniciada.
    """
    from fastapi import BackgroundTasks
    background = BackgroundTasks()
    background.add_task(background_task)
