import pytest
from fastapi.testclient import TestClient
from neosearch import app 

client = TestClient(app)

# Teste para o endpoint de adicionar repositório
def test_add_repository():
    # Preparar o corpo da requisição
    data = {"path": "repo/test_repo.json"}

    # Enviar a requisição POST para adicionar um repositório
    response = client.post("/repositories/add", json=data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Repository added successfully."}

# Teste para o endpoint de deletar repositório
def test_delete_repository():
    # Preparar o corpo da requisição
    data = {"path": "repo/test_repo.json"}

    # Adicionar o repositório antes de tentar deletá-lo
    client.post("/repositories/add", json=data)

    # Enviar a requisição POST para deletar o repositório
    response = client.post("/repositories/delete", json=data)
    
    assert response.status_code == 200
    assert response.json() == {"message": "Repository deleted successfully."}

# Teste para listar repositórios
def test_list_repositories():
    # Enviar a requisição GET para listar repositórios
    response = client.get("/repositories/list")
    
    assert response.status_code == 200
    assert "repositories" in response.json()

# Teste para buscar repositórios
def test_search():
    # Adicionar um repositório de teste
    data = {"path": "repo/test_repo.json"}
    client.post("/repositories/add", json=data)

    # Enviar uma requisição GET para buscar por um termo (alterando conforme o seu formato de dados)
    response = client.get("/search", params={"keyword": "test"})
    
    assert response.status_code == 200
    assert "results" in response.json()

# Teste para verificar o comportamento com repositórios inválidos
def test_invalid_repository():
    data = {"path": "repo/invalid_repo.json"}
    response = client.post("/repositories/add", json=data)
    
    assert response.status_code == 400
    assert response.json() == {"detail": "Repository already exists."}
