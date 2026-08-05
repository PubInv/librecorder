from __future__ import annotations

import tempfile

from pathlib import Path

import pandas as pd
import streamlit as st

from src.predict import (
    predict_image,
)


st.set_page_config(
    page_title="HAM10000 CNN Demo",
    page_icon="🔬",
    layout="centered",
)


st.title(
    "HAM10000 Skin-Lesion Classifier"
)


st.warning(
    "Research demonstration only. "
    "This model is not clinically "
    "validated and must not be used "
    "for medical diagnosis."
)


uploaded_file = st.file_uploader(
    "Upload a dermoscopic image",

    type=[
        "jpg",
        "jpeg",
        "png",
    ],
)


if uploaded_file is not None:
    st.image(
        uploaded_file,
        caption="Uploaded image",
        use_container_width=True,
    )

    suffix = (
        Path(uploaded_file.name).suffix
        or ".jpg"
    )

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as temporary_file:

        temporary_file.write(
            uploaded_file.getbuffer()
        )

        temporary_path = Path(
            temporary_file.name
        )

    try:
        with st.spinner(
            "Running CNN prediction..."
        ):
            result = predict_image(
                temporary_path
            )

        st.subheader("Prediction")

        st.write(
            "**Class code:** "
            f"`{result['predicted_class']}`"
        )

        st.write(
            "**Class description:** "
            f"{result['description']}"
        )

        st.write(
            "**Confidence:** "
            f"{result['confidence']:.2%}"
        )

        probability_table = (
            pd.DataFrame(
                {
                    "class": list(
                        result[
                            "probabilities"
                        ].keys()
                    ),

                    "probability": list(
                        result[
                            "probabilities"
                        ].values()
                    ),
                }
            )
            .sort_values(
                "probability",
                ascending=False,
            )
        )

        st.subheader(
            "All class probabilities"
        )

        st.dataframe(
            probability_table,
            hide_index=True,
            use_container_width=True,
        )

        st.bar_chart(
            probability_table.set_index(
                "class"
            )
        )

    except Exception as error:
        st.error(str(error))

    finally:
        temporary_path.unlink(
            missing_ok=True
        )