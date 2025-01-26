import json
import os
import re
import requests
import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

# Função para validar um repositório (arquivo local ou URL)
def validate_repository(repo):
    try:
        if repo.startswith("http://") or repo.startswith("https://"):
            # Validação de URL
            response = requests.get(repo)
            response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
            data = response.json()  # Tenta carregar o JSON
            return True, "OK"
        else:
            # Validação de arquivo local
            if not os.path.exists(repo):
                return False, "File not found"
            with open(repo, 'r', encoding='utf-8') as file:
                data = json.load(file)  # Tenta carregar o JSON
            return True, "OK"
    except Exception as e:
        return False, f"Invalid format: {str(e)}"

# Função para ler o arquivo JSON
def load_data_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"Erro ao processar o arquivo {file_path}: JSON inválido - {e}")
        return None  # Retorna None para indicar que o arquivo está inválido
    except Exception as e:
        print(f"Erro ao processar o arquivo {file_path}: {e}")
        return None  # Retorna None para indicar que o arquivo está inválido

# Função para baixar o arquivo da URL
def download_json_from_url(url, download_dir=".repositories"):
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    response = requests.get(url)
    response.raise_for_status()  # Levanta um erro se a requisição falhar
    
    file_name = os.path.join(download_dir, os.path.basename(url))
    with open(file_name, 'w', encoding='utf-8') as file:
        json.dump(response.json(), file, ensure_ascii=False, indent=4)
    
    return file_name

# Função para filtrar dados por campo específico (tags, description, category)
def filter_data(data, keyword=None, repository=None, field=None):
    filtered = data
    if keyword and field:
        # Filtra apenas no campo especificado
        if field == "tags":  # Caso especial para tags (lista de strings)
            filtered = [entry for entry in filtered if field in entry and any(keyword.lower() in tag.lower() for tag in entry[field])]
        else:
            filtered = [entry for entry in filtered if field in entry and keyword.lower() in str(entry[field]).lower()]
    elif keyword:
        # Filtra em todos os campos (busca global)
        filtered = [entry for entry in filtered if any(keyword.lower() in str(entry[f]).lower() for f in entry)]
    if repository:
        filtered = [entry for entry in filtered if entry.get("repository") == repository]
    return filtered

# Função para truncar a descrição se for maior que 20 caracteres
def truncate_description(description, length=20):
    if len(description) > length:
        return description[:length] + '...'
    return description

# Função para exibir os dados em uma tabela com numeração
def display_table(data, page, per_page, total_pages):
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    page_data = data[start_index:end_index]

    # Título da tabela com a paginação
    table_title = f"Search Results (Page {page} of {total_pages})"
    table = Table(title=table_title, box=box.SQUARE)
    table.add_column("No.", justify="center", style="cyan", width=6)
    table.add_column("URL", justify="left", style="magenta", width=40)
    table.add_column("Description", justify="left", style="green")
    table.add_column("Category", justify="left", style="yellow")

    for idx, entry in enumerate(page_data, start=1):
        truncated_description = truncate_description(entry["description"])
        table.add_row(str(idx), entry["url"], truncated_description, entry["category"])

    console = Console()
    console.print(table)

# Função para exibir detalhes completos de um registro dentro de uma tabela
def display_full_record_in_table(data, index):
    if index < 1 or index > len(data):
        console.print("Invalid selection. Please choose a valid number.", style="bold red")
        return

    entry = data[index - 1]  # Ajuste no índice (começa de 1 na interface)
    
    table = Table(title="Full Record Details", box=box.SQUARE)
    table.add_column("Field", justify="left", style="cyan", width=15)
    table.add_column("Value", justify="left", style="green")

    table.add_row("URL", entry["url"])
    table.add_row("Description", entry["description"])
    table.add_row("Category", entry["category"])
    
    if "tags" in entry:
        table.add_row("Tags", ", ".join(entry["tags"]))
    else:
        table.add_row("Tags", "No tags available.")
    
    console = Console()
    console.print(table)

# Função para processar a query do usuário
def parse_query(query):
    filters = {}
    pattern = re.compile(r'(\w+)="([^"]+)"')
    matches = pattern.findall(query)

    for field, value in matches:
        filters[field] = value

    remaining_query = query
    for field, value in matches:
        remaining_query = remaining_query.replace(f'{field}="{value}"', "").strip()

    return filters, remaining_query

