from intra import ic
import json
from collections import defaultdict
import networkx as nx

CAMPUS_ID = 56
CURSUS_ID = 21

def fetch():
    res = ic.pages_threaded('scale_teams', params={
        'filter[campus_id]': CAMPUS_ID,
        'filter[cursus_id]': CURSUS_ID,
        'range[begin_at]': "2023-01-01,2024-08-12"
    })
    return res

def process(res):
    nodes = set()
    links = defaultdict(int)
    for entry in res:
        corrector = entry['corrector']['login']
        correcteds = entry['correcteds']
        nodes.add(corrector)
        for corrected in correcteds:
            corrected_login = corrected['login']
            nodes.add(corrected_login)
            links[(corrector, corrected_login)] += 1
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from([(source, target, {'weight': value}) for (source, target), value in links.items()])
    # Perform clustering
    import community as community_louvain
    partition = community_louvain.best_partition(G)
    clusters = defaultdict(list)
    for node, group in partition.items():
        clusters[group].append(node)
    # Save each cluster's data separately
    for cluster, cluster_nodes in clusters.items():
        cluster_links = [(source, target, value) for (source, target), value in links.items() if source in cluster_nodes and target in cluster_nodes]
        nodes_data = [{"id": node, "group": partition[node]} for node in cluster_nodes]
        links_data = [{"source": source, "target": target, "value": value} for source, target, value in cluster_links]
        cluster_data = {
            "nodes": nodes_data,
            "links": links_data
        }
        with open(f'web/data_cluster_{cluster}.json', 'w') as f:
            json.dump(cluster_data, f, indent=4)
    # Save the list of clusters
    with open('web/clusters.json', 'w') as f:
        json.dump(list(clusters.keys()), f, indent=4)
    # Return the original data for the main visualization
    nodes_data = [{"id": node, "group": partition[node]} for node in nodes]
    links_data = [{"source": source, "target": target, "value": value} for (source, target), value in links.items()]
    return {
        "nodes": nodes_data,
        "links": links_data
    }

def write(data):
    with open('web/data.json', 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    ic.progress_enable()
    res = fetch()
    data = process(res)
    write(data)