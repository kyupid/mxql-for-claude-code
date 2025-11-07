#!/usr/bin/env python3
"""
MXQL Test Query Generator
Generates test queries with ADDROW for validating MXQL queries with sample data.
"""

import json
from typing import List, Dict, Any, Optional


class TestQueryGenerator:
    """Generate MXQL test queries with sample data using ADDROW"""

    def __init__(self):
        pass

    def generate_test_query(
        self,
        original_query: str,
        sample_data: List[Dict[str, Any]],
        test_description: Optional[str] = None
    ) -> str:
        """
        Generate a test query that prepends ADDROW data to the original query.

        Args:
            original_query: The MXQL query to test
            sample_data: List of sample data rows (dict format)
            test_description: Optional description of the test

        Returns:
            Complete test query with ADDROW + APPEND pattern
        """
        # Generate test query
        test_query_parts = []

        # Add header comment
        if test_description:
            test_query_parts.append(f"# Test: {test_description}")
        test_query_parts.append("# This query uses ADDROW to inject test data")
        test_query_parts.append("")

        # Generate SUB query with ADDROW
        test_query_parts.append("SUB {id: test_data}")

        for i, row in enumerate(sample_data):
            addrow_json = self._dict_to_json_inline(row)
            test_query_parts.append(f"ADDROW {addrow_json}")

        test_query_parts.append("END")
        test_query_parts.append("")

        # Add original query with APPEND at the beginning
        query_lines = original_query.strip().split('\n')

        # Find the position to insert APPEND (after CATEGORY and data loader)
        insert_pos = 0
        has_category = False
        has_loader = False

        for i, line in enumerate(query_lines):
            line_stripped = line.strip().upper()
            if line_stripped.startswith('CATEGORY'):
                has_category = True
            elif line_stripped.startswith(('TAGLOAD', 'FLEX-LOAD')):
                has_loader = True
                insert_pos = i + 1
                break

        # If no data loader found, insert after CATEGORY
        if not has_loader and has_category:
            for i, line in enumerate(query_lines):
                if line.strip().upper().startswith('CATEGORY'):
                    insert_pos = i + 1
                    break

        # Insert APPEND command
        query_lines.insert(insert_pos, "APPEND {query: test_data}")

        # Add modified query
        test_query_parts.extend(query_lines)

        return '\n'.join(test_query_parts)

    def generate_simple_test_example(self, original_query: str) -> str:
        """
        Generate a simple test example with generic sample data.

        This is useful when the user doesn't provide specific test data.
        """
        # Analyze query to determine what fields might be needed
        fields = self._extract_fields_from_query(original_query)

        # Generate sample data based on detected fields
        sample_data = self._generate_sample_data(fields)

        # Add explanation
        explanation = [
            "# ==========================================",
            "# MXQL Test Query Example",
            "# ==========================================",
            "#",
            "# This query demonstrates how to test your MXQL with sample data.",
            "# You can modify the ADDROW data to test different scenarios.",
            "#",
            "# How it works:",
            "# 1. SUB creates a subquery named 'test_data'",
            "# 2. ADDROW adds sample rows to the subquery",
            "# 3. APPEND merges the test data into your main query",
            "#",
            "# To test in your environment:",
            "# - Copy this entire query",
            "# - Adjust the ADDROW data to match your test cases",
            "# - Run in your MXQL executor",
            "#",
            ""
        ]

        test_query = self.generate_test_query(
            original_query,
            sample_data,
            "Sample data test"
        )

        return '\n'.join(explanation) + test_query

    def _dict_to_json_inline(self, data: Dict[str, Any]) -> str:
        """Convert dict to inline JSON format for ADDROW"""
        # Use compact JSON format
        return json.dumps(data, separators=(',', ':')).replace('"', "'")

    def _extract_fields_from_query(self, query: str) -> List[str]:
        """Extract field names mentioned in the query"""
        import re

        fields = set()

        # Find SELECT statements
        select_matches = re.finditer(r'SELECT\s+\[(.*?)\]', query, re.IGNORECASE)
        for match in select_matches:
            field_list = match.group(1)
            # Split by comma and clean
            for field in field_list.split(','):
                field = field.strip().strip("'\"")
                if field and field != '*':
                    # Handle function calls like cpu(xos)
                    if '(' in field:
                        fields.add(field)
                    else:
                        fields.add(field)

        # Find FILTER statements
        filter_matches = re.finditer(r'key:\s*["\']?(\w+)["\']?', query, re.IGNORECASE)
        for match in filter_matches:
            fields.add(match.group(1))

        # Find GROUP pk
        group_matches = re.finditer(r'pk:\s*["\']?(\w+)["\']?', query, re.IGNORECASE)
        for match in group_matches:
            fields.add(match.group(1))

        # Always include common fields
        common_fields = ['time', 'oid', 'oname']
        fields.update(common_fields)

        return sorted(list(fields))

    def _generate_sample_data(self, fields: List[str]) -> List[Dict[str, Any]]:
        """Generate sample data based on field names"""
        # Field value generators
        def get_sample_value(field_name: str, row_num: int) -> Any:
            field_lower = field_name.lower()

            # Time fields
            if 'time' in field_lower:
                return 1700000000000 + (row_num * 60000)  # Timestamp with 1 min intervals

            # ID fields
            if field_lower in ('oid', 'id'):
                return 1000 + row_num

            # Name fields
            if 'name' in field_lower:
                return f"instance-{row_num}"

            # CPU related
            if 'cpu' in field_lower:
                return 50 + (row_num * 10)

            # Memory related
            if 'mem' in field_lower or 'memory' in field_lower:
                return 60 + (row_num * 5)

            # Count fields
            if 'count' in field_lower:
                return 100 + (row_num * 10)

            # Percentage fields
            if 'pct' in field_lower or 'percent' in field_lower:
                return 70 + row_num

            # Query hash
            if 'query_hash' in field_lower:
                return f"{1000000000 + row_num}"

            # Execute count
            if 'execute' in field_lower:
                return 50 + (row_num * 5)

            # Default
            return f"value_{row_num}"

        # Generate 3 sample rows
        sample_data = []
        for i in range(3):
            row = {}
            for field in fields:
                row[field] = get_sample_value(field, i)
            sample_data.append(row)

        return sample_data

    def generate_test_guide(self, original_query: str) -> str:
        """Generate a comprehensive testing guide for the query"""
        guide = [
            "# ==========================================",
            "# MXQL Query Testing Guide",
            "# ==========================================",
            "",
            "## Your Original Query",
            "```mxql",
            original_query,
            "```",
            "",
            "## How to Test This Query",
            "",
            "### Option 1: Test with Sample Data (Recommended)",
            "",
            "Use the test query below with ADDROW to inject sample data:",
            "",
            "```mxql",
            self.generate_simple_test_example(original_query),
            "```",
            "",
            "### Option 2: Test with Real Data",
            "",
            "If you have access to a WhaTap environment:",
            "",
            "1. Ensure the CATEGORY exists in your environment",
            "2. Set appropriate time range (stime/etime)",
            "3. Use valid OID values from your agents",
            "4. Run the query through the MXQL executor",
            "",
            "### Customizing Test Data",
            "",
            "Modify the ADDROW lines to test different scenarios:",
            "",
            "```mxql",
            "# Example: Testing high CPU values",
            "ADDROW {time:1700000000000, oid:1001, oname:'server-1', cpu:95}",
            "ADDROW {time:1700000060000, oid:1001, oname:'server-1', cpu:98}",
            "",
            "# Example: Testing multiple instances",
            "ADDROW {time:1700000000000, oid:1001, oname:'server-1', cpu:50}",
            "ADDROW {time:1700000000000, oid:1002, oname:'server-2', cpu:75}",
            "ADDROW {time:1700000000000, oid:1003, oname:'server-3', cpu:30}",
            "```",
            "",
            "### Expected Results",
            "",
            "Based on your query, you should see:",
            "- Fields selected in your SELECT statement",
            "- Filtered results based on your FILTER conditions",
            "- Aggregated data if using GROUP/UPDATE",
            "- Sorted results if using ORDER",
            "",
            "### Troubleshooting",
            "",
            "If the query doesn't work:",
            "1. Check that all brackets {} [] are balanced",
            "2. Ensure UPDATE comes after GROUP (if used)",
            "3. Verify CATEGORY matches your data source",
            "4. Check field names match your data schema",
            "",
            "### Next Steps",
            "",
            "Once tested successfully:",
            "1. Replace ADDROW with actual data loaders (TAGLOAD, FLEX-LOAD)",
            "2. Remove the SUB/APPEND test scaffolding",
            "3. Add appropriate time range and OID filters",
            "4. Deploy to production environment",
            "",
        ]

        return '\n'.join(guide)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = sys.stdin.read()

    generator = TestQueryGenerator()
    print(generator.generate_test_guide(query))