# Função para carregar os dados do YAML
def load_yaml_config(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

# Função para salvar os dados no arquivo YAML
def save_yaml_config(yaml_path, config):
    with open(yaml_path, 'w', encoding='utf-8') as file:
        yaml.dump(config, file)

# Função principal
def main():
    yaml_path = os.path.join(os.getcwd(), 'config.yaml')
    
    if not os.path.exists(yaml_path):
        print(f"O arquivo de configuração {yaml_path} não foi encontrado.")
        return

    # Carregar configuração do YAML
    config = load_yaml_config(yaml_path)
    
    all_data = []
    console = Console()

    # Validar repositórios no início do programa
    repositories = config.get('local_files', []) + config.get('urls', [])
    invalid_repos = []
    for repo in repositories:
        is_valid, message = validate_repository(repo)
        if not is_valid:
            invalid_repos.append((repo, message))

    # Exibir warning se houver repositórios inválidos
    if invalid_repos:
        console.print("\n[bold yellow]WARNING: Some repositories are invalid:[/bold yellow]")
        for repo, message in invalid_repos:
            console.print(f"- [bold red]{repo}[/bold red]: {message}")
        console.print("\n")

    # Processar os arquivos locais
    for file_path in config.get('local_files', []):
        try:
            data = load_data_from_file(file_path)
            if data is not None:  # Ignora arquivos inválidos
                for entry in data:
                    entry["repository"] = file_path  # Adiciona o repositório ao registro
                all_data.extend(data)
        except FileNotFoundError as e:
            print(e)

    # Processar as URLs
    for url in config.get('urls', []):
        try:
            file_path = download_json_from_url(url)
            data = load_data_from_file(file_path)
            if data is not None:  # Ignora arquivos inválidos
                for entry in data:
                    entry["repository"] = url  # Adiciona o repositório ao registro
                all_data.extend(data)
        except Exception as e:
            print(f"Erro ao processar a URL {url}: {e}")

    current_page = 1
    per_page = 10
    filtered_data = all_data
    total_pages = (len(filtered_data) + per_page - 1) // per_page  # Calcular total de páginas

    if not filtered_data:
        console.print("No results found!", style="bold red")
        return

    # Variável para armazenar o filtro atual
    current_filter = None
    current_field = None  # Campo específico para filtrar (tags, description, category)

    while True:
        # Exibindo os resultados da página atual
        display_table(filtered_data, current_page, per_page, total_pages)

        # Exibindo navegação e opções de filtro
        options_line1 = Text()
        options_line1.append("Press ", style="default")
        options_line1.append("'n'", style="bold cyan")
        options_line1.append(" for next, ", style="default")
        options_line1.append("'p'", style="bold cyan")
        options_line1.append(" for previous, ", style="default")
        options_line1.append("'f'", style="bold cyan")
        options_line1.append(" to filter, ", style="default")
        options_line1.append("'c'", style="bold cyan")
        options_line1.append(" to clear filters", style="default")

        options_line2 = Text()
        options_line2.append("Press ", style="default")
        options_line2.append("'s'", style="bold cyan")
        options_line2.append(" to select a record, ", style="default")
        options_line2.append("'r'", style="bold cyan")
        options_line2.append(" for repositories, ", style="default")
        options_line2.append("'fr'", style="bold cyan")
        options_line2.append(" to filter by repository, ", style="default")
        options_line2.append("'q'", style="bold cyan")
        options_line2.append(" to quit", style="default")

        console.print(options_line1)
        console.print(options_line2)

        user_input = input("Enter your choice: ").lower()

        if user_input == 'n' and current_page < total_pages:
            current_page += 1
        elif user_input == 'p' and current_page > 1:
            current_page -= 1
        elif user_input == 'q':
            break
        elif user_input == 'f':
            query = input("Enter your search query (e.g., 'algebra', 'description=\"math\"', 'tags=\"science\"', 'category=\"math\"'): ")
            filters, keyword = parse_query(query)
            if filters:
                # Aplica o filtro no campo específico
                current_field = list(filters.keys())[0]  # Pega o primeiro campo (tags, description, category)
                current_filter = filters[current_field]  # Pega o valor do filtro
                filtered_data = filter_data(all_data, keyword=current_filter, field=current_field)
            elif keyword:
                # Busca global (em todos os campos)
                current_filter = keyword
                current_field = None
                filtered_data = filter_data(all_data, keyword=current_filter)
                
            total_pages = (len(filtered_data) + per_page - 1) // per_page  # Recalcular total de páginas após o filtro
            current_page = 1  # Resetar para a primeira página após aplicar o filtro
        elif user_input == 'c':
            current_filter = None  # Limpa o filtro atual
            current_field = None
            filtered_data = all_data
            total_pages = (len(filtered_data) + per_page - 1) // per_page  # Recalcular total de páginas
            current_page = 1  # Resetar para a primeira página após limpar o filtro
        elif user_input == 's':
            record_number = input("Enter the record number to view full details: ")
            try:
                record_number = int(record_number)
                display_full_record_in_table(filtered_data, record_number)
            except ValueError:
                console.print("Invalid input. Please enter a valid number.", style="bold red")
        elif user_input == 'r':
            # Exibir repositórios com status
            repositories = config.get('local_files', []) + config.get('urls', [])
            console.print("Repositories:", style="bold")
            if not repositories:
                console.print("No repositories available.", style="bold red")
            else:
                console.print("0. All repositories (global search)", style="bold cyan")
                for idx, repo in enumerate(repositories, start=1):
                    is_valid, message = validate_repository(repo)
                    status = "[bold green]OK[/bold green]" if is_valid else f"[bold red]INVALID: {message}[/bold red]"
                    console.print(f"{idx}. {repo} - {status}")
            
            # Adicionar ou remover repositórios
            repo_action = input("Press 'a' to add a repository, 'd' to delete a repository, or 'q' to return: ").lower()
            if repo_action == 'a':
                new_repo = input("Enter the repository URL to add: ")
                if new_repo.endswith('.json'):
                    config['local_files'].append(new_repo)
                else:
                    config['urls'].append(new_repo)
                save_yaml_config(yaml_path, config)
                console.print(f"Repository '{new_repo}' added.", style="bold green")
            elif repo_action == 'd':
                repo_number = input("Enter the number of the repository to remove: ")
                try:
                    repo_number = int(repo_number)
                    if repo_number <= len(config.get('local_files', [])):
                        removed_repo = config['local_files'].pop(repo_number - 1)
                    else:
                        removed_repo = config['urls'].pop(repo_number - 1 - len(config.get('local_files', [])))
                    save_yaml_config(yaml_path, config)
                    console.print(f"Repository '{removed_repo}' removed.", style="bold red")
                except (ValueError, IndexError):
                    console.print("Invalid repository number.", style="bold red")
            elif repo_action == 'q':
                continue
        elif user_input == 'fr':
            # Filtrar por repositório
            repositories = config.get('local_files', []) + config.get('urls', [])
            console.print("Repositories:", style="bold")
            if not repositories:
                console.print("No repositories available.", style="bold red")
            else:
                console.print("0. All repositories (global search)", style="bold cyan")
                for idx, repo in enumerate(repositories, start=1):
                    console.print(f"{idx}. {repo}")
            
            repo_number = input("Enter the number of the repository to filter by (or 0 for global search): ")
            try:
                repo_number = int(repo_number)
                if repo_number == 0:
                    filtered_data = filter_data(all_data, keyword=current_filter, field=current_field)  # Mantém o filtro de busca
                elif repo_number < 1 or repo_number > len(repositories):
                    console.print("Invalid repository number.", style="bold red")
                else:
                    selected_repo = repositories[repo_number - 1]
                    filtered_data = filter_data(all_data, keyword=current_filter, field=current_field, repository=selected_repo)
                total_pages = (len(filtered_data) + per_page - 1) // per_page  # Recalcular total de páginas após o filtro
                current_page = 1  # Resetar para a primeira página após aplicar o filtro
            except ValueError:
                console.print("Invalid input. Please enter a valid number.", style="bold red")
        else:
            console.print("Invalid input. Please try again.", style="bold red")

if __name__ == "__main__":
    main()