import os
import cv2
import tempfile
from typing import Optional

def add_captions_to_video(input_video_path: str, caption_text: str, output_video_path: str) -> Optional[str]:
    """
    Overlays transcribed caption text onto a webcam video recording frame by frame using OpenCV.
    Returns path to output captioned video.
    """
    if not os.path.exists(input_video_path):
        print(f"Video file not found: {input_video_path}")
        return None
        
    try:
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            return input_video_path
            
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0 or fps > 120:
            fps = 30.0
            
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        # Prepare text wrapping for overlay
        words = caption_text.split()
        lines = []
        current_line = []
        for w in words:
            current_line.append(w)
            if len(" ".join(current_line)) > 35:
                lines.append(" ".join(current_line[:-1]))
                current_line = [w]
        if current_line:
            lines.append(" ".join(current_line))
            
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Draw semi-transparent dark banner at bottom of frame
            banner_h = min(120, int(height * 0.25))
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, height - banner_h), (width, height), (0, 0, 0), -1)
            alpha = 0.65
            frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
            
            # Render caption text lines
            y_offset = height - banner_h + 35
            for line in lines[:3]:
                cv2.putText(frame, line, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX,
                            0.75, (255, 255, 255), 2, cv2.LINE_AA)
                y_offset += 32
                
            out.write(frame)
            
        cap.release()
        out.release()
        return output_video_path
    except Exception as e:
        print(f"Error overlaying captions on video: {e}")
        return input_video_path
