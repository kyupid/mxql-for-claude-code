#!/usr/bin/env python3
"""
MXQL Category Finder

Helps find and recommend appropriate MXQL categories based on user intent.
Used by the MXQL skill to suggest categories when generating queries.

Usage:
    from category_finder import CategoryFinder

    finder = CategoryFinder()

    # Search by keyword
    categories = finder.search("postgresql")

    # Get category info
    info = finder.get_category_info("db_postgresql_counter")

    # Find by product type
    categories = finder.find_by_product("database")
"""

import json
import os
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class CategoryFinder:
    """Find and recommend MXQL categories based on user intent."""

    def __init__(self, categories_dir: Optional[str] = None):
        """
        Initialize the category finder.

        Args:
            categories_dir: Path to the categories directory.
                          If None, uses the directory relative to this script.
        """
        if categories_dir is None:
            script_dir = Path(__file__).parent
            categories_dir = script_dir / "categories"

        self.categories_dir = Path(categories_dir)
        self.index_path = self.categories_dir / "category-index.json"
        self.index = self._load_or_build_index()

    def _load_or_build_index(self) -> Dict:
        """Load index from file or build it if it doesn't exist."""
        if self.index_path.exists():
            with open(self.index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return self._build_index()

    def _build_index(self) -> Dict:
        """Build index from all meta files in the categories directory."""
        index = {
            "categories": {},
            "products": {},
            "keywords": {}
        }

        if not self.categories_dir.exists():
            return index

        for meta_file in self.categories_dir.glob("*.meta"):
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                category_name = data.get("categoryName", "")
                if not category_name:
                    continue

                # Extract language from filename
                lang = "en"  # default
                if meta_file.stem.endswith("_ko"):
                    lang = "ko"
                elif meta_file.stem.endswith("_ja"):
                    lang = "ja"

                # Store category info
                if category_name not in index["categories"]:
                    index["categories"][category_name] = {
                        "title": data.get("title", ""),
                        "interval": data.get("interval", ""),
                        "pk": data.get("pk", []),
                        "platforms": data.get("platforms", []),
                        "languages": {},
                        "tags": [],
                        "fields": []
                    }

                # Add language-specific file
                index["categories"][category_name]["languages"][lang] = meta_file.name

                # Store tags and fields (from English version for consistency)
                if lang == "en":
                    index["categories"][category_name]["tags"] = [
                        tag.get("tagName", "") for tag in data.get("tags", [])
                    ]
                    index["categories"][category_name]["fields"] = [
                        field.get("fieldName", "") for field in data.get("fields", [])
                    ]

                # Index by product type
                product_type = self._extract_product_type(category_name)
                if product_type not in index["products"]:
                    index["products"][product_type] = []
                if category_name not in index["products"][product_type]:
                    index["products"][product_type].append(category_name)

                # Index keywords
                keywords = self._extract_keywords(category_name, data)
                for keyword in keywords:
                    if keyword not in index["keywords"]:
                        index["keywords"][keyword] = []
                    if category_name not in index["keywords"][keyword]:
                        index["keywords"][keyword].append(category_name)

            except Exception as e:
                print(f"Error processing {meta_file}: {e}")
                continue

        # Save index
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        return index

    def _extract_product_type(self, category_name: str) -> str:
        """Extract product type from category name (e.g., 'db', 'app', 'server')."""
        parts = category_name.split("_")
        return parts[0] if parts else "unknown"

    def _extract_keywords(self, category_name: str, data: Dict) -> List[str]:
        """Extract searchable keywords from category data."""
        keywords = set()

        # Add category name parts
        keywords.update(category_name.lower().split("_"))

        # Add title words
        title = data.get("title", "")
        keywords.update(re.findall(r'\w+', title.lower()))

        # Add platforms
        for platform in data.get("platforms", []):
            keywords.add(platform.lower())

        return list(keywords)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for categories matching the query.

        Args:
            query: Search query (e.g., "postgresql", "cpu", "kubernetes")
            limit: Maximum number of results to return

        Returns:
            List of matching categories with relevance scores
        """
        query = query.lower().strip()
        results = {}

        # Search in keywords
        for keyword, categories in self.index.get("keywords", {}).items():
            if query in keyword or keyword in query:
                score = 2.0 if keyword == query else 1.0
                for cat in categories:
                    results[cat] = results.get(cat, 0) + score

        # Search in category names
        for cat_name in self.index.get("categories", {}).keys():
            if query in cat_name.lower():
                score = 3.0 if cat_name.lower() == query else 2.0
                results[cat_name] = results.get(cat_name, 0) + score

        # Sort by relevance
        sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

        # Format results
        formatted = []
        for cat_name, score in sorted_results[:limit]:
            cat_info = self.index["categories"].get(cat_name, {})
            formatted.append({
                "categoryName": cat_name,
                "title": cat_info.get("title", ""),
                "platforms": cat_info.get("platforms", []),
                "relevance": score,
                "languages": list(cat_info.get("languages", {}).keys())
            })

        return formatted

    def find_by_product(self, product_type: str) -> List[str]:
        """
        Find all categories for a specific product type.

        Args:
            product_type: Product type (e.g., 'db', 'app', 'server', 'kube', 'aws')

        Returns:
            List of category names
        """
        return self.index.get("products", {}).get(product_type.lower(), [])

    def get_category_info(self, category_name: str, language: str = "en") -> Optional[Dict]:
        """
        Get detailed information about a specific category.

        Args:
            category_name: Name of the category
            language: Preferred language ('en', 'ko', 'ja')

        Returns:
            Category metadata or None if not found
        """
        cat_info = self.index.get("categories", {}).get(category_name)
        if not cat_info:
            return None

        # Get the meta file for the requested language
        languages = cat_info.get("languages", {})
        meta_file = languages.get(language) or languages.get("en")

        if not meta_file:
            return cat_info

        # Load full metadata from file
        meta_path = self.categories_dir / meta_file
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                return json.load(f)

        return cat_info

    def list_all_products(self) -> List[str]:
        """Get a list of all product types."""
        return sorted(self.index.get("products", {}).keys())

    def recommend(self, intent: str, context: Optional[Dict] = None) -> List[Dict]:
        """
        Recommend categories based on user intent and context.

        Args:
            intent: User's intent (e.g., "monitor CPU usage", "track database queries")
            context: Optional context with keys like 'product', 'metric_type', etc.

        Returns:
            List of recommended categories with explanations
        """
        recommendations = []

        # Parse intent for keywords
        intent_lower = intent.lower()

        # Determine product type
        product_keywords = {
            'db': ['database', 'db', 'sql', 'mysql', 'postgresql', 'oracle', 'mongodb', 'redis'],
            'app': ['application', 'app', 'service', 'api', 'transaction', 'apm'],
            'server': ['server', 'host', 'cpu', 'memory', 'disk', 'network', 'infrastructure'],
            'kube': ['kubernetes', 'k8s', 'pod', 'container', 'deployment'],
            'aws': ['aws', 'amazon', 'ec2', 's3', 'rds', 'lambda'],
            'azure': ['azure', 'microsoft'],
            'rum': ['browser', 'frontend', 'rum', 'pageload']
        }

        # Find matching product types
        matched_products = []
        for product, keywords in product_keywords.items():
            if any(kw in intent_lower for kw in keywords):
                matched_products.append(product)

        # If no specific product found, search broadly
        if not matched_products:
            return self.search(intent, limit=5)

        # Get categories for matched products
        for product in matched_products:
            categories = self.find_by_product(product)

            # Further filter by intent keywords
            for cat in categories:
                if any(word in cat.lower() for word in intent_lower.split()):
                    cat_info = self.index["categories"].get(cat, {})
                    recommendations.append({
                        "categoryName": cat,
                        "title": cat_info.get("title", ""),
                        "platforms": cat_info.get("platforms", []),
                        "reason": f"Matches {product} monitoring for: {intent}",
                        "languages": list(cat_info.get("languages", {}).keys())
                    })

        return recommendations[:5]


def format_category_list(categories: List[Dict], include_details: bool = False) -> str:
    """Format a list of categories for display."""
    if not categories:
        return "No categories found."

    output = []
    for i, cat in enumerate(categories, 1):
        name = cat.get("categoryName", "")
        title = cat.get("title", "")
        platforms = cat.get("platforms", [])

        line = f"{i}. **{name}**"
        if title:
            line += f" - {title}"
        if platforms and include_details:
            line += f" (Platforms: {', '.join(platforms)})"

        output.append(line)

    return "\n".join(output)


# Command-line interface
if __name__ == "__main__":
    import sys

    finder = CategoryFinder()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python category_finder.py search <query>")
        print("  python category_finder.py product <product_type>")
        print("  python category_finder.py info <category_name>")
        print("  python category_finder.py products")
        print("  python category_finder.py recommend '<intent>'")
        sys.exit(1)

    command = sys.argv[1]

    if command == "search" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        results = finder.search(query)
        print(format_category_list(results, include_details=True))

    elif command == "product" and len(sys.argv) > 2:
        product = sys.argv[2]
        categories = finder.find_by_product(product)
        print(f"Categories for product '{product}':")
        for cat in categories:
            print(f"  - {cat}")

    elif command == "info" and len(sys.argv) > 2:
        category = sys.argv[2]
        info = finder.get_category_info(category)
        if info:
            print(json.dumps(info, indent=2, ensure_ascii=False))
        else:
            print(f"Category '{category}' not found.")

    elif command == "products":
        products = finder.list_all_products()
        print("Available product types:")
        for prod in products:
            count = len(finder.find_by_product(prod))
            print(f"  - {prod}: {count} categories")

    elif command == "recommend" and len(sys.argv) > 2:
        intent = " ".join(sys.argv[2:])
        recommendations = finder.recommend(intent)
        print(f"Recommendations for: '{intent}'")
        print(format_category_list(recommendations, include_details=True))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
