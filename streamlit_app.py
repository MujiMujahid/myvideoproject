import streamlit as st
import cv2
import os
import zipfile
import tempfile
from PIL import Image
import re

def extract_screenshots_at_timestamps(video_path, timestamps):
    """
    Video se user-defined timestamps par screenshots extract karta hai
    """
    cap = cv2.VideoCapture(video_path)
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    temp_dir = tempfile.mkdtemp()
    screenshot_paths = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    timestamps.sort()
    
    for i, (minutes, seconds) in enumerate(timestamps):
        timestamp_seconds = minutes * 60 + seconds
        
        if timestamp_seconds > duration:
            st.warning(f"⚠️ Timestamp {minutes}m {seconds}s exceeds video duration, skipping.")
            continue
        
        frame_position = int(timestamp_seconds * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_position)
        
        ret, frame = cap.read()
        
        if ret:
            screenshot_filename = f"{minutes}-{seconds:02d}.jpg"
            screenshot_path = os.path.join(temp_dir, screenshot_filename)
            
            cv2.imwrite(screenshot_path, frame)
            screenshot_paths.append(screenshot_path)
            
            status_text.text(f"📸 Screenshot {i+1} saved at {minutes}m {seconds}s")
            
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
            arcname = os.path.basename(screenshot_path)
            zip_file.write(screenshot_path, arcname)
    
    return zip_path

def parse_bulk_timestamps(text):
    """
    Convert bulk timestamp text (e.g., "1:23\n5:2\n2:39") to a list of (minute, second) tuples
    """
    timestamps = []
    pattern = r'(\d+):(\d+)'
    
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
            
        match = re.match(pattern, line)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            if seconds > 59:
                seconds = 59
            timestamps.append((minutes, seconds))
    
    return timestamps

def main():
    st.set_page_config(
        page_title="Video Screenshot Extractor",
        page_icon="📹"
    )
    
    st.title("📹 Video Screenshot Extractor")
    
    uploaded_file = st.file_uploader(
        "Video Upload",
        type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm']
    )
    
    if uploaded_file:
        if 'bulk_timestamps_text' not in st.session_state:
            st.session_state.bulk_timestamps_text = "1:00\n2:30\n3:00"
        
        bulk_timestamps_text = st.text_area(
            "Enter timestamps (minute:second format, one per line)",
            value=st.session_state.bulk_timestamps_text,
            height=200
        )
        
        st.session_state.bulk_timestamps_text = bulk_timestamps_text
        
        timestamps = parse_bulk_timestamps(bulk_timestamps_text)
    
        if st.button("Process Video", type="primary"):
            if len(timestamps) == 0:
                st.error("Please add at least one valid timestamp.")
            else:
                with st.spinner("Processing video... Please wait..."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                            temp_video.write(uploaded_file.read())
                            temp_video_path = temp_video.name
                        
                        screenshot_paths, temp_dir = extract_screenshots_at_timestamps(temp_video_path, timestamps)
                        
                        if screenshot_paths:
                            zip_path = create_zip_file(screenshot_paths, temp_dir)
                            
                            with open(zip_path, 'rb') as zip_file:
                                st.download_button(
                                    label="Download Screenshots ZIP",
                                    data=zip_file.read(),
                                    file_name=f"screenshots_{uploaded_file.name.split('.')[0]}.zip",
                                    mime="application/zip",
                                    type="primary"
                                )
                        
                        else:
                            st.error("No screenshots could be extracted from the video.")
                        
                        os.unlink(temp_video_path)
                        
                    except Exception as e:
                        st.error(f"Error processing video: {str(e)}")

if __name__ == "__main__":
    main()
