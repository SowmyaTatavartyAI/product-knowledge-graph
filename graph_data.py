"""
Product Knowledge Graph — Product Relationship Layer

Models a product knowledge graph with:
- Products with attributes (brand, category, price, features)
- Relationships: Same, Variant, Complementary, Substitutable
- Brand hierarchies (parent brand → sub-brands → products)
- Category taxonomy

Architecture:
- graph_data.py = Product Relationship Layer (what relates to what, and how)
- graph_engine.py = Product Knowledge Graph engine (walk the graph to answer questions)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RelationshipType(str, Enum):
    """How two products relate — the core BPG relationship types."""
    SAME = "same"                    # Identical product, different listing
    VARIANT = "variant"              # Same product line, different spec (color, size, storage)
    COMPLEMENTARY = "complementary"  # Frequently bought together / enhances the other
    SUBSTITUTABLE = "substitutable"  # Competing product, similar use case


@dataclass
class Product:
    id: str
    name: str
    brand: str
    category: str
    subcategory: str
    price: float
    features: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class Relationship:
    source_id: str
    target_id: str
    rel_type: RelationshipType
    confidence: float  # 0.0 - 1.0
    reasoning: str     # Why this relationship exists


@dataclass
class Brand:
    name: str
    parent_brand: Optional[str]  # e.g., "Pixel" -> "Google"
    categories: list[str] = field(default_factory=list)


# ── Category Taxonomy ────────────────────────────────────────────────
CATEGORY_TAXONOMY = {
    "Electronics": ["Smartphones", "Laptops", "Headphones", "Smartwatches", "Tablets"],
    "Fashion": ["Sneakers", "Running Shoes", "Casual Wear", "Activewear"],
    "Beauty": ["Skincare", "Haircare", "Fragrance"],
}

# ── Brands ───────────────────────────────────────────────────────────
BRANDS = [
    Brand("Apple", None, ["Smartphones", "Laptops", "Headphones", "Smartwatches", "Tablets"]),
    Brand("Samsung", None, ["Smartphones", "Laptops", "Headphones", "Smartwatches", "Tablets"]),
    Brand("Google", None, ["Smartphones", "Headphones", "Smartwatches"]),
    Brand("Pixel", "Google", ["Smartphones"]),
    Brand("Galaxy", "Samsung", ["Smartphones", "Smartwatches", "Tablets"]),
    Brand("Sony", None, ["Headphones", "Smartphones"]),
    Brand("Nike", None, ["Sneakers", "Running Shoes", "Activewear"]),
    Brand("Adidas", None, ["Sneakers", "Running Shoes", "Activewear"]),
    Brand("New Balance", None, ["Sneakers", "Running Shoes"]),
    Brand("The Ordinary", None, ["Skincare"]),
    Brand("CeraVe", None, ["Skincare"]),
    Brand("Dyson", None, ["Haircare"]),
    Brand("Olaplex", None, ["Haircare"]),
]

# ── Products ─────────────────────────────────────────────────────────
PRODUCTS = [
    # === Smartphones ===
    Product("phone-001", "iPhone 16 Pro 256GB", "Apple", "Electronics", "Smartphones", 1099.00,
            ["A18 Pro chip", "48MP camera", "Titanium", "USB-C", "Action Button"],
            ["flagship", "premium", "5g"]),
    Product("phone-002", "iPhone 16 Pro 512GB", "Apple", "Electronics", "Smartphones", 1299.00,
            ["A18 Pro chip", "48MP camera", "Titanium", "USB-C", "Action Button"],
            ["flagship", "premium", "5g"]),
    Product("phone-003", "iPhone 16 128GB", "Apple", "Electronics", "Smartphones", 799.00,
            ["A18 chip", "48MP camera", "Aluminum", "USB-C", "Action Button"],
            ["mainstream", "5g"]),
    Product("phone-004", "Samsung Galaxy S25 Ultra 256GB", "Samsung", "Electronics", "Smartphones", 1299.00,
            ["Snapdragon 8 Elite", "200MP camera", "Titanium", "S Pen", "Galaxy AI"],
            ["flagship", "premium", "5g", "android"]),
    Product("phone-005", "Samsung Galaxy S25 256GB", "Samsung", "Electronics", "Smartphones", 799.00,
            ["Snapdragon 8 Elite", "50MP camera", "Armor Aluminum", "Galaxy AI"],
            ["mainstream", "5g", "android"]),
    Product("phone-006", "Google Pixel 9 Pro 256GB", "Google", "Electronics", "Smartphones", 999.00,
            ["Tensor G4", "50MP camera", "AI features", "7 years updates"],
            ["flagship", "5g", "android", "ai-first"]),
    Product("phone-007", "Google Pixel 9 128GB", "Google", "Electronics", "Smartphones", 699.00,
            ["Tensor G4", "50MP camera", "AI features", "7 years updates"],
            ["mainstream", "5g", "android", "ai-first"]),

    # === Headphones ===
    Product("audio-001", "AirPods Pro 2", "Apple", "Electronics", "Headphones", 249.00,
            ["ANC", "Transparency mode", "Spatial Audio", "USB-C", "Adaptive Audio"],
            ["wireless", "premium", "earbuds"]),
    Product("audio-002", "AirPods Max", "Apple", "Electronics", "Headphones", 549.00,
            ["ANC", "Spatial Audio", "Digital Crown", "Aluminum", "USB-C"],
            ["wireless", "premium", "over-ear"]),
    Product("audio-003", "Sony WH-1000XM5", "Sony", "Electronics", "Headphones", 348.00,
            ["ANC", "30hr battery", "Multipoint", "LDAC", "Speak-to-Chat"],
            ["wireless", "premium", "over-ear"]),
    Product("audio-004", "Samsung Galaxy Buds3 Pro", "Samsung", "Electronics", "Headphones", 249.00,
            ["ANC", "360 Audio", "Blade Lights", "IP57", "Galaxy AI"],
            ["wireless", "premium", "earbuds"]),

    # === Laptops ===
    Product("laptop-001", "MacBook Air M3 13-inch", "Apple", "Electronics", "Laptops", 1099.00,
            ["M3 chip", "8GB RAM", "256GB SSD", "Fanless", "18hr battery"],
            ["ultrabook", "mainstream"]),
    Product("laptop-002", "MacBook Pro 14-inch M3 Pro", "Apple", "Electronics", "Laptops", 1999.00,
            ["M3 Pro chip", "18GB RAM", "512GB SSD", "ProMotion", "HDMI"],
            ["workstation", "premium"]),
    Product("laptop-003", "Samsung Galaxy Book4 Ultra", "Samsung", "Electronics", "Laptops", 2399.00,
            ["Intel Core Ultra 9", "32GB RAM", "1TB SSD", "RTX 4070", "AMOLED"],
            ["workstation", "premium", "gaming"]),

    # === Sneakers / Running ===
    Product("shoe-001", "Nike Air Force 1 '07", "Nike", "Fashion", "Sneakers", 115.00,
            ["Leather upper", "Air-Sole unit", "Classic silhouette"],
            ["casual", "iconic", "unisex"]),
    Product("shoe-002", "Nike Dunk Low", "Nike", "Fashion", "Sneakers", 110.00,
            ["Leather upper", "Foam midsole", "Padded collar"],
            ["casual", "retro", "unisex"]),
    Product("shoe-003", "Adidas Samba OG", "Adidas", "Fashion", "Sneakers", 100.00,
            ["Leather upper", "Suede T-toe", "Gum sole"],
            ["casual", "retro", "unisex"]),
    Product("shoe-004", "New Balance 550", "New Balance", "Fashion", "Sneakers", 110.00,
            ["Leather upper", "Retro basketball", "ENCAP midsole"],
            ["casual", "retro", "unisex"]),
    Product("shoe-005", "Nike Pegasus 41", "Nike", "Fashion", "Running Shoes", 140.00,
            ["React foam", "Air Zoom", "Engineered mesh"],
            ["daily trainer", "neutral"]),
    Product("shoe-006", "Adidas Ultraboost Light", "Adidas", "Fashion", "Running Shoes", 190.00,
            ["Light BOOST", "Continental rubber", "Primeknit+"],
            ["daily trainer", "neutral"]),
    Product("shoe-007", "New Balance Fresh Foam X 1080v14", "New Balance", "Fashion", "Running Shoes", 165.00,
            ["Fresh Foam X", "Hypoknit upper", "Ortholite insole"],
            ["daily trainer", "neutral", "cushioned"]),

    # === Skincare ===
    Product("skin-001", "The Ordinary Niacinamide 10% + Zinc 1%", "The Ordinary", "Beauty", "Skincare", 5.90,
            ["Niacinamide", "Zinc PCA", "Oil control", "Pore reduction"],
            ["serum", "acne", "oily-skin"]),
    Product("skin-002", "The Ordinary Hyaluronic Acid 2% + B5", "The Ordinary", "Beauty", "Skincare", 7.90,
            ["Hyaluronic Acid", "Vitamin B5", "Hydration"],
            ["serum", "hydrating", "all-skin"]),
    Product("skin-003", "CeraVe Moisturizing Cream", "CeraVe", "Beauty", "Skincare", 18.99,
            ["Ceramides", "Hyaluronic Acid", "MVE Technology"],
            ["moisturizer", "barrier-repair", "sensitive-skin"]),
    Product("skin-004", "CeraVe Foaming Facial Cleanser", "CeraVe", "Beauty", "Skincare", 15.99,
            ["Ceramides", "Niacinamide", "Hyaluronic Acid"],
            ["cleanser", "oily-skin", "gentle"]),

    # === Haircare ===
    Product("hair-001", "Dyson Airwrap Multi-Styler", "Dyson", "Beauty", "Haircare", 599.99,
            ["Coanda airflow", "Multiple attachments", "Intelligent heat"],
            ["styling-tool", "premium"]),
    Product("hair-002", "Dyson Supersonic Hair Dryer", "Dyson", "Beauty", "Haircare", 429.99,
            ["V9 motor", "Intelligent heat control", "Magnetic attachments"],
            ["hair-dryer", "premium"]),
    Product("hair-003", "Olaplex No. 3 Hair Perfector", "Olaplex", "Beauty", "Haircare", 30.00,
            ["Bond-building", "Bis-aminopropyl diglycol dimaleate", "Pre-shampoo"],
            ["treatment", "repair", "color-safe"]),
    Product("hair-004", "Olaplex No. 4 Bond Maintenance Shampoo", "Olaplex", "Beauty", "Haircare", 30.00,
            ["Bond-building", "Sulfate-free", "Color-safe"],
            ["shampoo", "repair", "color-safe"]),
]

# ── Relationships (the Product Relationship Layer) ───────────────────
RELATIONSHIPS = [
    # Variants — same product line, different spec
    Relationship("phone-001", "phone-002", RelationshipType.VARIANT, 0.99,
                 "Same iPhone 16 Pro, different storage capacity (256GB vs 512GB)"),
    Relationship("phone-001", "phone-003", RelationshipType.VARIANT, 0.85,
                 "Same iPhone 16 generation — Pro vs standard tier"),
    Relationship("phone-004", "phone-005", RelationshipType.VARIANT, 0.85,
                 "Same Galaxy S25 generation — Ultra vs standard tier"),
    Relationship("phone-006", "phone-007", RelationshipType.VARIANT, 0.90,
                 "Same Pixel 9 generation — Pro vs standard"),
    Relationship("audio-001", "audio-002", RelationshipType.VARIANT, 0.70,
                 "Same Apple audio line — earbuds vs over-ear form factor"),
    Relationship("hair-003", "hair-004", RelationshipType.VARIANT, 0.80,
                 "Same Olaplex bond-building line — treatment vs shampoo step"),
    Relationship("skin-001", "skin-002", RelationshipType.VARIANT, 0.75,
                 "Same The Ordinary serum line — different active ingredients"),

    # Substitutable — competing products, same use case
    Relationship("phone-001", "phone-004", RelationshipType.SUBSTITUTABLE, 0.92,
                 "Both flagship smartphones in the same price tier with premium cameras"),
    Relationship("phone-001", "phone-006", RelationshipType.SUBSTITUTABLE, 0.88,
                 "Both flagship smartphones — Apple vs Google AI-first approach"),
    Relationship("phone-003", "phone-005", RelationshipType.SUBSTITUTABLE, 0.90,
                 "Both mainstream smartphones around $799"),
    Relationship("phone-003", "phone-007", RelationshipType.SUBSTITUTABLE, 0.88,
                 "Both mainstream smartphones — Apple vs Google"),
    Relationship("audio-001", "audio-004", RelationshipType.SUBSTITUTABLE, 0.93,
                 "Both premium ANC earbuds at $249 — AirPods Pro vs Galaxy Buds"),
    Relationship("audio-002", "audio-003", RelationshipType.SUBSTITUTABLE, 0.91,
                 "Both premium ANC over-ear headphones — Apple vs Sony"),
    Relationship("shoe-001", "shoe-003", RelationshipType.SUBSTITUTABLE, 0.85,
                 "Both iconic leather casual sneakers — AF1 vs Samba"),
    Relationship("shoe-001", "shoe-004", RelationshipType.SUBSTITUTABLE, 0.80,
                 "Both retro leather casual sneakers — AF1 vs NB 550"),
    Relationship("shoe-002", "shoe-003", RelationshipType.SUBSTITUTABLE, 0.87,
                 "Both retro casual sneakers trending in streetwear — Dunk vs Samba"),
    Relationship("shoe-005", "shoe-006", RelationshipType.SUBSTITUTABLE, 0.90,
                 "Both neutral daily training running shoes"),
    Relationship("shoe-005", "shoe-007", RelationshipType.SUBSTITUTABLE, 0.88,
                 "Both neutral daily trainers — Pegasus vs 1080"),
    Relationship("shoe-006", "shoe-007", RelationshipType.SUBSTITUTABLE, 0.85,
                 "Both premium cushioned daily trainers"),
    Relationship("skin-001", "skin-004", RelationshipType.SUBSTITUTABLE, 0.60,
                 "Both target oily/acne-prone skin — serum vs cleanser approach"),
    Relationship("hair-001", "hair-002", RelationshipType.SUBSTITUTABLE, 0.65,
                 "Both premium Dyson hair tools — styler vs dryer, overlapping use case"),

    # Complementary — bought together or enhances the other
    Relationship("phone-001", "audio-001", RelationshipType.COMPLEMENTARY, 0.95,
                 "AirPods Pro pairs natively with iPhone for seamless audio"),
    Relationship("phone-004", "audio-004", RelationshipType.COMPLEMENTARY, 0.93,
                 "Galaxy Buds pairs natively with Samsung phones"),
    Relationship("phone-001", "laptop-001", RelationshipType.COMPLEMENTARY, 0.80,
                 "Apple ecosystem — AirDrop, Continuity, shared iCloud"),
    Relationship("laptop-001", "laptop-002", RelationshipType.VARIANT, 0.75,
                 "Same MacBook line — Air vs Pro tier"),
    Relationship("skin-001", "skin-002", RelationshipType.COMPLEMENTARY, 0.85,
                 "Niacinamide for oil control + HA for hydration — common layering routine"),
    Relationship("skin-002", "skin-003", RelationshipType.COMPLEMENTARY, 0.90,
                 "HA serum for hydration followed by CeraVe cream to lock it in"),
    Relationship("skin-004", "skin-001", RelationshipType.COMPLEMENTARY, 0.80,
                 "CeraVe cleanser then The Ordinary niacinamide — classic acne routine"),
    Relationship("hair-003", "hair-004", RelationshipType.COMPLEMENTARY, 0.95,
                 "Olaplex No.3 treatment before No.4 shampoo — designed as a sequence"),
    Relationship("hair-001", "hair-003", RelationshipType.COMPLEMENTARY, 0.60,
                 "Olaplex repairs bonds before heat styling with Airwrap"),
    Relationship("shoe-005", "shoe-001", RelationshipType.COMPLEMENTARY, 0.50,
                 "Running shoe for workouts + AF1 for casual wear — different occasions"),

    # Same — identical product, different listing
    # (In production these catch duplicates across retailers)
]
