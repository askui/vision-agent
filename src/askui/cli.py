import streamlit.web.cli as stcli
import sys
import importlib.util


def main():
    chat_module = importlib.util.find_spec('askui.chat').origin
    sys.argv = ["streamlit", "run", chat_module]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
