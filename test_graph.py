"""Quick smoke test for the graph engine."""
import json
from graph_engine import ProductKnowledgeGraph

g = ProductKnowledgeGraph()

print("=== Graph Stats ===")
print(json.dumps(g.graph_stats(), indent=2))

print("\n=== Search: iPhone ===")
for p in g.search_products("iPhone"):
    print(f"  {p.id}: {p.name} (${p.price})")

print("\n=== Substitutes for phone-001 (iPhone 16 Pro 256GB) ===")
for s in g.find_substitutes("phone-001"):
    print(f"  {s['product']['name']} - confidence: {s['confidence']}")

print("\n=== Complementary for phone-001 ===")
for c in g.find_complementary("phone-001"):
    print(f"  {c['product']['name']} - {c['reasoning']}")

print("\n=== Traverse from skin-003 (CeraVe Cream), depth=2 ===")
for node in g.traverse("skin-003", max_depth=2):
    path_str = " -> ".join(node["path"])
    print(f"  depth={node['depth']}: {node['name']} ({node['brand']}) -- path: {path_str}")

print("\n=== Compare iPhone 16 Pro vs Galaxy S25 Ultra ===")
comp = g.compare_products("phone-001", "phone-004")
print(json.dumps(comp, indent=2))

print("\n=== Brand Hierarchy: Google ===")
print(json.dumps(g.get_brand_hierarchy("Google"), indent=2))

print("\nAll tests passed!")
