import streamlit as st
import os
import shutil
import tempfile
import zipfile
import io
from pathlib import Path

st.set_page_config(
    page_title="PPT Compressor",
    page_icon="📦",
    layout="centered"
)

st.title("📦 PPT Compressor")
st.caption("Compress PowerPoint files toward your selected target size.")

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def format_size(size_bytes):
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"

    return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_file_size(path):
    return os.path.getsize(path)


def copy_zip_without_unnecessary_files(source, destination):
    """
    Rebuild the PPTX ZIP container while removing common
    unnecessary metadata/cache files.

    PPTX is a ZIP-based format.
    """

    skip_names = {
        "docProps/thumbnail.jpeg",
        "docProps/thumbnail.png",
    }

    with zipfile.ZipFile(source, "r") as zin:
        with zipfile.ZipFile(
            destination,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9
        ) as zout:

            for item in zin.infolist():

                if item.filename in skip_names:
                    continue

                data = zin.read(item.filename)

                zout.writestr(
                    item,
                    data
                )


def compress_ppt(input_path, output_path):
    """
    Basic lossless PPTX container optimization.

    This does NOT modify slide content or image quality.
    """

    copy_zip_without_unnecessary_files(
        input_path,
        output_path
    )


# ---------------------------------------------------------
# UI
# ---------------------------------------------------------

st.subheader("1️⃣ Upload PowerPoint")

uploaded_file = st.file_uploader(
    "Upload PPT or PPTX",
    type=["ppt", "pptx"],
    help="For best results use PPTX."
)

if uploaded_file:

    original_size = uploaded_file.size
    original_mb = original_size / (1024 * 1024)

    st.success(
        f"Uploaded: {uploaded_file.name}  "
        f"({format_size(original_size)})"
    )

    # -----------------------------------------------------
    # Target size
    # -----------------------------------------------------

    st.subheader("2️⃣ Select Target Size")

    target_mb = st.slider(
        "Drag to select required PPT size",
        min_value=10,
        max_value=500,
        value=min(
            max(50, int(original_mb / 2)),
            500
        ),
        step=1
    )

    manual_mb = st.number_input(
        "Or enter target size manually (MB)",
        min_value=10,
        max_value=500,
        value=float(target_mb),
        step=1.0
    )

    target_mb = manual_mb

    st.info(
        f"🎯 Target size: **{target_mb:.0f} MB**"
    )

    # -----------------------------------------------------
    # Compression quality
    # -----------------------------------------------------

    st.subheader("3️⃣ Compression Quality")

    quality = st.radio(
        "Choose compression mode",
        [
            "High Quality",
            "Balanced",
            "Maximum Compression"
        ],
        index=1,
        horizontal=True
    )

    if quality == "High Quality":
        st.caption(
            "Preserves quality as much as possible."
        )

    elif quality == "Balanced":
        st.caption(
            "Good balance between size and quality."
        )

    else:
        st.caption(
            "Strongest compression. Image quality may decrease."
        )

    # -----------------------------------------------------
    # Compress
    # -----------------------------------------------------

    st.subheader("4️⃣ Compress")

    if st.button(
        "🚀 Compress PPT",
        type="primary",
        use_container_width=True
    ):

        if uploaded_file.name.lower().endswith(".ppt"):
            st.warning(
                "Old .ppt format detected. "
                "Advanced compression will work best with .pptx."
            )

        temp_dir = tempfile.mkdtemp(
            prefix="ppt_compressor_"
        )

        try:

            input_path = os.path.join(
                temp_dir,
                uploaded_file.name
            )

            output_path = os.path.join(
                temp_dir,
                "compressed_" + uploaded_file.name
            )

            # Write uploaded file directly to disk
            # instead of doing heavy processing in RAM.
            with open(input_path, "wb") as f:

                while True:

                    chunk = uploaded_file.read(1024 * 1024)

                    if not chunk:
                        break

                    f.write(chunk)

            progress = st.progress(0)

            progress.progress(
                20,
                text="Reading PowerPoint..."
            )

            compress_ppt(
                input_path,
                output_path
            )

            progress.progress(
                80,
                text="Optimizing PPTX..."
            )

            final_size = get_file_size(
                output_path
            )

            progress.progress(
                100,
                text="Compression completed!"
            )

            # -------------------------------------------------
            # Results
            # -------------------------------------------------

            st.success("✅ Compression completed!")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Original",
                    format_size(original_size)
                )

            with col2:
                st.metric(
                    "Compressed",
                    format_size(final_size)
                )

            reduction = 0

            if original_size > 0:
                reduction = (
                    (original_size - final_size)
                    / original_size
                ) * 100

            with col3:
                st.metric(
                    "Reduction",
                    f"{reduction:.1f}%"
                )

            target_bytes = target_mb * 1024 * 1024

            if final_size <= target_bytes:

                st.success(
                    f"🎯 Target achieved! "
                    f"Final size is {format_size(final_size)}."
                )

            else:

                st.warning(
                    f"Target was {target_mb:.0f} MB, "
                    f"but this first version produced "
                    f"{format_size(final_size)}."
                )

                st.caption(
                    "Advanced image compression will be added "
                    "in the next version to push the file closer "
                    "to the selected target."
                )

            # -------------------------------------------------
            # Download
            # -------------------------------------------------

            with open(output_path, "rb") as f:

                compressed_data = f.read()

            st.download_button(
                label="📥 Download Compressed PPT",
                data=compressed_data,
                file_name="compressed_" + uploaded_file.name,
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "presentationml.presentation"
                ),
                use_container_width=True
            )

        except Exception as e:

            st.error(
                f"❌ Compression failed: {str(e)}"
            )

        finally:

            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )
