import json
import os
import re
import requests
import yaml
from rich.console import Console
from rich.table import Table

# Função para ler o arquivo JSON
def load_data_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

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

# Função para filtrar dados por qualquer campo (incluindo a URL, tag, description, category)
def filter_data(data, keyword=None):
    filtered = data
    if keyword:
        filtered = [entry for entry in filtered if any(keyword.lower() in str(entry[field]).lower() for field in entry)]
    return filtered

# Função para truncar a descrição se for maior que 20 caracteres
def truncate_description(description, length=20):
    if len(description) > length:
        return description[:length] + '...'
    return description

# Função para exibir os dados em uma tabela com numeração
def display_table(data, page, per_page):
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    page_data = data[start_index:end_index]

    table = Table(title="Search Results")
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
    
    table = Table(title="Full Record Details")
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

    # Processar os arquivos locais
    for file_path in config.get('local_files', []):
        try:
            data = load_data_from_file(file_path)
            all_data.extend(data)
        except FileNotFoundError as e:
            print(e)

    # Processar as URLs
    for url in config.get('urls', []):
        try:
            file_path = download_json_from_url(url)
            data = load_data_from_file(file_path)
            all_data.extend(data)
        except Exception as e:
            print(f"Erro ao processar a URL {url}: {e}")

    console = Console()
    current_page = 1
    per_page = 10
    filtered_data = all_data
    total_pages = (len(filtered_data) + per_page - 1) // per_page  # Calcular total de páginas

    if not filtered_data:
        console.print("No results found!", style="bold red")
        return

    while True:
        # Exibindo os resultados da página atual
        display_table(filtered_data, current_page, per_page)

        # Exibindo navegação e opções de filtro
        console.print(f"\nPage {current_page}/{total_pages}", style="bold")
        
        user_input = input("Press 'n' for next, 'p' for previous, 'f' to filter, 'c' to clear filters, 's' to select a record, 'r' for repositories, or 'q' to quit: ").lower()

        if user_input == 'n' and current_page < total_pages:
            current_page += 1
        elif user_input == 'p' and current_page > 1:
            current_page -= 1
        elif user_input == 'q':
            break
        elif user_input == 'f':
            query = input("Enter your search query (e.g., 'algebra', 'description=\"math\"', 'tag=\"science\"'): ")
            filters, keyword = parse_query(query)
            if not filters and keyword:
                filtered_data = filter_data(all_data, keyword)
            else:
                filtered_data = filter_data(all_data, keyword)
                
            total_pages = (len(filtered_data) + per_page - 1) // per_page  # Recalcular total de páginas após o filtro
        elif user_input == 'c':
            filtered_data = all_data
            total_pages = (len(filtered_data) + per_page - 1) // per_page  # Recalcular total de páginas
        elif user_input == 's':
            record_number = input("Enter the record number to view full details: ")
            try:
                record_number = int(record_number)
                display_full_record_in_table(filtered_data, record_number)
            except ValueError:
                console.print("Invalid input. Please enter a valid number.", style="bold red")
        elif user_input == 'r':
            # Exibir repositórios
            repositories = config.get('local_files', [])
            console.print("Repositories:", style="bold")
            if not repositories:
                console.print("No repositories available.", style="bold red")
            else:
                for idx, repo in enumerate(repositories, start=1):
                    console.print(f"{idx}. {repo}")
            
            # Adicionar ou remover repositórios
            repo_action = input("Press 'a' to add a repository, 'd' to delete a repository, or 'q' to return: ").lower()
            if repo_action == 'a':
                new_repo = input("Enter the repository URL to add: ")
                repositories.append(new_repo)
                config['repositories'] = repositories
                save_yaml_config(yaml_path, config)
                console.print(f"Repository '{new_repo}' added.", style="bold green")
            elif repo_action == 'd':
                repo_number = input("Enter the number of the repository to remove: ")
                try:
                    repo_number = int(repo_number)
                    removed_repo = repositories.pop(repo_number - 1)
                    config['repositories'] = repositories
                    save_yaml_config(yaml_path, config)
                    console.print(f"Repository '{removed_repo}' removed.", style="bold red")
                except (ValueError, IndexError):
                    console.print("Invalid repository number.", style="bold red")
            elif repo_action == 'q':
                continue
        else:
            console.print("Invalid input. Please press 'n', 'p', 'f', 'c', 's', 'r' or 'q'.", style="bold red")

if __name__ == "__main__":
    main()
