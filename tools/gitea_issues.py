import json
from time import time
#with open("/home/john/issues.json", "r") as f:
#    data = json.loads(f.read())
#with open("/home/john/issues2.json", "r") as f:
#    data.extend(json.loads(f.read()))

print("Fetching issues...", end='')
start = time()
from gitea import Gitea, Repository, Issue
g = Gitea("https://gamedev.ffwf.net/gitea", token_text="febad52bd50f87fb17691c5e972597d6fff73452")
repo = Repository.request(g, "john", "McRogueFace")
issues = repo.get_issues()
dur = time() - start
print(f"({dur:.1f}s)")
print("Gitea Version: " + g.get_version())
print("API-Token belongs to user: " + g.get_user().username)

data = [
    {
        "labels": i.labels,
        "body": i.body,
        "number": i.number,
    }
    for i in issues
    ]

input()

def front_number(txt):
    if not txt[0].isdigit(): return None
    number = ""
    for c in txt:
        if not c.isdigit():
            break
        number += c
    return int(number)

def split_any(txt, splitters):
    tokens = []
    txt = [txt]
    for s in splitters:
        for t in txt:
            tokens.extend(t.split(s))
        txt = tokens
        tokens = []
    return txt

def find_refs(txt):
    tokens = [tok for tok in split_any(txt, ' ,;\t\r\n') if tok.startswith('#')]
    return [front_number(tok[1:]) for tok in tokens]
    
from collections import defaultdict
issue_relations = defaultdict(list)

nodes = set()

for issue in data:
    #refs = issue['body'].split('#')[1::2]
    
    #refs = [front_number(r) for r in refs if front_number(r) is not None]
    refs = find_refs(issue['body'])
    print(issue['number'], ':', refs)
    issue_relations[issue['number']].extend(refs)
    nodes.add(issue['number'])
    for r in refs:
        nodes.add(r)
        issue_relations[r].append(issue['number'])
    

# Find issue labels
issue_labels = {}
for d in data:
    labels = [l['name'] for l in d['labels']]
    #print(d['number'], labels)
    issue_labels[d['number']] = labels

import networkx as nx
import matplotlib.pyplot as plt

relations = nx.Graph()

for k in issue_relations:
    relations.add_node(k)
    for r in issue_relations[k]:
        relations.add_edge(k, r)
        relations.add_edge(r, k)

#nx.draw_networkx(relations)
        
pos = nx.spring_layout(relations)
nx.draw_networkx_nodes(relations, pos,
        nodelist = [n for n in issue_labels if 'Alpha Release Requirement' in issue_labels[n]],
        node_color="tab:red")
nx.draw_networkx_nodes(relations, pos,
        nodelist = [n for n in issue_labels if 'Alpha Release Requirement' not in issue_labels[n]],
        node_color="tab:blue")
nx.draw_networkx_edges(relations, pos,
        edgelist = relations.edges()
        )
nx.draw_networkx_labels(relations, pos, {i: str(i) for i in relations.nodes()})
plt.show()
