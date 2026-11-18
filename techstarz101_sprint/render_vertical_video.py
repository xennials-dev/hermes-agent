from pathlib import Path
import numpy as np
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

# Ensure Pillow 10+ compatibility for MoviePy 1.x resize()
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip


def _make_text_banner_clip(text_content: str, width: int, duration: float):
    """Try MoviePy TextClip first; fall back to PIL-rendered ImageClip if ImageMagick is absent."""
    try:
        return (
            TextClip(
                text_content,
                fontsize=60,
                color="white",
                font="Arial",
                bg_color="rgba(0,0,0,0.5)",
            )
            .set_pos(("center", "bottom"))
            .set_duration(duration)
        )
    except Exception:
        font_path = r"C:\Windows\Fonts\arialbd.ttf"
        if not Path(font_path).is_file():
            font_path = r"C:\Windows\Fonts\arial.ttf"
        font = PIL.ImageFont.truetype(font_path, 52) if Path(font_path).is_file() else PIL.ImageFont.load_default()

        dummy = PIL.Image.new("RGBA", (width, 240), (0, 0, 0, 0))
        draw = PIL.ImageDraw.Draw(dummy)
        # Word-wrap to fit within 1000px width
        words = text_content.split()
        lines: list[str] = []
        current = ""
        for w in words:
            test = f"{current} {w}".strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= width - 80 or not current:
                current = test
            else:
                lines.append(current)
                current = w
        if current:
            lines.append(current)

        line_h = 68
        pad_y = 32
        banner_h = len(lines) * line_h + pad_y * 2
        img = PIL.Image.new("RGBA", (width, banner_h + 80), (0, 0, 0, 0))
        draw = PIL.ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (width, banner_h)], fill=(0, 0, 0, 160))

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            x = (width - tw) // 2
            y = pad_y + i * line_h
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

        return ImageClip(np.array(img)).set_pos(("center", "bottom")).set_duration(duration)


def render_vertical_video(input_path, output_path, text_content):
    # Load the source video
    clip = VideoFileClip(str(input_path))

    # Target dimensions for 9:16 vertical (e.g., 1080x1920)
    target_width = 1080
    target_height = 1920

    # Resize and crop/pad to fit 9:16 aspect ratio
    # (Scale video to fill width or height so no black bars appear, then center crop)
    w, h = clip.size
    scale_factor = max(target_width / w, target_height / h)
    resized_clip = clip.resize(scale_factor)

    x_center = resized_clip.w / 2
    y_center = resized_clip.h / 2
    final_video = resized_clip.crop(
        x1=max(0, x_center - (target_width / 2)),
        x2=min(resized_clip.w, x_center + (target_width / 2)),
        y1=max(0, y_center - (target_height / 2)),
        y2=min(resized_clip.h, y_center + (target_height / 2)),
    )

    # Create text overlay
    txt_clip = _make_text_banner_clip(text_content, target_width, final_video.duration)

    # Composite video and text
    result = CompositeVideoClip([final_video, txt_clip], size=(target_width, target_height))

    # Write output file
    result.write_videofile(
        str(output_path),
        fps=30,
        codec="libx264",
        audio_codec="aac",
    )
    clip.close()
    result.close()


if __name__ == "__main__":
    base_dir = Path(r"C:\Users\tee\OneDrive\Desktop\techstarz101")
    src = base_dir / "summary_of_services.mp4" if (base_dir / "summary_of_services.mp4").is_file() else Path("summary_of_services.mp4")
    out = base_dir / "output_vertical.mp4" if base_dir.is_dir() else Path("output_vertical.mp4")
    render_vertical_video(
        input_path=src,
        output_path=out,
        text_content="Stop renting your software. Own your AI stack.",
    )

