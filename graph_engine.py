"""
Product Knowledge Graph — Graph Engine

Indexes the product relationship data and provides traversal, search, and analysis.

Architecture:
- graph_data.py = Product Relationship Layer (what relates to what)
- graph_engine.py = Product Knowledge Graph engine (walk the graph to answer questions)
"""

from collections import defaultdict
from typing import Optional

from graph_data import (
    PRODUCTS, RELATIONSHIPS, BRANDS, CATEGORY_TAXONOMY,
    Product, Relationship, RelationshipType, Brand,
)


class ProductKnowledgeGraph:
    """In-memory product knowledge graph with traversal capabilities."""

    def __init__(self):
        # Indexes
        self.products: dict[str, Product] = {}
        self.brands: dict[str, Brand] = {}
        self.adjacency: dict[str, list[Relationship]] = defaultdict(list)
        self.brand_products: dict[str, list[str]] = defaultdict(list)
        self.category_products: dict[str, list[str]] = defaultdict(list)
        self.subcategory_products: dict[str, list[str]] = defaultdict(list)
        self.taxonomy = CATEGORY_TAXONOMY

        self._load()

    def _load(self):
        """Index all products, brands, and relationships."""
        for p in PRODUCTS:
            self.products[p.id] = p
            self.brand_products[p.brand.lower()].append(p.id)
            self.category_products[p.category.lower()].append(p.id)
            self.subcategory_products[p.subcategory.lower()].append(p.id)

        for b in BRANDS:
            self.brands[b.name.lower()] = b

        # Bidirectional adjacency
        for r in RELATIONSHIPS:
            self.adjacency[r.source_id].append(r)
            self.adjacency[r.target_id].append(
                Relationship(r.target_id, r.source_id, r.rel_type, r.confidence, r.reasoning)
            )

    # ── Lookup ───────────────────────────────────────────────────────

    def get_product(self, product_id: str) -> Optional[Product]:
        return self.products.get(product_id)

    def search_products(self, query: str) -> list[Product]:
        """Fuzzy search across product names, brands, tags, features."""
        q = query.lower()
        results = []
        for p in self.products.values():
            searchable = f"{p.name} {p.brand} {p.category} {p.subcategory} {' '.join(p.tags)} {' '.join(p.features)}".lower()
            if q in searchable:
                results.append(p)
        return results

    # ── Relationships ────────────────────────────────────────────────

    def get_relationships(
        self, product_id: str, rel_type: Optional[RelationshipType] = None
    ) -> list[Relationship]:
        """Get all relationships for a product, optionally filtered by type."""
        rels = self.adjacency.get(product_id, [])
        if rel_type:
            rels = [r for r in rels if r.rel_type == rel_type]
        return sorted(rels, key=lambda r: r.confidence, reverse=True)

    def compare_products(self, id_a: str, id_b: str) -> dict:
        """Compare two products — find relationship and feature diff."""
        pa = self.products.get(id_a)
        pb = self.products.get(id_b)
        if not pa or not pb:
            return {"error": f"Product not found: {id_a if not pa else id_b}"}

        # Check direct relationship
        direct_rel = None
        for r in self.adjacency.get(id_a, []):
            if r.target_id == id_b:
                direct_rel = r
                break

        shared_features = set(pa.features) & set(pb.features)
        unique_a = set(pa.features) - set(pb.features)
        unique_b = set(pb.features) - set(pa.features)

        return {
            "product_a": {"id": pa.id, "name": pa.name, "brand": pa.brand, "price": pa.price},
            "product_b": {"id": pb.id, "name": pb.name, "brand": pb.brand, "price": pb.price},
            "relationship": {
                "type": direct_rel.rel_type.value if direct_rel else "none",
                "confidence": direct_rel.confidence if direct_rel else 0,
                "reasoning": direct_rel.reasoning if direct_rel else "No direct relationship found",
            },
            "price_difference": round(pb.price - pa.price, 2),
            "shared_features": list(shared_features),
            "unique_to_a": list(unique_a),
            "unique_to_b": list(unique_b),
            "same_category": pa.subcategory == pb.subcategory,
            "same_brand": pa.brand == pb.brand,
        }

    # ── Graph Traversal ──────────────────────────────────────────────

    def traverse(
        self,
        start_id: str,
        rel_type: Optional[RelationshipType] = None,
        max_depth: int = 2,
        min_confidence: float = 0.0,
    ) -> list[dict]:
        """BFS traversal from a starting product.

        Returns a list of nodes discovered with their depth and path.
        This is the core CKG operation — walking the product graph.
        """
        visited = set()
        queue = [(start_id, 0, [start_id])]
        results = []

        while queue:
            current_id, depth, path = queue.pop(0)

            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)

            product = self.products.get(current_id)
            if product and current_id != start_id:
                results.append({
                    "product_id": current_id,
                    "name": product.name,
                    "brand": product.brand,
                    "price": product.price,
                    "depth": depth,
                    "path": path,
                })

            if depth < max_depth:
                for r in self.adjacency.get(current_id, []):
                    if r.confidence >= min_confidence:
                        if rel_type is None or r.rel_type == rel_type:
                            if r.target_id not in visited:
                                queue.append((r.target_id, depth + 1, path + [r.target_id]))

        return results

    # ── Brand Operations ─────────────────────────────────────────────

    def get_brand_products(self, brand_name: str) -> list[Product]:
        """Get all products for a brand (including sub-brands)."""
        brand_key = brand_name.lower()
        product_ids = set(self.brand_products.get(brand_key, []))

        # Include sub-brands
        for b in self.brands.values():
            if b.parent_brand and b.parent_brand.lower() == brand_key:
                product_ids.update(self.brand_products.get(b.name.lower(), []))

        return [self.products[pid] for pid in product_ids if pid in self.products]

    def get_brand_hierarchy(self, brand_name: str) -> dict:
        """Get brand info including parent/sub-brand relationships."""
        brand_key = brand_name.lower()
        brand = self.brands.get(brand_key)
        if not brand:
            return {"error": f"Brand not found: {brand_name}"}

        sub_brands = [
            b.name for b in self.brands.values()
            if b.parent_brand and b.parent_brand.lower() == brand_key
        ]

        parent = brand.parent_brand
        siblings = []
        if parent:
            siblings = [
                b.name for b in self.brands.values()
                if b.parent_brand and b.parent_brand.lower() == parent.lower()
                and b.name.lower() != brand_key
            ]

        return {
            "brand": brand.name,
            "parent_brand": parent,
            "sub_brands": sub_brands,
            "sibling_brands": siblings,
            "categories": brand.categories,
            "product_count": len(self.get_brand_products(brand_name)),
        }

    # ── Analytics ────────────────────────────────────────────────────

    def find_substitutes(self, product_id: str, max_results: int = 5) -> list[dict]:
        """Find substitutable products sorted by confidence."""
        rels = self.get_relationships(product_id, RelationshipType.SUBSTITUTABLE)
        results = []
        for r in rels[:max_results]:
            target = self.products.get(r.target_id)
            if target:
                results.append({
                    "product": {"id": target.id, "name": target.name, "brand": target.brand, "price": target.price},
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                    "price_diff": round(target.price - self.products[product_id].price, 2),
                })
        return results

    def find_complementary(self, product_id: str, max_results: int = 5) -> list[dict]:
        """Find complementary products (buy-together candidates)."""
        rels = self.get_relationships(product_id, RelationshipType.COMPLEMENTARY)
        results = []
        for r in rels[:max_results]:
            target = self.products.get(r.target_id)
            if target:
                results.append({
                    "product": {"id": target.id, "name": target.name, "brand": target.brand, "price": target.price},
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                })
        return results

    def category_price_range(self, subcategory: str) -> dict:
        """Get price statistics for a subcategory."""
        pids = self.subcategory_products.get(subcategory.lower(), [])
        if not pids:
            return {"error": f"No products in subcategory: {subcategory}"}
        prices = [self.products[pid].price for pid in pids]
        return {
            "subcategory": subcategory,
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": round(sum(prices) / len(prices), 2),
            "product_count": len(prices),
        }

    def graph_stats(self) -> dict:
        """Summary statistics of the knowledge graph."""
        rel_counts = defaultdict(int)
        for rels in self.adjacency.values():
            for r in rels:
                rel_counts[r.rel_type.value] += 1
        # Each relationship is counted twice (bidirectional)
        for k in rel_counts:
            rel_counts[k] //= 2

        return {
            "total_products": len(self.products),
            "total_brands": len(self.brands),
            "total_relationships": sum(rel_counts.values()),
            "relationships_by_type": dict(rel_counts),
            "categories": list(self.taxonomy.keys()),
            "subcategories": [sub for subs in self.taxonomy.values() for sub in subs],
        }
