"""
Reusable Streamlit output components shared across all pipelines.
"""
import streamlit as st


def render_report_output(result: dict) -> None:
    if result.get("errors"):
        for err in result["errors"]:
            st.error(err)
        return

    st.success("Pipeline completed!")

    steps = result.get("steps_completed", [])
    if steps:
        st.caption(f"Steps completed: {', '.join(steps)}")

    report_text = result.get("ac_audit_report") or result.get("summary_report", "")

    tab1, tab2 = st.tabs(["Report", "Raw Data"])
    with tab1:
        st.markdown(report_text)
    with tab2:
        st.json(result)

    if report_text:
        st.download_button(
            label="Download Report",
            data=report_text,
            file_name="report.txt",
            mime="text/plain",
        )