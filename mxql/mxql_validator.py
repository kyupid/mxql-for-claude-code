#!/usr/bin/env python3
"""
MXQL Query Validator
Validates MXQL queries using regex patterns without requiring Java runtime.
"""

import re
import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    severity: Severity
    line: int
    message: str
    suggestion: Optional[str] = None


class MXQLValidator:
    """MXQL Query Validator using regex patterns"""

    # MXQL command patterns
    COMMANDS = {
        'CATEGORY': r'^CATEGORY\s+\{.*\}',
        'TAGLOAD': r'^TAGLOAD\s*$',
        'FLEX-LOAD': r'^FLEX-LOAD\s+\{.*\}',
        'OID': r'^OID\s+\[.*\]',
        'SELECT': r'^SELECT\s+\[.*\]',
        'FILTER': r'^FILTER\s+\{.*\}',
        'GROUP': r'^GROUP\s+\{.*\}',
        'UPDATE': r'^UPDATE\s+\{.*\}',
        'ORDER': r'^ORDER\s+\{.*\}',
        'LIMIT': r'^LIMIT\s+\d+',
        'CREATE': r'^CREATE\s+\{.*\}',
        'DELETE': r'^DELETE\s+\[.*\]',
        'RENAME': r'^RENAME\s+\{.*\}',
        'FORMAT': r'^FORMAT\s+\{.*\}',
        'UNFOLD': r'^UNFOLD\s+\[.*\]',
        'JOIN': r'^JOIN\s+\{.*\}',
        'APPEND': r'^APPEND\s+\{.*\}',
        'SUB': r'^SUB\s+\{.*\}',
        'END': r'^END\s*$',
        'ADDROW': r'^ADDROW\s+\{.*\}',
        'TIMEADD': r'^TIMEADD\s+\{.*\}',
        'TIMEPAST': r'^TIMEPAST\s+\w+',
        'HvText': r'^HvText\s+\{.*\}',
    }

    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.lines: List[str] = []
        self.commands: List[Tuple[int, str, str]] = []  # (line_num, command_name, full_line)

    def validate(self, query: str) -> Tuple[bool, List[ValidationIssue]]:
        """
        Validate MXQL query and return success status and issues list.

        Returns:
            (is_valid, issues)
        """
        self.issues = []
        self.lines = query.strip().split('\n')
        self.commands = []

        # Parse and identify commands
        self._parse_commands()

        # Run validation checks
        self._check_syntax()
        self._check_semantics()
        self._check_best_practices()

        # Check if there are any critical issues
        has_critical = any(issue.severity == Severity.CRITICAL for issue in self.issues)

        return (not has_critical, self.issues)

    def _parse_commands(self):
        """Parse query and identify all commands"""
        for i, line in enumerate(self.lines, 1):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#') or line.startswith('//') or line.startswith('--'):
                continue

            # Skip multi-line comments
            if line.startswith('/*'):
                continue

            # Identify command
            for cmd_name, pattern in self.COMMANDS.items():
                if re.match(pattern, line, re.IGNORECASE):
                    self.commands.append((i, cmd_name, line))
                    break

    def _check_syntax(self):
        """Check syntax errors"""
        for line_num, line in enumerate(self.lines, 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue

            # Check bracket balance
            self._check_bracket_balance(line_num, line)

            # Check JSON structure in commands with braces
            if '{' in line:
                self._check_json_structure(line_num, line)

    def _check_bracket_balance(self, line_num: int, line: str):
        """Check if brackets and braces are balanced"""
        stack = []
        pairs = {'[': ']', '{': '}', '(': ')'}
        closing = {']', '}', ')'}

        in_string = False
        escape = False

        for char in line:
            if escape:
                escape = False
                continue

            if char == '\\':
                escape = True
                continue

            if char in ('"', "'"):
                in_string = not in_string
                continue

            if in_string:
                continue

            if char in pairs:
                stack.append(char)
            elif char in closing:
                if not stack:
                    self.issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        line=line_num,
                        message=f"Unmatched closing bracket '{char}'",
                        suggestion="Remove extra closing bracket or add opening bracket"
                    ))
                    return
                expected = pairs[stack.pop()]
                if char != expected:
                    self.issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        line=line_num,
                        message=f"Mismatched brackets: expected '{expected}' but found '{char}'",
                        suggestion=f"Change '{char}' to '{expected}'"
                    ))
                    return

        if stack:
            self.issues.append(ValidationIssue(
                severity=Severity.CRITICAL,
                line=line_num,
                message=f"Unclosed bracket '{stack[-1]}'",
                suggestion=f"Add closing bracket '{pairs[stack[-1]]}'"
            ))

    def _check_json_structure(self, line_num: int, line: str):
        """Check JSON structure in command parameters"""
        # Extract JSON part (between braces)
        match = re.search(r'\{.*\}', line)
        if not match:
            return

        json_str = match.group(0)

        # Check for unquoted field names (valid but not recommended)
        unquoted_fields = re.findall(r'\{\s*(\w+)\s*:', json_str)
        unquoted_fields += re.findall(r',\s*(\w+)\s*:', json_str)

        if unquoted_fields:
            self.issues.append(ValidationIssue(
                severity=Severity.INFO,
                line=line_num,
                message="Field names without quotes (valid but not recommended for readability)",
                suggestion=f"Consider using quotes: {', '.join(unquoted_fields)}"
            ))

    def _check_semantics(self):
        """Check semantic errors"""
        # Check for required commands
        self._check_required_commands()

        # Check command order
        self._check_command_order()

        # Check UPDATE requires GROUP
        self._check_update_requires_group()

        # Check SUB/END pairing
        self._check_sub_end_pairing()

        # Check GROUP syntax (key/value vs pk)
        self._check_group_syntax()

    def _check_required_commands(self):
        """Check if required commands are present"""
        command_names = [cmd[1] for cmd in self.commands]

        # Check for data loader
        data_loaders = {'TAGLOAD', 'FLEX-LOAD', 'ADDROW', 'APPEND'}
        has_loader = any(cmd in data_loaders for cmd in command_names)

        if not has_loader and 'SUB' not in command_names:
            self.issues.append(ValidationIssue(
                severity=Severity.CRITICAL,
                line=1,
                message="Missing data loader command (TAGLOAD, FLEX-LOAD, ADDROW, or APPEND)",
                suggestion="Add TAGLOAD after CATEGORY command"
            ))

    def _check_command_order(self):
        """Check if commands are in proper order"""
        prev_commands = []

        for line_num, cmd_name, full_line in self.commands:
            # CATEGORY should come before data loaders
            if cmd_name in ('TAGLOAD', 'FLEX-LOAD') and 'CATEGORY' not in prev_commands:
                # Check if CATEGORY is defined via parameter
                if not any('$category' in cmd[2] for cmd in self.commands):
                    self.issues.append(ValidationIssue(
                        severity=Severity.WARNING,
                        line=line_num,
                        message="Data loader before CATEGORY command",
                        suggestion="Move CATEGORY command before TAGLOAD/FLEX-LOAD"
                    ))

            prev_commands.append(cmd_name)

    def _check_update_requires_group(self):
        """Check if UPDATE comes after GROUP"""
        group_found = False

        for line_num, cmd_name, full_line in self.commands:
            if cmd_name == 'GROUP':
                group_found = True
            elif cmd_name == 'UPDATE':
                if not group_found:
                    self.issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        line=line_num,
                        message="UPDATE command without preceding GROUP",
                        suggestion="Add GROUP command before UPDATE"
                    ))

    def _check_sub_end_pairing(self):
        """Check if SUB and END are properly paired"""
        sub_count = sum(1 for _, cmd, _ in self.commands if cmd == 'SUB')
        end_count = sum(1 for _, cmd, _ in self.commands if cmd == 'END')

        if sub_count != end_count:
            self.issues.append(ValidationIssue(
                severity=Severity.CRITICAL,
                line=1,
                message=f"Mismatched SUB/END: {sub_count} SUB commands, {end_count} END commands",
                suggestion="Ensure each SUB has a matching END"
            ))

    def _check_best_practices(self):
        """Check for best practice violations"""
        # Check for late filtering
        self._check_filter_placement()

        # Check for SELECT *
        self._check_select_star()

        # Check for LIMIT without ORDER
        self._check_limit_without_order()

    def _check_filter_placement(self):
        """Check if FILTER is placed early"""
        filter_pos = None
        group_pos = None
        select_pos = None

        for i, (line_num, cmd_name, _) in enumerate(self.commands):
            if cmd_name == 'FILTER':
                if filter_pos is None:
                    filter_pos = i
            elif cmd_name == 'GROUP':
                if group_pos is None:
                    group_pos = i
            elif cmd_name == 'SELECT':
                if select_pos is None:
                    select_pos = i

        # Check if FILTER comes after GROUP
        if filter_pos is not None and group_pos is not None and filter_pos > group_pos:
            line_num = self.commands[filter_pos][0]
            self.issues.append(ValidationIssue(
                severity=Severity.WARNING,
                line=line_num,
                message="FILTER after GROUP - may impact performance",
                suggestion="Move FILTER before GROUP for better performance"
            ))

    def _check_select_star(self):
        """Check for SELECT *"""
        for line_num, cmd_name, full_line in self.commands:
            if cmd_name == 'SELECT' and '[*]' in full_line:
                self.issues.append(ValidationIssue(
                    severity=Severity.WARNING,
                    line=line_num,
                    message="SELECT [*] includes all fields - may impact performance",
                    suggestion="Select only needed fields explicitly"
                ))

    def _check_group_syntax(self):
        """Check for incorrect GROUP syntax (using key/value instead of pk)"""
        import re
        for line_num, cmd_name, full_line in self.commands:
            if cmd_name == 'GROUP':
                # Check if GROUP uses 'key' parameter (should use 'pk' instead)
                if re.search(r'\bkey\s*:', full_line):
                    self.issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        line=line_num,
                        message="GROUP uses 'key' parameter - should use 'pk' instead",
                        suggestion="Use GROUP {pk: \"field\"} or GROUP {timeunit: \"5m\", pk: \"field\"}"
                    ))
                # Check if GROUP uses 'value' parameter (wrong - this is for UPDATE)
                if re.search(r'\bvalue\s*:', full_line):
                    self.issues.append(ValidationIssue(
                        severity=Severity.CRITICAL,
                        line=line_num,
                        message="GROUP uses 'value' parameter - this is UPDATE syntax, not GROUP",
                        suggestion="GROUP uses special keywords (pk, timeunit, first, last, merge, etc.), not key-value pairs"
                    ))

    def _check_limit_without_order(self):
        """Check if LIMIT is used without ORDER"""
        has_order = any(cmd[1] == 'ORDER' for cmd in self.commands)
        has_limit = any(cmd[1] == 'LIMIT' for cmd in self.commands)

        if has_limit and not has_order:
            limit_line = next(cmd[0] for cmd in self.commands if cmd[1] == 'LIMIT')
            self.issues.append(ValidationIssue(
                severity=Severity.INFO,
                line=limit_line,
                message="LIMIT without ORDER - results may be arbitrary",
                suggestion="Add ORDER command before LIMIT for predictable Top-N results"
            ))


