"""
Product Knowledge Graph — MCP Server

Exposes the Product Knowledge Graph as MCP tools.
Connect this to Claude Desktop, Cursor, or any MCP client
to query product relationships using natural language.

Usage:
    pip install "mcp[cli]"
    python server.py                 # stdio (for Claude Desktop)
    python server.py --http 8000     # HTTP (for remote clients)

Architecture:
    server.py  →  graph_engine.py (graph traversal)  →  graph_data.py (product relationships)
"""

import json
import sys
from dataclasses import asdict
from typing import Optional

from mcp.server.fastmcp import FastMCP

from graph_engine import ProductKnowledgeGraph
from graph_data import RelationshipType


# ── Initialize ───────────────────────────────────────────────────────

mcp = FastMCP("product_kg_mcp")
graph = ProductKnowledgeGraph()


# ── Helper ───────────────────────────────────────────────────────────

def _json(obj) -> str:
    """Serialize response to pretty JSON."""
    return json.dumps(obj, indent=2, default=str)


def _product_to_dict(p) -> dict:
    return {
        "id": p.id, "name": p.name, "brand": p.brand,
        "category": p.category, "subcategory": p.subcategory,
        "price": p.price, "features": p.features, "tags": p.tags,
    }


# ── Tools ────────────────────────────────────────────────────────────

