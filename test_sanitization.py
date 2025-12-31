#!/usr/bin/env python3
"""Quick test script to verify path sanitization logic."""

from api.services.database import sanitize_path_component


def test_sanitization():
    """Run quick tests on sanitization function."""
    tests = [
        # (input, expected)
        ("simple", "simple"),
        ("test/project", "test_project"),
        ("test\\project", "test_project"),
        ("project:v1", "project_v1"),
        ("test*file", "test_file"),
        ("what?", "what_"),
        ('test"name"', "test_name_"),
        ("project<2024>", "project_2024_"),
        ("test|name", "test_name"),
        ("My Project: Episode 1/Part 2 <Draft>", "My_Project_Episode_1_Part_2_Draft_"),
        ("test___file", "test_file"),
        ("_test_", "test"),
        ("", "unnamed"),
        ("///", "unnamed"),
        ("My Project Name", "My Project Name"),
        ("file.name", "file.name"),
        ("University Place: Episode #123", "University_Place_Episode_123"),
    ]

    print("Testing sanitize_path_component()...")
    passed = 0
    failed = 0

    for input_str, expected in tests:
        result = sanitize_path_component(input_str)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1
        print(f"{status} '{input_str}' -> '{result}' (expected: '{expected}')")

    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = test_sanitization()
    exit(0 if success else 1)