def format_validation_result(is_valid: bool, issues: List[ValidationIssue]) -> str:
    """Format validation results as readable string"""
    if is_valid and not issues:
        return "✅ Query is valid!\n"

    result = []

    # Group by severity
    critical = [i for i in issues if i.severity == Severity.CRITICAL]
    warnings = [i for i in issues if i.severity == Severity.WARNING]
    info = [i for i in issues if i.severity == Severity.INFO]

    if critical:
        result.append("🔴 Critical Issues:")
        for issue in critical:
            result.append(f"  Line {issue.line}: {issue.message}")
            if issue.suggestion:
                result.append(f"    → {issue.suggestion}")
        result.append("")

    if warnings:
        result.append("🟡 Warnings:")
        for issue in warnings:
            result.append(f"  Line {issue.line}: {issue.message}")
            if issue.suggestion:
                result.append(f"    → {issue.suggestion}")
        result.append("")

    if info:
        result.append("🔵 Suggestions:")
        for issue in info:
            result.append(f"  Line {issue.line}: {issue.message}")
            if issue.suggestion:
                result.append(f"    → {issue.suggestion}")
        result.append("")

    summary = "✅ Query is valid" if is_valid else "❌ Query has critical issues"
    result.insert(0, f"{summary} ({len(critical)} critical, {len(warnings)} warnings, {len(info)} info)\n")

    return "\n".join(result)


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = sys.stdin.read()

    validator = MXQLValidator()
    is_valid, issues = validator.validate(query)
    print(format_validation_result(is_valid, issues))

    sys.exit(0 if is_valid else 1)
