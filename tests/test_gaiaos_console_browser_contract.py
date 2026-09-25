"""Fail-closed browser contract for GaiaOS's owner-operated Render consoles.

Tests the *rendered GET response*, not the Python HTML template. A no-secret
Node VM checks that every type=button control has a handler; node --check
rejects JavaScript syntax errors caused by Python string interpolation.
No authenticated POST, provider/model call, or MemoryOS operation is made.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from fastapi.responses import HTMLResponse
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

import gaiaos_app as carrier


# Every new GET /gaiaos/*console route must be registered here. The discovery
# assertion below fails when a new console is added without its browser test.
CONSOLE_ROUTES = frozenset({
    "/gaiaos/memory/technical-partial-console",
})

# Node is mandatory in this CI gate, not an optional skip. GitHub-hosted Linux
# runners supply Node; local contributors must install it to run this suite.
BUTTON_WIRING_HARNESS = r"""
"use strict";
const fs = require("node:fs");
const vm = require("node:vm");
const script = fs.readFileSync(process.argv[2], "utf8");
const manifest = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
const elements = Object.create(null);
const clickHandlers = new Map();
const readyHandlers = [];
let networkRequests = 0;

for (const id of manifest.ids) {
  elements[id] = {
    value: "", checked: false, disabled: false, hidden: false, textContent: "",
    addEventListener(event, fn) {
      if (event === "click") {
        if (clickHandlers.has(id)) throw Error("Duplicate click handler: " + id);
        clickHandlers.set(id, fn);
      }
    },
    replaceChildren() {}, appendChild() {}
  };
}
const document = {
  getElementById(id) {
    if (!(id in elements)) throw Error("Script references absent element: " + id);
    return elements[id];
  },
  createElement(name) {
    return {
      value: "", textContent: "", id: "", appendChild() {},
      addEventListener() {}
    };
  },
  addEventListener(event, fn) {
    if (event === "DOMContentLoaded") readyHandlers.push(fn);
  }
};
const context = {
  document,
  fetch() { networkRequests++; throw Error("Unexpected network request during console init"); },
  navigator: {clipboard: {writeText() {throw Error("Clipboard access in CI");}}},
  console
};
(async function main() {
  vm.runInNewContext(script, context, {timeout: 1000, filename: "served-console.js"});
  for (const fn of readyHandlers) await fn();
  const missing = manifest.buttons.filter(id => !clickHandlers.has(id));
  if (missing.length) throw Error("Buttons without click handlers: " + missing.join(","));
  if (networkRequests) throw Error("Network request during console initialization");
  // The privacy-critical oracle action must reject a missing key without
  // touching the network. This exercises an actual registered click handler.
  if (manifest.buttons.includes("oracle")) {
    await clickHandlers.get("oracle")();
    if (!elements.status || !/key/i.test(elements.status.textContent)) {
      throw Error("Oracle click did not provide missing-key feedback");
    }
    if (networkRequests) throw Error("Unauthenticated oracle click reached network");
  }
  process.stdout.write("CONSOLE_BUTTON_WIRING_PASS\n");
})().catch(error => {
  process.stderr.write(String(error.message || error) + "\n");
  process.exitCode = 1;
});
"""


class ConsoleHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.ids: list[str] = []
        self.buttons: list[str] = []
        self.scripts: list[tuple[dict[str, str | None], str]] = []
        self._script_attrs: dict[str, str | None] | None = None
        self._script_body: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id") is not None:
            self.ids.append(values["id"])
        if tag == "button":
            kind = (values.get("type") or "submit").lower()
            if kind == "button":
                if not values.get("id"):
                    raise AssertionError("A JavaScript-driven console button lacks an ID")
                self.buttons.append(values["id"])
        if tag == "script":
            self._script_attrs = values
            self._script_body = []

    def handle_data(self, data: str) -> None:
        if self._script_attrs is not None:
            self._script_body.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script" and self._script_attrs is not None:
            self.scripts.append((self._script_attrs, "".join(self._script_body)))
            self._script_attrs = None
            self._script_body = []


def _node(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", *args], text=True, capture_output=True,
        timeout=15, check=False,
    )


class RenderConsoleBrowserContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if shutil.which("node") is None:
            raise AssertionError(
                "Node.js is mandatory for Render console JavaScript validation"
            )

    def test_every_gaiaos_console_is_registered(self) -> None:
        discovered = {
            route.path
            for route in carrier.app.routes
            if isinstance(route, APIRoute)
            and "GET" in (route.methods or set())
            and route.path.startswith("/gaiaos/")
            and "console" in route.path
            and isinstance(route.response_class, type)
            and issubclass(route.response_class, HTMLResponse)
        }
        self.assertEqual(
            discovered, CONSOLE_ROUTES,
            "Register every new GaiaOS console and audit its interactive controls",
        )

    def test_rendered_console_js_parses_and_every_button_is_wired(self) -> None:
        with TestClient(carrier.app) as client:
            for path in sorted(CONSOLE_ROUTES):
                with self.subTest(path=path):
                    response = client.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("no-store", response.headers.get("cache-control", ""))
                    self.assertIn("nonce-", response.headers.get(
                        "content-security-policy", ""
                    ))
                    parser = ConsoleHTMLParser()
                    parser.feed(response.text)
                    self.assertEqual(
                        len(parser.ids), len(set(parser.ids)),
                        "Duplicate element IDs make click handlers ambiguous",
                    )
                    self.assertTrue(parser.buttons, "Console has no registered buttons")
                    self.assertTrue(parser.scripts, "Console buttons have no script")
                    self.assertEqual(
                        len(parser.scripts), 1,
                        "Add multi-script support before shipping another console script",
                    )
                    attrs, source = parser.scripts[0]
                    self.assertIsNone(attrs.get("src"), "External script not validated")
                    self.assertIn(attrs.get("nonce"), response.headers[
                        "content-security-policy"
                    ])
                    with tempfile.TemporaryDirectory() as folder:
                        root = Path(folder)
                        script = root / "served-console.js"
                        manifest = root / "button-manifest.json"
                        harness = root / "button-wiring.js"
                        script.write_text(source, encoding="utf-8")
                        manifest.write_text(json.dumps({
                            "ids": parser.ids, "buttons": parser.buttons,
                        }), encoding="utf-8")
                        harness.write_text(BUTTON_WIRING_HARNESS, encoding="utf-8")
                        syntax = _node(["--check", str(script)])
                        self.assertEqual(
                            syntax.returncode, 0, "Served JavaScript syntax error: "
                            + syntax.stderr[:1000],
                        )
                        wired = _node([str(harness), str(script), str(manifest)])
                        self.assertEqual(
                            wired.returncode, 0,
                            "Served console button wiring failure: "
                            + wired.stderr[:1000],
                        )
                        self.assertIn("CONSOLE_BUTTON_WIRING_PASS", wired.stdout)

    def test_guard_rejects_the_original_raw_newline_failure(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            broken = Path(folder) / "original-regression.js"
            broken.write_text(
                'const statement = "line one\nline two";\n',
                encoding="utf-8",
            )
            self.assertNotEqual(_node(["--check", str(broken)]).returncode, 0)

    def test_guard_rejects_an_inert_button(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "inert.js").write_text('"use strict";\n', encoding="utf-8")
            (root / "manifest.json").write_text(json.dumps({
                "ids": ["orphan"], "buttons": ["orphan"],
            }), encoding="utf-8")
            (root / "harness.js").write_text(
                BUTTON_WIRING_HARNESS, encoding="utf-8",
            )
            verdict = _node([
                str(root / "harness.js"), str(root / "inert.js"),
                str(root / "manifest.json"),
            ])
            self.assertNotEqual(verdict.returncode, 0)
            self.assertIn("Buttons without click handlers", verdict.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
