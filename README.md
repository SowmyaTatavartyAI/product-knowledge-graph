# Product Knowledge Graph — MCP Server

A personal MCP server that exposes a product knowledge graph as tools any LLM client can call. Built as a portfolio demonstration of the **Product Knowledge Graph architecture**: a product relationship layer defines how products relate, and a graph traversal engine answers commerce questions by walking those relationships.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   MCP Client     │     │    MCP Server     │     │   Graph Engine   │
│ (Claude Desktop, │────▶│   (server.py)     │────▶│ (graph_engine.py)│
│  Cursor, etc.)   │     │   FastMCP tools   │     │  BFS traversal   │
└─────────────────┘     └──────────────────┘     │  Search/Compare  │
                                                   └────────┬─────────┘
                                                            │
                                                   ┌────────▼─────────┐
                                                   │   Graph Data      │
                                                   │ (graph_data.py)   │
                                                   │  Products/Brands  │
                                                   │  Relationships    │
                                                   └──────────────────┘
```

**Design decisions mirror production systems:**
- **Single-writer ownership**: Data layer is read-only at runtime; the graph is built once and traversed many times
- **Relationship types**: Same, Variant, Complementary, Substitutable — the four relationship classes
- **Confidence scores**: Every relationship has a confidence score, enabling threshold-based filtering
- **Bidirectional edges**: If A→B exists, B→A is automatically indexed

## Setup

```bash
# 1. Clone or copy this directory to your machine
cd commerce-kg-mcp

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install "mcp[cli]"

# 4. Test it works
python -c "from graph_engine import CommerceKnowledgeGraph; g = CommerceKnowledgeGraph(); print(g.graph_stats())"
```

## Run

### stdio mode (for Claude Desktop)
```bash
python server.py
```

### HTTP mode (for remote clients)
```bash
python server.py --http 8000
```

### Test with MCP Inspector
```bash
mcp dev server.py
```

## Connect to Claude Desktop

Add this to your Claude Desktop config file:

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "commerce-kg": {
      "command": "python",
      "args": ["/FULL/PATH/TO/commerce-kg-mcp/server.py"],
      "env": {
        "PYTHONPATH": "/FULL/PATH/TO/commerce-kg-mcp"
      }
    }
  }
}
```

> Replace `/FULL/PATH/TO/` with the actual path on your machine.
> If using a venv, point `command` to the venv's Python: `/FULL/PATH/TO/commerce-kg-mcp/.venv/bin/python`

## Available Tools

| Tool | What it does |
|------|-------------|
| `search_products` | Search by name, brand, category, tag, or feature |
| `get_product_relationships` | Get all relationships for a product (filter by type) |
| `compare_products` | Side-by-side comparison with feature diff |
| `traverse_graph` | BFS walk from a product — discover connected items |
| `find_substitutes` | Find competing/alternative products |
| `find_complementary` | Find buy-together candidates |
| `get_brand_info` | Brand hierarchy — parents, sub-brands, categories |
| `get_brand_products` | All products under a brand umbrella |
| `get_category_prices` | Price stats for a subcategory |
| `graph_overview` | Summary stats of the entire graph |

## Example Queries

Once connected, ask Claude things like:

- "What products are in the knowledge graph?"
- "Find me substitutes for the iPhone 16 Pro"
- "What goes well with AirPods Pro?"
- "Compare the Nike Pegasus 41 and Adidas Ultraboost Light"
- "Walk the graph starting from CeraVe Moisturizing Cream — what's connected?"
- "Show me Apple's brand hierarchy and all their products"
- "What's the price range for running shoes?"

## Extending the Graph

Add products and relationships in `graph_data.py`:

```python
# Add a product
Product("phone-008", "OnePlus 13 256GB", "OnePlus", "Electronics", "Smartphones", 899.00,
        ["Snapdragon 8 Elite", "50MP camera", "5400mAh"],
        ["flagship", "5g", "android"])

# Add a relationship
Relationship("phone-008", "phone-004", RelationshipType.SUBSTITUTABLE, 0.85,
             "Both Android flagships with Snapdragon 8 Elite at similar price")
```

## Why This Exists

This is a portfolio-ready demonstration of:
1. **Knowledge graph design** for commerce — product relationship layer + traversal engine
2. **MCP server development** — making AI tools composable
3. **Product relationship modeling** — the four relationship types that power shopping intelligence
4. **Graph traversal** — BFS with confidence-weighted edges

Built by [Sowmya Tatavarty](https://www.linkedin.com/in/sowmyatatavarty/)
