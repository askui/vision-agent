Can you create a set of integration tests under `tests/integration/agent` to test model routing given different configurations custom act, get, locate models implementing the abstract classes (use override decorator from typing_extensions)?

Pls. mock the other dependencies of `VisionAgent`, e.g., the tools simmilar to how it is done in @conftest.py

Pls. update the tests to the new implementation. Add and remove tests where you see fit. You can execute them using `pdm test "tests/unit/models/test_router.py"`.
