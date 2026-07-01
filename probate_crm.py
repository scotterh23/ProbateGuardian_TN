"""
ProbateGuardian CRM — Branton Walker mobile money machine.
Open app → see hot list → tap lead → one-tap actions → done.
"""
import streamlit as st


class _LazyApp:
    """Resolve app helpers from the active Streamlit script — never reload app.py."""

    _mod = None

    @staticmethod
    def _resolve_app_module():
        import sys

        main = sys.modules.get("__main__")
        main_file = getattr(main, "__file__", "") or ""
        if main is not None and main_file.endswith("app_local_crm.py"):
            return main
        if main is not None and main_file.endswith("app.py"):
            return main
        import importlib

        return importlib.import_module("app")

    def __getattr__(self, name: str):
        if self._mod is None:
            self._mod = self._resolve_app_module()
        return getattr(self._mod, name)


pg = _LazyApp()


def render_probate_crm() -> None:
    """Single-screen CRM — call queue is the entire product."""
    run_serial = st.session_state.get("_run_serial", 0)
    if st.session_state.get("_crm_done_serial") == run_serial:
        return

    pg.render_crm_call_queue(st.session_state.leads)
    st.session_state["_crm_done_serial"] = run_serial