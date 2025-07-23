import streamlit as st
import cv2
import os
import zipfile
import tempfile
from PIL import Image
import io
import pandas as pd
import numpy as np

def extract_screenshots_at_timestamps(video_path, timestamps):
    """
    Video se user-defined timestamps par screenshots extract karta hai
    """
    # Video capture object banate hain
    cap = cv2.VideoCapture(video_path)
    
    # Video properties get karte hain
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    st.write(f"📹 Video Details:")
    st.write(f"- Duration: {duration:.2f} seconds")
    st.write(f"- FPS: {fps}")
    st.write(f"- Total Frames: {total_frames}")
    
    # Screenshots ke liye temporary directory banate hain
    temp_dir = tempfile.mkdtemp()
    screenshot_paths = []
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Sort timestamps to process in order
    timestamps.sort()
    
    for i, (minutes, seconds) in enumerate(timestamps):
        timestamp_seconds = minutes * 60 + seconds
        
        # Check if timestamp is valid
        if timestamp_seconds > duration:
            st.warning(f"⚠️ Timestamp {minutes}m {seconds}s exceeds video duration, skipping.")
            continue
        
        # Set video position to timestamp
        frame_position = int(timestamp_seconds * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
        
        # Read frame
        ret, frame = cap.read()
        
        if ret:
            # Screenshot filename
            screenshot_filename = f"screenshot_{minutes}m_{seconds}s.jpg"
            screenshot_path = os.path.join(temp_dir, screenshot_filename)
            
            # Frame ko save karte hain
            cv2.imwrite(screenshot_path, frame)
            screenshot_paths.append(screenshot_path)
            
            status_text.text(f"📸 Screenshot {i+1} saved at {minutes}m {seconds}s")
            
            # Progress update karte hain
            progress = (i + 1) / len(timestamps)
            progress_bar.progress(progress)
        else:
            st.warning(f"⚠️ Could not capture frame at {minutes}m {seconds}s")
    
    cap.release()
    
    st.success(f"✅ Total {len(screenshot_paths)} screenshots extracted!")
    
    return screenshot_paths, temp_dir

def create_zip_file(screenshot_paths, temp_dir):
    """
    Screenshots ko zip file mein compress karta hai
    """
    zip_path = os.path.join(temp_dir, "screenshots.zip")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for screenshot_path in screenshot_paths:
            # Zip mein sirf filename rakhte hain, pura path nahi
            arcname = os.path.basename(screenshot_path)
            zip_file.write(screenshot_path, arcname)
    
    return zip_path

def main():
    # Page config
    st.set_page_config(
        page_title="Video Screenshot Extractor",
        page_icon="📹",
        layout="wide"
    )
    
    # Title aur description
    st.title("📹 Video Screenshot Extractor")
    st.markdown("**Video upload kar ke custom timestamps par screenshots extract krain!**")
    
    # Sidebar mein instructions
    with st.sidebar:
        st.markdown("## 📋 Instructions")
        st.markdown("""
        1. **Video File Upload** krain
        2. **Timestamps** add krain (minute aur second)  
        3. **Process** button dabain
        4. **Download** zip file
        """)
        
        st.markdown("## 📝 Supported Formats")
        st.markdown("- MP4, AVI, MOV, MKV")
        st.markdown("- WMV, FLV, WebM")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "🎥 Video File Upload Krain",
            type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'],
            help="Supported formats: MP4, AVI, MOV, MKV, WMV, FLV, WebM"
        )
    
    # Timestamp input section
    if uploaded_file:
        st.markdown("### ⏱️ Screenshot Timestamps")
        st.markdown("Video mein jin timestamps par screenshot lena hai, wo add krain:")
        
        # Initialize timestamp data in session state if not already present
        if 'timestamps' not in st.session_state:
            st.session_state.timestamps = pd.DataFrame({
                'Minute': [1, 2, 3],
                'Second': [0, 30, 0]
            })
        
        # Edit timestamps using data editor
        edited_df = st.data_editor(
            st.session_state.timestamps,
            num_rows="dynamic",
            column_config={
                "Minute": st.column_config.NumberColumn(
                    "Minute",
                    help="Minutes (0-999)",
                    min_value=0,
                    max_value=999,
                    step=1,
                    format="%d"
                ),
                "Second": st.column_config.NumberColumn(
                    "Second",
                    help="Seconds (0-59)",
                    min_value=0,
                    max_value=59,
                    step=1,
                    format="%d"
                )
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Update session state
        st.session_state.timestamps = edited_df
        
        # Extract timestamps as list of tuples
        timestamps = [(int(row['Minute']), int(row['Second'])) for _, row in edited_df.iterrows()]
        
        with col2:
            st.markdown("### 📊 File Info")
            st.write(f"**File Name:** {uploaded_file.name}")
            st.write(f"**File Size:** {uploaded_file.size / (1024*1024):.2f} MB")
            st.write(f"**Total Timestamps:** {len(timestamps)}")
    
        # Processing section
        if st.button("🚀 Process Video", type="primary", use_container_width=True):
            if len(timestamps) == 0:
                st.error("❌ Please add at least one timestamp.")
            else:
                with st.spinner("🔄 Video processing... Please wait..."):
                    try:
                        # Temporary file mein video save karte hain
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                            temp_video.write(uploaded_file.read())
                            temp_video_path = temp_video.name
                        
                        # Screenshots extract karte hain
                        screenshot_paths, temp_dir = extract_screenshots_at_timestamps(temp_video_path, timestamps)
                        
                        if screenshot_paths:
                            # Zip file banate hain
                            zip_path = create_zip_file(screenshot_paths, temp_dir)
                            
                            # Download button
                            with open(zip_path, 'rb') as zip_file:
                                st.download_button(
                                    label="📥 Download Screenshots ZIP",
                                    data=zip_file.read(),
                                    file_name=f"screenshots_{uploaded_file.name.split('.')[0]}.zip",
                                    mime="application/zip",
                                    type="primary",
                                    use_container_width=True
                                )
                            
                            # Sample screenshots preview
                            st.markdown("### 🖼️ Screenshots Preview")
                            
                            # Preview all screenshots in grid
                            preview_count = min(6, len(screenshot_paths))
                            num_cols = 3
                            num_rows = (preview_count + num_cols - 1) // num_cols
                            
                            for row in range(num_rows):
                                cols = st.columns(num_cols)
                                for col in range(num_cols):
                                    idx = row * num_cols + col
                                    if idx < preview_count:
                                        with cols[col]:
                                            img = Image.open(screenshot_paths[idx])
                                            filename = os.path.basename(screenshot_paths[idx])
                                            st.image(img, caption=filename, use_column_width=True)
                        
                        else:
                            st.error("❌ No screenshots could be extracted from the video.")
                        
                        # Cleanup temp files
                        os.unlink(temp_video_path)
                        
                    except Exception as e:
                        st.error(f"❌ Error processing video: {str(e)}")
                        st.error("Please make sure the video file is valid and not corrupted.")
    
    # Footer
    st.markdown("---")
    st.markdown("**💡 Tips:**")
    st.markdown("- Click '+' button to add more timestamps")
    st.markdown("- Timestamps ko precise rakhne ke liye seconds 0-59 tak hi rakhein") 
    st.markdown("- Agar timestamp video duration se zyada hai to wo skip ho jaye ga")

if __name__ == "__main__":
    main()
