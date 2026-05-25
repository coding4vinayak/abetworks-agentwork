"""Tests for the plugin system: manifest, plugin, and manager."""

import json
import os

import pytest

from agentwork.plugins.manifest import PluginManifest
from agentwork.plugins.plugin import Plugin
from agentwork.plugins.manager import PluginManager
from agentwork.tools.base import Tool


# --- Helpers ---


def _create_plugin_module(tmp_path, module_name="my_plugin.py", content=None):
    """Create a temporary Python module that defines tools using @tool decorator."""
    if content is None:
        content = '''
from agentwork.tools.decorators import tool

@tool(name="add", description="Add two numbers")
def add(a: int, b: int) -> int:
    return a + b

@tool(name="multiply", description="Multiply two numbers")
def multiply(a: int, b: int) -> int:
    return a * b

not_a_tool = "I am just a string"
'''
    module_path = tmp_path / module_name
    module_path.write_text(content)
    return str(module_path)


def _create_plugin_json(directory, manifest_data):
    """Create a plugin.json file in the given directory."""
    manifest_path = os.path.join(directory, "plugin.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f)
    return manifest_path


# --- TestPluginManifest ---


class TestPluginManifest:
    """Tests for PluginManifest model."""

    def test_valid_manifest_creation(self):
        manifest = PluginManifest(
            name="test-plugin",
            version="1.0.0",
            description="A test plugin",
            author="Test Author",
            tools=["add", "multiply"],
            dependencies=["numpy"],
            entry_point="my_package.tools",
        )
        assert manifest.name == "test-plugin"
        assert manifest.version == "1.0.0"
        assert manifest.description == "A test plugin"
        assert manifest.author == "Test Author"
        assert manifest.tools == ["add", "multiply"]
        assert manifest.dependencies == ["numpy"]
        assert manifest.entry_point == "my_package.tools"

    def test_manifest_defaults(self):
        manifest = PluginManifest(name="minimal", entry_point="some.module")
        assert manifest.version == "0.1.0"
        assert manifest.description == ""
        assert manifest.author == ""
        assert manifest.tools == []
        assert manifest.dependencies == []

    def test_manifest_requires_name(self):
        with pytest.raises(Exception):
            PluginManifest(entry_point="some.module")

    def test_manifest_requires_entry_point(self):
        with pytest.raises(Exception):
            PluginManifest(name="test")

    def test_manifest_from_dict(self):
        data = {
            "name": "dict-plugin",
            "entry_point": "path/to/module.py",
            "version": "2.0.0",
        }
        manifest = PluginManifest(**data)
        assert manifest.name == "dict-plugin"
        assert manifest.entry_point == "path/to/module.py"
        assert manifest.version == "2.0.0"


# --- TestPlugin ---


class TestPlugin:
    """Tests for Plugin class lifecycle."""

    def test_load_from_file_path(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(
            name="file-plugin",
            entry_point=module_path,
        )
        plugin = Plugin(manifest)
        plugin.load()

        assert plugin.loaded is True
        assert plugin.error is None
        assert len(plugin.tools) == 2
        tool_names = [t.name for t in plugin.tools]
        assert "add" in tool_names
        assert "multiply" in tool_names

    def test_plugin_properties(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(
            name="props-plugin",
            version="3.0.0",
            entry_point=module_path,
        )
        plugin = Plugin(manifest)
        assert plugin.name == "props-plugin"
        assert plugin.version == "3.0.0"
        assert plugin.loaded is False
        assert plugin.tools == []

    def test_unload_clears_tools(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(name="unload-test", entry_point=module_path)
        plugin = Plugin(manifest)
        plugin.load()
        assert len(plugin.tools) == 2
        assert plugin.loaded is True

        plugin.unload()
        assert plugin.loaded is False
        assert plugin.tools == []

    def test_reload_refreshes_tools(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(name="reload-test", entry_point=module_path)
        plugin = Plugin(manifest)
        plugin.load()
        assert len(plugin.tools) == 2

        # Rewrite module with only one tool
        new_content = '''
from agentwork.tools.decorators import tool

@tool(name="subtract", description="Subtract two numbers")
def subtract(a: int, b: int) -> int:
    return a - b
'''
        with open(module_path, "w") as f:
            f.write(new_content)

        plugin.reload()
        assert plugin.loaded is True
        assert len(plugin.tools) == 1
        assert plugin.tools[0].name == "subtract"

    def test_load_error_captured_gracefully(self):
        manifest = PluginManifest(
            name="bad-plugin",
            entry_point="nonexistent.module.that.doesnt.exist",
        )
        plugin = Plugin(manifest)
        plugin.load()

        assert plugin.loaded is False
        assert plugin.error is not None
        assert len(plugin.tools) == 0

    def test_load_returns_self_for_chaining(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(name="chain-test", entry_point=module_path)
        plugin = Plugin(manifest)
        result = plugin.load()
        assert result is plugin

    def test_load_invalid_file_path(self):
        manifest = PluginManifest(
            name="bad-file",
            entry_point="/nonexistent/path/module.py",
        )
        plugin = Plugin(manifest)
        plugin.load()

        assert plugin.loaded is False
        assert plugin.error is not None

    def test_tools_are_tool_instances(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(name="type-check", entry_point=module_path)
        plugin = Plugin(manifest)
        plugin.load()

        for t in plugin.tools:
            assert isinstance(t, Tool)


# --- TestPluginManager ---


class TestPluginManager:
    """Tests for PluginManager."""

    def test_discover_finds_plugin_json(self, tmp_path):
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()
        _create_plugin_json(
            str(plugin_dir),
            {
                "name": "discovered-plugin",
                "entry_point": "some.module",
                "version": "1.0.0",
            },
        )

        manager = PluginManager()
        manifests = manager.discover(str(tmp_path))
        assert len(manifests) == 1
        assert manifests[0].name == "discovered-plugin"

    def test_discover_finds_nested_plugins(self, tmp_path):
        dir_a = tmp_path / "plugins" / "plugin_a"
        dir_b = tmp_path / "plugins" / "plugin_b"
        dir_a.mkdir(parents=True)
        dir_b.mkdir(parents=True)

        _create_plugin_json(str(dir_a), {"name": "plugin-a", "entry_point": "a.mod"})
        _create_plugin_json(str(dir_b), {"name": "plugin-b", "entry_point": "b.mod"})

        manager = PluginManager()
        manifests = manager.discover(str(tmp_path))
        assert len(manifests) == 2
        names = {m.name for m in manifests}
        assert names == {"plugin-a", "plugin-b"}

    def test_discover_nonexistent_directory(self):
        manager = PluginManager()
        manifests = manager.discover("/nonexistent/path/to/plugins")
        assert manifests == []

    def test_discover_skips_invalid_manifest(self, tmp_path):
        plugin_dir = tmp_path / "bad_plugin"
        plugin_dir.mkdir()
        # Missing required fields
        manifest_path = plugin_dir / "plugin.json"
        manifest_path.write_text('{"description": "no name or entry_point"}')

        manager = PluginManager()
        manifests = manager.discover(str(tmp_path))
        assert manifests == []

    def test_load_plugin_loads_and_tracks(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(name="tracked-plugin", entry_point=module_path)

        manager = PluginManager()
        plugin = manager.load_plugin(manifest)

        assert plugin.loaded is True
        assert manager.get_plugin("tracked-plugin") is plugin

    def test_unload_plugin_removes(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(name="removable", entry_point=module_path)

        manager = PluginManager()
        manager.load_plugin(manifest)
        assert manager.get_plugin("removable") is not None

        manager.unload_plugin("removable")
        assert manager.get_plugin("removable") is None

    def test_list_plugins_returns_all(self, tmp_path):
        mod1 = _create_plugin_module(tmp_path, "mod1.py")
        mod2 = _create_plugin_module(tmp_path, "mod2.py")

        manager = PluginManager()
        manager.load_plugin(PluginManifest(name="p1", entry_point=mod1))
        manager.load_plugin(PluginManifest(name="p2", entry_point=mod2))

        plugins = manager.list_plugins()
        assert len(plugins) == 2
        names = {p.name for p in plugins}
        assert names == {"p1", "p2"}

    def test_get_all_tools_aggregates(self, tmp_path):
        mod1 = _create_plugin_module(tmp_path, "mod1.py")
        content2 = '''
from agentwork.tools.decorators import tool

@tool(name="greet", description="Greet someone")
def greet(name: str) -> str:
    return f"Hello, {name}!"
'''
        mod2 = _create_plugin_module(tmp_path, "mod2.py", content=content2)

        manager = PluginManager()
        manager.load_plugin(PluginManifest(name="math-plugin", entry_point=mod1))
        manager.load_plugin(PluginManifest(name="greet-plugin", entry_point=mod2))

        all_tools = manager.get_all_tools()
        assert len(all_tools) == 3
        tool_names = {t.name for t in all_tools}
        assert tool_names == {"add", "multiply", "greet"}

    def test_reload_plugin_works(self, tmp_path):
        module_path = _create_plugin_module(tmp_path)
        manifest = PluginManifest(name="reloadable", entry_point=module_path)

        manager = PluginManager()
        manager.load_plugin(manifest)
        assert len(manager.get_plugin("reloadable").tools) == 2

        # Rewrite module
        new_content = '''
from agentwork.tools.decorators import tool

@tool(name="only_one", description="Only tool")
def only_one() -> str:
    return "one"
'''
        with open(module_path, "w") as f:
            f.write(new_content)

        plugin = manager.reload_plugin("reloadable")
        assert plugin.loaded is True
        assert len(plugin.tools) == 1
        assert plugin.tools[0].name == "only_one"

    def test_reload_plugin_not_found(self):
        manager = PluginManager()
        with pytest.raises(KeyError):
            manager.reload_plugin("nonexistent")

    def test_get_plugin_not_found(self):
        manager = PluginManager()
        assert manager.get_plugin("nope") is None

    def test_full_discover_and_load_workflow(self, tmp_path):
        """End-to-end: discover plugin.json, load, and use tools."""
        plugin_dir = tmp_path / "my_plugin"
        plugin_dir.mkdir()

        # Create module file
        module_content = '''
from agentwork.tools.decorators import tool

@tool(name="echo", description="Echo input")
def echo(msg: str) -> str:
    return msg
'''
        module_file = plugin_dir / "tools.py"
        module_file.write_text(module_content)

        # Create plugin.json pointing to the module file
        _create_plugin_json(
            str(plugin_dir),
            {
                "name": "echo-plugin",
                "entry_point": str(module_file),
                "version": "1.0.0",
                "tools": ["echo"],
            },
        )

        manager = PluginManager()
        manifests = manager.discover(str(tmp_path))
        assert len(manifests) == 1

        plugin = manager.load_plugin(manifests[0])
        assert plugin.loaded is True
        assert len(plugin.tools) == 1
        assert plugin.tools[0].name == "echo"

        # Verify the tool actually works
        result = plugin.tools[0].execute("hello")
        assert result.output == "hello"
        assert result.success is True
