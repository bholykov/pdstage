from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class PdObject:
    """Represents an object defined in a Pure Data patch."""

    index: int
    type: str
    args: List[str]


@dataclass
class PdConnection:
    """Represents a connection between two objects."""

    src_obj: int
    src_outlet: int
    dst_obj: int
    dst_inlet: int


class SourceGeneratorHarness:
    """A small structural harness for `patches/source-generator.pd`.

    The project does not bundle libpd, so this harness performs the minimum
    structural inspection necessary to exercise the selector routing logic.
    For each selector value (0-5) we build the mapping from the routed control
    inlet through to the corresponding subpatch and confirm that the
    `selector~` outlet is fed by that subpatch.
    """

    def __init__(self, patch_path: Path) -> None:
        self.patch_path = patch_path
        self.objects: List[PdObject] = []
        self.connections: List[PdConnection] = []
        self._parse_patch()

        self.route_index = self._find_unique_object("route")
        self.selector_index = self._find_unique_object("selector~")
        self.outlet_index = self._find_unique_object("outlet~")

        self.route_args = [int(arg) for arg in self.objects[self.route_index].args]
        self.value_to_outlet = {
            value: outlet for outlet, value in enumerate(self.route_args)
        }

        self.route_branches: Dict[int, int] = {}
        self.selector_signal_sources: Dict[int, int] = {}
        self.route_control_outlets: set[int] = set()
        self.selector_outlet_targets: List[int] = []

        for connection in self.connections:
            if connection.src_obj == self.route_index:
                if (
                    connection.dst_obj == self.selector_index
                    and connection.dst_inlet == 0
                ):
                    self.route_control_outlets.add(connection.src_outlet)
                else:
                    self.route_branches[connection.src_outlet] = connection.dst_obj
            if connection.dst_obj == self.selector_index and connection.dst_inlet > 0:
                self.selector_signal_sources[connection.dst_inlet - 1] = connection.src_obj
            if connection.src_obj == self.selector_index:
                self.selector_outlet_targets.append(connection.dst_obj)

        if self.outlet_index not in self.selector_outlet_targets:
            raise ValueError("selector~ does not reach the outlet~ in the patch")

        self.branch_expectations: Dict[int, Dict[str, object]] = {}
        for value, outlet_index in self.value_to_outlet.items():
            subpatch_obj = self.route_branches.get(outlet_index)
            if subpatch_obj is None:
                continue
            if self.selector_signal_sources.get(outlet_index) != subpatch_obj:
                continue
            subpatch_name = self.objects[subpatch_obj].type
            self.branch_expectations[value] = {
                "outlet_index": outlet_index,
                "subpatch_object": subpatch_obj,
                "subpatch": subpatch_name,
                "selector_output": f"{subpatch_name}::signal",
            }

        missing = sorted(set(self.route_args) - set(self.branch_expectations))
        if missing:
            raise ValueError(
                f"No selector routing expectations could be derived for values: {missing}"
            )

    def drive_selection(self, value: int) -> Dict[str, object]:
        """Simulate sending a selector value into inlet 0 of the patch."""

        if value not in self.branch_expectations:
            raise KeyError(f"Unexpected selector value: {value}")

        info = self.branch_expectations[value]
        outlet_index = info["outlet_index"]
        if outlet_index not in self.route_control_outlets:
            raise AssertionError(
                f"Route outlet {outlet_index} does not update the selector control"
            )

        return {
            "control_message": value,
            "active_subpatch": info["subpatch"],
            "selector_output": info["selector_output"],
        }

    def _parse_patch(self) -> None:
        for line in self.patch_path.read_text().splitlines():
            if line.startswith("#X obj "):
                self._add_object(line)
            elif line.startswith("#X connect "):
                self._add_connection(line)

    def _add_object(self, line: str) -> None:
        body = line[len("#X obj ") :].rstrip(";")
        tokens = body.split()
        if len(tokens) < 3:
            raise ValueError(f"Malformed object line: {line}")
        obj_type = tokens[2]
        args = tokens[3:]
        self.objects.append(PdObject(index=len(self.objects), type=obj_type, args=args))

    def _add_connection(self, line: str) -> None:
        body = line[len("#X connect ") :].rstrip(";")
        parts = body.split()
        if len(parts) != 4:
            raise ValueError(f"Malformed connection line: {line}")
        src_obj, src_outlet, dst_obj, dst_inlet = map(int, parts)
        self.connections.append(
            PdConnection(
                src_obj=src_obj,
                src_outlet=src_outlet,
                dst_obj=dst_obj,
                dst_inlet=dst_inlet,
            )
        )

    def _find_unique_object(self, obj_type: str) -> int:
        indices = [obj.index for obj in self.objects if obj.type == obj_type]
        if len(indices) != 1:
            raise ValueError(f"Expected exactly one '{obj_type}' object, found {indices}")
        return indices[0]


def test_source_generator_selector_routing() -> None:
    patch_path = Path(__file__).resolve().parents[1] / "patches" / "source-generator.pd"
    harness = SourceGeneratorHarness(patch_path)

    expected_values = list(range(6))
    assert sorted(harness.branch_expectations) == expected_values

    for value in expected_values:
        result = harness.drive_selection(value)
        expectation = harness.branch_expectations[value]

        assert result["control_message"] == value
        assert result["active_subpatch"] == expectation["subpatch"]
        assert result["selector_output"] == expectation["selector_output"]

        for other_value, other_expectation in harness.branch_expectations.items():
            if other_value == value:
                continue
            assert result["selector_output"] != other_expectation["selector_output"]
