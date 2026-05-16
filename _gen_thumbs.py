import sys, types, importlib.util, contextlib
from pathlib import Path

fake_st = types.ModuleType("streamlit")
fake_st.set_page_config = lambda **kw: None
fake_st.title           = lambda *a, **kw: None
fake_st.columns         = lambda n: [types.SimpleNamespace(
                              text_input=lambda *a, **kw: "",
                              text_area =lambda *a, **kw: "")] * n
fake_st.text_input      = lambda *a, **kw: ""
fake_st.text_area       = lambda *a, **kw: ""
fake_st.button          = lambda *a, **kw: False
fake_st.spinner         = lambda *a, **kw: contextlib.nullcontext()
fake_st.error           = lambda *a, **kw: None
fake_st.image           = lambda *a, **kw: None
fake_st.download_button = lambda *a, **kw: None
sys.modules["streamlit"] = fake_st


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HERE = Path(__file__).parent
CODE  = "5016"
LINES = ["JX金属", "自社株取得へ", "最大2500億円", "ENEOSが一部売却"]


def main():
    dark   = load("td", str(HERE / "app_thumbnail_dark.py"))
    normal = load("tn", str(HERE / "app_thumbnail_normal.py"))

    df, name = dark.fetch(CODE)
    print(f"fetched: {name}  rows={len(df)}")

    (HERE / "thumbnail_dark.png").write_bytes(dark.render(df, CODE, name, LINES))
    (HERE / "thumbnail_normal.png").write_bytes(normal.render(df, CODE, name, LINES))
    print("written: thumbnail_dark.png / thumbnail_normal.png")


if __name__ == "__main__":
    main()
