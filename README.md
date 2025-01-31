# neosearch

:mag_right: :link: The favorite url search engine for people with bad memory

> Bookmarks are not an option

## cli mode

run it locally 
```sh
cd cli/
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
python3 neosearch.py
# python3 -m unittest test_neosearch.py
```

## server mode

run it locally 
```sh
pip install fastapi uvicorn
uvicorn neosearch:app --reload
```

### how to interact with the API

search using filters
```bash
curl -X GET "http://127.0.0.1:8000/search?keyword=example&repository=repo1&field=name"
```

add new repository
```bash
curl -X POST "http://localhost:8000/repositories/add" \
-H "Content-Type: application/json" \
-d '{"path": "path/repository.json"}'
```

remove repository
```bash
curl -X POST "http://localhost:8000/repositories/delete" \
-H "Content-Type: application/json" \
-d '{"path": "/caminho/para/repositorio.json"}'
```

list all repositories
```bash
curl -X GET "http://localhost:8000/repositories/list"
```

find word in all repositories
```bash
curl -X GET "http://localhost:8000/search?keyword=exemplo"
```

find word in especific repository
```bash
curl -X GET "http://localhost:8000/search?keyword=exemplo&repository=nome_do_repositorio"
```

find all
```bash
curl -X GET "http://localhost:8000/search"
```

## generate a binary 

```sh
pip install pyinstaller
pyinstaller --onefile --distpath ./dist --name neosearch main.py
```

## generate a container image

```sh
docker build -t neosearch
```