@mcp.tool(
    name="search_products",
    annotations={
        "title": "Search Products",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def search_products(query: str) -> str:
    """Search the product knowledge graph by name, brand, category, tag, or feature.

    Examples: 'iPhone', 'running shoes', 'ANC headphones', 'skincare serum'

    Args:
        query: Search text — matches against product names, brands, categories, tags, and features.

    Returns:
        JSON list of matching products with full details.
    """
    results = graph.search_products(query)
    if not results:
        return _json({"message": f"No products found for '{query}'", "suggestion": "Try broader terms like 'phone', 'shoes', or a brand name"})
    return _json([_product_to_dict(p) for p in results])


@mcp.tool(
    name="get_product_relationships",
    annotations={
        "title": "Get Product Relationships",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_product_relationships(
    product_id: str,
    relationship_type: Optional[str] = None,
) -> str:
    """Get all relationships for a product from the Brand Product Graph.

    Returns variants, substitutes, and complementary products with
    confidence scores and reasoning for each relationship.

    Args:
        product_id: Product ID (e.g., 'phone-001'). Use search_products to find IDs.
        relationship_type: Optional filter — one of 'same', 'variant', 'substitutable', 'complementary'.

    Returns:
        JSON list of relationships with target product details, confidence, and reasoning.
    """
    product = graph.get_product(product_id)
    if not product:
        return _json({"error": f"Product '{product_id}' not found", "hint": "Use search_products to find valid product IDs"})

    rel_type = None
    if relationship_type:
        try:
            rel_type = RelationshipType(relationship_type.lower())
        except ValueError:
            return _json({"error": f"Invalid relationship type: '{relationship_type}'", "valid_types": [r.value for r in RelationshipType]})

    rels = graph.get_relationships(product_id, rel_type)
    results = []
    for r in rels:
        target = graph.get_product(r.target_id)
        results.append({
            "target": _product_to_dict(target) if target else {"id": r.target_id},
            "relationship_type": r.rel_type.value,
            "confidence": r.confidence,
            "reasoning": r.reasoning,
        })

    return _json({
        "source_product": _product_to_dict(product),
        "relationships": results,
        "total": len(results),
    })


@mcp.tool(
    name="compare_products",
    annotations={
        "title": "Compare Two Products",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def compare_products(product_id_a: str, product_id_b: str) -> str:
    """Compare two products side-by-side.

    Returns their relationship type, price difference, shared and unique
    features, and whether they're in the same category/brand.

    Args:
        product_id_a: First product ID.
        product_id_b: Second product ID.

    Returns:
        JSON comparison with relationship, features diff, and price analysis.
    """
    result = graph.compare_products(product_id_a, product_id_b)
    return _json(result)


@mcp.tool(
    name="traverse_graph",
    annotations={
        "title": "Traverse Product Graph",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def traverse_graph(
    start_product_id: str,
    relationship_type: Optional[str] = None,
    max_depth: int = 2,
    min_confidence: float = 0.0,
) -> str:
    """Walk the knowledge graph from a starting product using BFS.

    Discovers connected products through relationship chains.
    Great for exploring product ecosystems and finding non-obvious connections.

    Args:
        start_product_id: Product ID to start traversal from.
        relationship_type: Optional — only follow edges of this type ('variant', 'substitutable', 'complementary').
        max_depth: How many hops to traverse (1-4, default 2).
        min_confidence: Minimum relationship confidence to follow (0.0-1.0).

    Returns:
        JSON list of discovered products with depth, path, and details.
    """
    product = graph.get_product(start_product_id)
    if not product:
        return _json({"error": f"Product '{start_product_id}' not found"})

    rel_type = None
    if relationship_type:
        try:
            rel_type = RelationshipType(relationship_type.lower())
        except ValueError:
            return _json({"error": f"Invalid relationship type: '{relationship_type}'"})

    max_depth = min(max(max_depth, 1), 4)  # Clamp to 1-4

    results = graph.traverse(start_product_id, rel_type, max_depth, min_confidence)
    return _json({
        "start_product": _product_to_dict(product),
        "discovered_products": results,
        "total_discovered": len(results),
        "max_depth_used": max_depth,
        "filter": {"relationship_type": relationship_type, "min_confidence": min_confidence},
    })


@mcp.tool(
    name="find_substitutes",
    annotations={
        "title": "Find Substitutable Products",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def find_substitutes(product_id: str, max_results: int = 5) -> str:
    """Find products that can substitute for a given product.

    Returns competing/alternative products ranked by confidence,
    with price comparison and reasoning.

    Args:
        product_id: Product ID to find substitutes for.
        max_results: Maximum substitutes to return (1-10, default 5).

    Returns:
        JSON list of substitute products with confidence, reasoning, and price diff.
    """
    product = graph.get_product(product_id)
    if not product:
        return _json({"error": f"Product '{product_id}' not found"})

    max_results = min(max(max_results, 1), 10)
    results = graph.find_substitutes(product_id, max_results)
    return _json({
        "source_product": _product_to_dict(product),
        "substitutes": results,
        "total": len(results),
    })


@mcp.tool(
    name="find_complementary",
    annotations={
        "title": "Find Complementary Products",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def find_complementary(product_id: str, max_results: int = 5) -> str:
    """Find products that complement a given product (buy-together candidates).

    Returns products frequently paired with the input, ranked by confidence.

    Args:
        product_id: Product ID to find complements for.
        max_results: Maximum complements to return (1-10, default 5).

    Returns:
        JSON list of complementary products with confidence and reasoning.
    """
    product = graph.get_product(product_id)
    if not product:
        return _json({"error": f"Product '{product_id}' not found"})

    max_results = min(max(max_results, 1), 10)
    results = graph.find_complementary(product_id, max_results)
    return _json({
        "source_product": _product_to_dict(product),
        "complementary_products": results,
        "total": len(results),
    })


@mcp.tool(
    name="get_brand_info",
    annotations={
        "title": "Get Brand Information",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_brand_info(brand_name: str) -> str:
    """Get brand hierarchy information — parent brands, sub-brands, categories, and product count.

    Args:
        brand_name: Brand name (e.g., 'Apple', 'Google', 'Nike', 'The Ordinary').

    Returns:
        JSON with brand hierarchy, categories, and product count.
    """
    hierarchy = graph.get_brand_hierarchy(brand_name)
    if "error" in hierarchy:
        available = [b.name for b in graph.brands.values()]
        hierarchy["available_brands"] = available
    return _json(hierarchy)


@mcp.tool(
    name="get_brand_products",
    annotations={
        "title": "Get Brand Products",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_brand_products(brand_name: str) -> str:
    """Get all products for a brand, including products from sub-brands.

    Args:
        brand_name: Brand name (e.g., 'Apple', 'Samsung', 'Nike').

    Returns:
        JSON list of all products under the brand umbrella.
    """
    products = graph.get_brand_products(brand_name)
    if not products:
        available = [b.name for b in graph.brands.values()]
        return _json({"error": f"No products found for brand '{brand_name}'", "available_brands": available})
    return _json({
        "brand": brand_name,
        "products": [_product_to_dict(p) for p in products],
        "total": len(products),
    })


@mcp.tool(
    name="get_category_prices",
    annotations={
        "title": "Get Category Price Range",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_category_prices(subcategory: str) -> str:
    """Get price statistics for a product subcategory.

    Args:
        subcategory: Subcategory name (e.g., 'Smartphones', 'Running Shoes', 'Skincare').

    Returns:
        JSON with min, max, average price and product count.
    """
    result = graph.category_price_range(subcategory)
    return _json(result)


@mcp.tool(
    name="graph_overview",
    annotations={
        "title": "Knowledge Graph Overview",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def graph_overview() -> str:
    """Get summary statistics of the entire commerce knowledge graph.

    Returns product count, brand count, relationship counts by type,
    and available categories/subcategories.

    Returns:
        JSON summary of graph contents and structure.
    """
    return _json(graph.graph_stats())


# ── Entry Point ──────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--http" in sys.argv:
        idx = sys.argv.index("--http")
        port = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 8000
        mcp.run(transport="streamable-http", port=port)
    else:
        mcp.run()  # Default: stdio for Claude Desktop
