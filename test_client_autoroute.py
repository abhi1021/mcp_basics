from llm_gatewayV3.client import LLM
import pytest

def test_stream_accepts_auto_route():
    llm = LLM()
    # This should not raise a TypeError now
    try:
        # We don't actually need to run it against a live server to check the signature
        # but we can check if the method exists and accepts the argument
        gen = llm.stream("Hello", auto_route="perception")
        print("Success: LLM().stream() accepts auto_route")
    except TypeError as e:
        print(f"Failure: {e}")
        exit(1)

if __name__ == "__main__":
    test_stream_accepts_auto_route()
