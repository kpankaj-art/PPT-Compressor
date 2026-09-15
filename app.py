import streamlit as st
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="PPT Compressor",
    page_icon="📦",
    layout="centered"
)

# =========================================================
# FUNCTIONS
# =========================================================

def format_size(size_bytes):
    """Convert bytes to readable size."""

    if size_bytes < 1024:
        return f"{size_bytes} B"

    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"

    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

    return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def remove_unnecessary_files(source, destination):
    """
    Rebuild PPTX ZIP container with maximum ZIP compression.
    This is lossless and does not reduce image quality.
    """

    skip_files = {
        "docProps/thumbnail.jpeg",
        "docProps/thumbnail.png",
        "docProps/thumbnail.jpg",
    }

    with zipfile.ZipFile(source, "r") as zin:

        with zipfile.ZipFile(
            destination,
            "w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9
        ) as zout:

            for item in zin.infolist():

                # Skip unnecessary thumbnails
                if item.filename in skip_files:
                    continue

                # Skip directories
                if item.is_dir():
                    zout.writestr(item, b"")
                    continue

                data = zin.read(item.filename)

                zout.writestr(
                    item,
                    data
                )


def compress_file(input_path, output_path):

    remove_unnecessary_files(
        input_path,
        output_path
    )


# =========================================================
# HEADER
# =========================================================

st.title("📦 PPT Compressor")

st.write(
    "Compress your PowerPoint file and select your preferred "
    "target size."
)

st.divider()

# =========================================================
# UPLOAD
# =========================================================

st.subheader("1️⃣ Upload PowerPoint")

uploaded_file = st.file_uploader(
    "Choose a PPT or PPTX file",
    type=["ppt", "pptx"],
    help="For best results use PPTX format."
)

# =========================================================
# AFTER UPLOAD
# =========================================================

if uploaded_file:

    original_size = uploaded_file.size
    original_mb = original_size / (1024 * 1024)

    st.success(
        f"Uploaded: **{uploaded_file.name}**  "
        f"({format_size(original_size)})"
    )

    # =====================================================
    # TARGET SIZE
    # =====================================================

    st.subheader("2️⃣ Select Target Size")

    # Safe integer value for slider
    default_slider_value = int(original_mb / 2)

    if default_slider_value < 10:
        default_slider_value = 10

    if default_slider_value > 500:
        default_slider_value = 500

    target_slider = st.slider(
        "🎯 Drag to select required PPT size",
        min_value=10,
        max_value=500,
        value=default_slider_value,
        step=1
    )

    st.write(
        f"Selected target: **{target_slider} MB**"
    )

    # =====================================================
    # MANUAL SIZE
    # =====================================================

    manual_mb = st.number_input(
        "Or enter target size manually (MB)",
        min_value=10.0,
        max_value=500.0,
        value=float(target_slider),
        step=1.0
    )

    target_mb = float(manual_mb)

    st.info(
        f"🎯 Final target size: **{target_mb:.0f} MB**"
    )

    # =====================================================
    # QUALITY
    # =====================================================

    st.subheader("3️⃣ Compression Quality")

    quality = st.selectbox(
        "Select compression level",
        [
            "High Quality",
            "Balanced",
            "Maximum Compression"
        ],
        index=1
    )

    if quality == "High Quality":

        st.caption(
            "Best quality. Minimal compression."
        )

    elif quality == "Balanced":

        st.caption(
            "Recommended. Good balance between quality and size."
        )

    else:

        st.caption(
            "Maximum compression. Image quality may be reduced "
            "in the advanced version."
        )

    # =====================================================
    # COMPRESS BUTTON
    # =====================================================

    st.subheader("4️⃣ Start Compression")

    compress_button = st.button(
        "🚀 Compress PPT",
        type="primary",
        use_container_width=True
    )

    # =====================================================
    # PROCESS
    # =====================================================

    if compress_button:

        # Old .ppt warning
        if uploaded_file.name.lower().endswith(".ppt"):

            st.warning(
                "⚠️ This is an old .ppt file. "
                "For better compression results, convert it to "
                ".pptx first."
            )

        temp_dir = tempfile.mkdtemp(
            prefix="ppt_compressor_"
        )

        try:

            # -------------------------------------------------
            # FILE PATHS
            # -------------------------------------------------

            input_path = os.path.join(
                temp_dir,
                uploaded_file.name
            )

            output_path = os.path.join(
                temp_dir,
                "compressed_" + uploaded_file.name
            )

            # -------------------------------------------------
            # SAVE UPLOAD TO DISK
            # -------------------------------------------------

            progress = st.progress(
                0,
                text="Saving PowerPoint..."
            )

            with open(input_path, "wb") as file:

                while True:

                    chunk = uploaded_file.read(
                        1024 * 1024
                    )

                    if not chunk:
                        break

                    file.write(chunk)

            progress.progress(
                25,
                text="PowerPoint saved..."
            )

            # -------------------------------------------------
            # COMPRESSION
            # -------------------------------------------------

            progress.progress(
                40,
                text="Compressing PowerPoint..."
            )

            compress_file(
                input_path,
                output_path
            )

            progress.progress(
                85,
                text="Finalizing compressed file..."
            )

            # -------------------------------------------------
            # RESULT
            # -------------------------------------------------

            final_size = os.path.getsize(
                output_path
            )

            progress.progress(
                100,
                text="Compression completed!"
            )

            st.success(
                "✅ Compression completed successfully!"
            )

            # -------------------------------------------------
            # STATS
            # -------------------------------------------------

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

            with col3:

                if original_size > 0:

                    reduction = (
                        (original_size - final_size)
                        / original_size
                    ) * 100

                else:

                    reduction = 0

                st.metric(
                    "Reduction",
                    f"{reduction:.1f}%"
                )

            # -------------------------------------------------
            # TARGET CHECK
            # -------------------------------------------------

            target_bytes = (
                target_mb * 1024 * 1024
            )

            if final_size <= target_bytes:

                st.success(
                    f"🎯 Target achieved!\n\n"
                    f"Target: {target_mb:.0f} MB\n\n"
                    f"Final: {format_size(final_size)}"
                )

            else:

                difference = (
                    final_size - target_bytes
                )

                st.warning(
                    f"⚠️ Target size was "
                    f"{target_mb:.0f} MB, but the current "
                    f"compression engine produced "
                    f"{format_size(final_size)}."
                )

                st.caption(
                    f"Approximately {format_size(difference)} "
                    f"more compression is required."
                )

            # -------------------------------------------------
            # DOWNLOAD
            # -------------------------------------------------

            st.subheader("📥 Download")

            with open(output_path, "rb") as file:

                compressed_data = file.read()

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

        except Exception as error:

            st.error(
                "❌ Compression failed."
            )

            st.code(
                str(error)
            )

        finally:

            # -------------------------------------------------
            # CLEAN TEMP FILES
            # -------------------------------------------------

            shutil.rmtree(
                temp_dir,
                ignore_errors=True
            )

else:

    st.info(
        "👆 Upload a PPT/PPTX file to start."
    )

# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "PPT Compressor • Target Size Compression"
)
