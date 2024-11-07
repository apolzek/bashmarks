import json
import os
import re
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

# Função para ler o arquivo JSON
def load_data_from_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Função para filtrar dados por qualquer campo (incluindo a URL, tag, description, category)
def filter_data(data, keyword=None):
    filtered = data

    # Se houver uma palavra-chave (keyword), fazemos uma busca geral por substrings em todos os campos
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

    # Palavra solta (fora dos filtros específicos)
    remaining_query = query
    for field, value in matches:
        remaining_query = remaining_query.replace(f'{field}="{value}"', "").strip()

    return filters, remaining_query

# Função principal
def main(file_path):
    try:
        # Carregar dados do arquivo
        data = load_data_from_file(file_path)
    except FileNotFoundError as e:
        print(e)
        return

    console = Console()
    current_page = 1
    per_page = 5
    filtered_data = data
    total_pages = (len(filtered_data) + per_page - 1) // per_page  # Calcular total de páginas

    # Exibindo todos os dados inicialmente
    if not filtered_data:
        console.print("No results found!", style="bold red")
        return

    while True:
        # Exibindo os resultados da página atual
        display_table(filtered_data, current_page, per_page)

        # Exibindo navegação e opções de filtro
        console.print(f"\nPage {current_page}/{total_pages}", style="bold")
        
        # Perguntar por filtros ou limpar filtros
        user_input = Prompt.ask("Press 'n' for next, 'p' for previous, 'f' to filter, 'c' to clear filters, 's' to select a record, or 'q' to quit").lower()

        if user_input == 'n' and current_page < total_pages:
            current_page += 1
        elif user_input == 'p' and current_page > 1:
            current_page -= 1
        elif user_input == 'q':
            break
        elif user_input == 'f':
            # Aplicar filtros dinâmicos
            query = Prompt.ask("Enter your search query (e.g., 'algebra', 'description=\"math\"', 'tag=\"science\"')")
            
            # Se houver uma palavra chave solta (sem filtros), ela será aplicada a todos os campos
            filters, keyword = parse_query(query)
            
            # Se houver uma palavra-chave sem filtro, ela será aplicada a todos os campos (url, description, category, tags)
            if not filters and keyword:
                filtered_data = filter_data(data, keyword)
            else:
                # Filtrar dados com base nos filtros especificados
                filtered_data = filter_data(data, keyword)
                
            total_pages = (len(filtered_data) + per_page - 1) // per_page  # Recalcular total de páginas após o filtro
        elif user_input == 'c':
            # Limpar filtros
            filtered_data = data
            total_pages = (len(filtered_data) + per_page - 1) // per_page  # Recalcular total de páginas
        elif user_input == 's':
            # Selecionar um registro específico para exibir detalhes completos
            record_number = Prompt.ask("Enter the record number to view full details", default="1")
            try:
                record_number = int(record_number)
                display_full_record_in_table(filtered_data, record_number)
            except ValueError:
                console.print("Invalid input. Please enter a valid number.", style="bold red")
        else:
            console.print("Invalid input. Please press 'n', 'p', 'f', 'c', 's' or 'q'.", style="bold red")

if __name__ == "__main__":
    # Caminho do arquivo JSON será passado como parâmetro ao iniciar o script
    file_path = Prompt.ask("Enter the path to the urls.json file")
    main(file_path)
