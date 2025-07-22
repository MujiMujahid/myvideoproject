import streamlit as st
import cv2
import os
import zipfile
import tempfile
from PIL import Image
import io

def extract_screenshots(video_path, interval_seconds):
    """
    Video se specific interval par screenshots extract karta hai
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
    
    # Interval frames calculate karte hain
    interval_frames = interval_seconds * fps
    
    frame_count = 0
    screenshot_count = 0
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while True:
        ret, frame = cap.read()
        
        if not ret:
            break
            
        # Har interval par screenshot lete hain
        if frame_count % interval_frames == 0:
            # Screenshot filename
            screenshot_filename = f"screenshot_{screenshot_count:04d}_at_{frame_count//fps}s.jpg"
            screenshot_path = os.path.join(temp_dir, screenshot_filename)
            
            # Frame ko save karte hain
            cv2.imwrite(screenshot_path, frame)
            screenshot_paths.append(screenshot_path)
            
            screenshot_count += 1
            status_text.text(f"📸 Screenshot {screenshot_count} saved at {frame_count//fps}s")
        
        frame_count += 1
        
        # Progress update karte hain
        progress = frame_count / total_frames
        progress_bar.progress(progress)
    
    cap.release()
    
    st.success(f"✅ Total {screenshot_count} screenshots extracted!")
    
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
    st.markdown("**Video upload kar ke specific intervals par screenshots extract krain!**")
    
    # Sidebar mein instructions
    with st.sidebar:
        st.markdown("## 📋 Instructions")
        st.markdown("""
        1. **Video File Upload** krain
        2. **Interval (seconds)** set krain  
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
        
        # Interval input
        interval = st.number_input(
            "⏱️ Screenshot Interval (Seconds)",
            min_value=1,
            max_value=60,
            value=5,
            help="Har kitne seconds ke baad screenshot lena hai"
        )
        
    with col2:
        if uploaded_file:
            st.markdown("### 📊 File Info")
            st.write(f"**File Name:** {uploaded_file.name}")
            st.write(f"**File Size:** {uploaded_file.size / (1024*1024):.2f} MB")
            st.write(f"**Screenshot Interval:** {interval} seconds")
    
    # Processing section
    if uploaded_file is not None:
        if st.button("🚀 Process Video", type="primary", use_container_width=True):
            with st.spinner("🔄 Video processing... Please wait..."):
                try:
                    # Temporary file mein video save karte hain
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                        temp_video.write(uploaded_file.read())
                        temp_video_path = temp_video.name
                    
                    # Screenshots extract karte hain
                    screenshot_paths, temp_dir = extract_screenshots(temp_video_path, interval)
                    
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
                        st.markdown("### 🖼️ Sample Screenshots Preview")
                        
                        # Pehle 4 screenshots ka preview dikhate hain
                        preview_count = min(4, len(screenshot_paths))
                        cols = st.columns(preview_count)
                        
                        for i in range(preview_count):
                            with cols[i]:
                                img = Image.open(screenshot_paths[i])
                                st.image(img, caption=f"Screenshot {i+1}", use_column_width=True)
                    
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
    st.markdown("- Chhote intervals (1-2 seconds) zyada screenshots denge")
    st.markdown("- Bade intervals (10+ seconds) kam screenshots denge") 
    st.markdown("- Video quality aur size ke according processing time vary hoga")

if __name__ == "__main__":
    main()
