"""
Test script to verify agent installation.

Checks:
1. All required modules exist and can be imported
2. Pydantic schemas are valid
3. State directory exists
4. Dependencies are installed

Run: uv run python test_installation.py
"""

import sys
from pathlib import Path


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        import schemas
        print("  ✓ schemas.py")
    except ImportError as e:
        print(f"  ✗ schemas.py: {e}")
        return False

    try:
        import memory
        print("  ✓ memory.py")
    except ImportError as e:
        print(f"  ✗ memory.py: {e}")
        return False

    try:
        import perception
        print("  ✓ perception.py")
    except ImportError as e:
        print(f"  ✗ perception.py: {e}")
        return False

    try:
        import decision
        print("  ✓ decision.py")
    except ImportError as e:
        print(f"  ✗ decision.py: {e}")
        return False

    try:
        import action
        print("  ✓ action.py")
    except ImportError as e:
        print(f"  ✗ action.py: {e}")
        return False

    try:
        import agent6
        print("  ✓ agent6.py")
    except ImportError as e:
        print(f"  ✗ agent6.py: {e}")
        return False

    return True


def test_schemas():
    """Test that Pydantic schemas are valid."""
    print("\nTesting Pydantic schemas...")

    try:
        from schemas import (
            Intent,
            IntentType,
            PerceptionInput,
            PerceptionOutput,
            MemoryInput,
            MemoryOutput,
            DecisionInput,
            DecisionOutput,
            ActionInput,
            ActionOutput,
            AgentState,
            AgentConfig,
        )

        # Test creating a basic intent
        intent = Intent(
            intent_type=IntentType.FACTUAL_QUERY,
            query="test query",
            entities={},
            requires_tools=[],
            confidence=0.9
        )
        print(f"  ✓ Intent schema valid: {intent.intent_type}")

        # Test config
        config = AgentConfig()
        print(f"  ✓ AgentConfig valid: max_iterations={config.max_iterations}")

        # Test state
        state = AgentState(
            session_id="test-123",
            user_message="test message"
        )
        print(f"  ✓ AgentState valid: iteration={state.iteration}")

        return True

    except Exception as e:
        print(f"  ✗ Schema validation failed: {e}")
        return False


def test_state_directory():
    """Test that state directory exists and is writable."""
    print("\nTesting state directory...")

    state_dir = Path("state")

    if not state_dir.exists():
        print(f"  ✗ state/ directory does not exist")
        return False

    print(f"  ✓ state/ directory exists")

    # Test write permissions
    test_file = state_dir / ".test_write"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print(f"  ✓ state/ directory is writable")
        return True
    except Exception as e:
        print(f"  ✗ state/ directory not writable: {e}")
        return False


def test_dependencies():
    """Test that required dependencies are installed."""
    print("\nTesting dependencies...")

    deps = [
        ("pydantic", "Pydantic v2"),
        ("httpx", "HTTP client"),
        ("dotenv", "Environment variables"),
        ("mcp", "MCP protocol"),
    ]

    all_ok = True
    for module_name, description in deps:
        try:
            __import__(module_name)
            print(f"  ✓ {description} ({module_name})")
        except ImportError:
            print(f"  ✗ {description} ({module_name}) not installed")
            all_ok = False

    return all_ok


def test_memory_manager():
    """Test that MemoryManager works."""
    print("\nTesting MemoryManager...")

    try:
        from memory import MemoryManager
        from schemas import MemoryType

        manager = MemoryManager(state_dir="state")
        print("  ✓ MemoryManager initialized")

        # Test storing a memory
        entry = manager.store_memory(
            content="Test memory",
            memory_type=MemoryType.FACT,
            session_id="test-session"
        )
        print(f"  ✓ Memory stored: {entry.memory_id}")

        # Test retrieving memories
        from schemas import MemoryQuery
        query = MemoryQuery(query="test", limit=5)
        results = manager.retrieve_memories(query)
        print(f"  ✓ Memory retrieval works: found {len(results)} memory(ies)")

        return True

    except Exception as e:
        print(f"  ✗ MemoryManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Agent Installation Test")
    print("="*60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Schemas", test_schemas()))
    results.append(("State Directory", test_state_directory()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("Memory Manager", test_memory_manager()))

    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("="*60)

    if all_passed:
        print("\n✓ All tests passed!")
        print("\nNext steps:")
        print("1. Configure .env with API keys (see .env.template)")
        print("2. Start LLM Gateway V3: cd llm_gatewayV3 && ./run.sh")
        print("3. Run agent: uv run python agent6.py 'your query'")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        print("\nTroubleshooting:")
        print("- Run: uv sync")
        print("- Ensure state/ directory exists: mkdir -p state")
        return 1


if __name__ == "__main__":
    sys.exit(main())
