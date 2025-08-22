# 🛠️ Direct Tool Use

Under the hood, agents are using a set of tools. You can directly access these tools.

## Agent OS

The controller for the operating system.

```python
agent.tools.os.click("left", 2) # clicking
agent.tools.os.mouse_move(100, 100) # mouse movement
agent.tools.os.keyboard_tap("v", modifier_keys=["control"]) # Paste
# and many more
```

## Web browser

The webbrowser tool powered by [webbrowser](https://docs.python.org/3/library/webbrowser.html) allows you to directly access webbrowsers in your environment.

```python
agent.tools.webbrowser.open_new("http://www.google.com")
# also check out open and open_new_tab
```

## Clipboard

The clipboard tool powered by [pyperclip](https://github.com/asweigart/pyperclip) allows you to interact with the clipboard.

```python
agent.tools.clipboard.copy("...")
result = agent.tools.clipboard.paste()
```

## 🖥️ Multi-Monitor Support

You have multiple monitors? Choose which one to automate by setting `display` to `1`, `2` etc. To find the correct display or monitor, you have to play play around a bit setting it to different values. We are going to improve this soon. By default, the agent will use display 1.

```python
with VisionAgent(display=1) as agent:
    agent...
```
