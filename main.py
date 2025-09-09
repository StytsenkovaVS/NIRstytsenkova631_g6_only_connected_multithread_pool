import re
from itertools import combinations
from multiprocessing import Pool, cpu_count
import time
import networkx as nx
from collections import deque
from tqdm import tqdm


def find_all_shortest_paths(adj_matrix):
    num_vertices = len(adj_matrix)
    def bfs_all_paths(u, v):
        queue = deque([(u, [u])])
        all_paths = []
        shortest_length = None
        while queue:
            current_vertex, path = queue.popleft()
            if current_vertex == v:
                if shortest_length is None:
                    shortest_length = len(path)
                    all_paths.append(path)
                elif len(path) == shortest_length:
                    all_paths.append(path)
                else:
                    break
                continue
            for neighbor in range(num_vertices):
                if adj_matrix[current_vertex][neighbor] == 1 and neighbor not in path:
                    queue.append((neighbor, path + [neighbor]))
        return all_paths
    shortest_paths = {}
    for u in range(num_vertices):
        for v in range(num_vertices):
            if u != v:
                shortest_paths[(u, v)] = bfs_all_paths(u, v)
    return shortest_paths

def find_min_geodetic_sets(graph_paths):
    vertices = set()
    for key in graph_paths.keys():
        vertices.update(key)
    vertices = list(vertices)
    n = len(vertices)
    valid_sets = []
    for r in range(2, n + 1):
        found_set = False
        for combo in combinations(vertices, r):
            visited_vertices = set()
            for v1 in combo:
                for v2 in combo:
                    if v1 != v2 and (v1, v2) in graph_paths:
                        for path in graph_paths[(v1, v2)]:
                            visited_vertices.update(path)
            if visited_vertices == set(vertices):
                valid_sets.append(combo)
                found_set = True
        if found_set:
            break
    return valid_sets

def find_minimal_forcing_subsets(sets):
    forcing_subsets = []
    for i, current_set in enumerate(sets):
        found = False
        for r in range(1, len(current_set) + 1):
            for subset in combinations(current_set, r):
                subset = set(subset)
                is_unique = True
                for j, other_set in enumerate(sets):
                    if i != j and subset.issubset(other_set):
                        is_unique = False
                        break
                if is_unique:
                    forcing_subsets.append(subset)
                    found = True
                    break
            if found:
                break
    return min(forcing_subsets, key=len)

def find_forcing_geodetic_number(adj_matrix):
    shortest_paths = find_all_shortest_paths(adj_matrix)
    min_geodetic_sets = find_min_geodetic_sets(shortest_paths)
    if len(min_geodetic_sets) > 1:
        return len(find_minimal_forcing_subsets(min_geodetic_sets))
    else:
        return 0

def is_dominating_set(adj_matrix, subset):
    n = len(adj_matrix)
    dominated = set(subset)
    for vertex in subset:
        for neighbor in range(n):
            if adj_matrix[vertex][neighbor] == 1:
                dominated.add(neighbor)
    return len(dominated) == n

def find_minimum_dominating_sets(adj_matrix):
    n = len(adj_matrix)
    min_dominating_sets = []
    for k in range(1, n + 1):
        for subset in combinations(range(n), k):
            if is_dominating_set(adj_matrix, subset):
                if not min_dominating_sets or len(subset) == len(min_dominating_sets[0]):
                    min_dominating_sets.append(subset)
                elif len(subset) < len(min_dominating_sets[0]):
                    min_dominating_sets = [subset]
        if min_dominating_sets:
            break
    return min_dominating_sets

def is_perfect_dominating_set(adj_matrix, subset):
    n = len(adj_matrix)
    for vertex in range(n):
        if vertex not in subset:
            neighbors_count = sum(adj_matrix[vertex][neighbor] for neighbor in subset)
            if neighbors_count != 1:
                return False
    return True

def find_perfect_dominating_set(adj_matrix):
    min_dominating_sets = find_minimum_dominating_sets(adj_matrix)
    for subset in min_dominating_sets:
        if is_perfect_dominating_set(adj_matrix, subset):
            return subset
    return None

def find_perfect_dominating_number(adj_matrix):
    perfect_dominating_set = find_perfect_dominating_set(adj_matrix)
    if perfect_dominating_set is not None:
        return len(perfect_dominating_set)
    else:
        return 0

def parse_graph_file(filename):
    graphs = []
    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            try:
                graph = nx.from_graph6_bytes(line.encode('ascii'))
                adj_matrix = nx.to_numpy_array(graph, dtype=int)
            except nx.NetworkXError as e:
                print(f"Ошибка в строке '{line}': {e}")
            graphs.append(adj_matrix)
    return graphs

def process_graph(graph_info):
    idx, graph = graph_info
    min_forc_geo = find_forcing_geodetic_number(graph)
    min_perf_dom = find_perfect_dominating_number(graph)
    return idx, graph, min_forc_geo, min_perf_dom

if __name__ == "__main__":
    input_file = '3.txt'
    output_file = 'output3.txt'
    graphs = parse_graph_file(input_file)
    num_vertices = re.match(r'(\d+)', input_file)
    num_vertices = int(num_vertices.group(1))
    table = [[0] * (num_vertices+1) for _ in range(num_vertices+1)]
    graph_infos = [(idx, graph) for idx, graph in enumerate(graphs)]
    total_graphs = len(graph_infos)
    start_time = time.perf_counter()
    with Pool(cpu_count()) as pool:
        results = list(tqdm(pool.imap(process_graph, graph_infos), total=total_graphs,
                            desc="Прогресс"))
    with open(output_file, 'w') as f:
        for idx, graph, min_forc_geo, min_perf_dom in results:
            f.write(f"Graph {idx + 1}: g={min_forc_geo} d={min_perf_dom}\n")
            f.write(f"{graph}\n")
            f.write(f"\n")
            table[min_perf_dom][min_forc_geo] += 1
    end_time = time.perf_counter()
    print("Количество вершин:", num_vertices)
    print("Таблица распределения графов по значениям инвариантов:")
    for row in table:
        print(" ".join(map(str, row)))
    elapsed_time = end_time - start_time
    print(f"Прошедшее время: {elapsed_time:.4f} секунд")
    while True:
        forc_geo_num = input("Введите принудительное геодезическое число (0-10): ")
        perf_dom_num = input("Введите число совершенного доминирования (0-10): ")
        if forc_geo_num and perf_dom_num:
            forc_geo_num = int(forc_geo_num)
            perf_dom_num = int(perf_dom_num)
            found_graphs = [g for g in results if g[2] == forc_geo_num and g[3] == perf_dom_num]
            if found_graphs:
                print(f"Графы с числом совершенного доминирования: {perf_dom_num}, "
                      f"принудительным геодезическим числом: {forc_geo_num}")
                for idx, graph, forc_geo_num, perf_dom_num in found_graphs:
                    print(graph)
                    print("")
            else:
                print("Графы с заданными параметрами не найдены.")
        else:
            break
