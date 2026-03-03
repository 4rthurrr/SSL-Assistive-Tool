from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from nlp_grammar import get_ssl_sequence, get_ssl_display_sequence
from concepts import get_sinhala_display
from video_manager import find_video_path
from moviepy.editor import VideoFileClip, concatenate_videoclips
import os
import uuid
import shutil
from avatar_engine import AvatarEngine
try:
    from skeleton_generator import SkeletonGenerator
    from ai_avatar_engine import NeuralAvatarEngine
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: AI Modules missing.")

from context_engine import process_input

app = Flask(__name__)
CORS(app)

# Output Directory
OUTPUT_DIR = "static/outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Avatar Assets Directory
AVATAR_DIR = "assets/avatars"
if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

@app.route('/translate', methods=['POST'])
def translate():
    try:
        data = request.json
        text = data.get('text', '')
        style = data.get('style', 'normal')
        source_image = data.get('source_image', 'source.png')

        print(f"📨 Request: '{text}' (Style: {style}, Source: {source_image})")

        processed_text = process_input(text)
        print(f"🧠 Processed Text: '{processed_text}'")

        ssl_words = get_ssl_sequence(processed_text)
        ssl_display_words = get_ssl_display_sequence(ssl_words)
        print(f"🔤 SSL Sequence: {ssl_words}")
        print(f"🔤 SSL Display: {ssl_display_words}")

        generated_clips = []
        word_timings = []
        current_time = 0.0

        for i, word in enumerate(ssl_words):
            display_word = ssl_display_words[i] if i < len(ssl_display_words) else word
            video_path = find_video_path(word)

            if video_path:
                print(f"✅ Found video for '{word}': {video_path}")
                try:
                    clip = VideoFileClip(video_path)
                    generated_clips.append(clip)
                    duration = clip.duration
                    word_timings.append({"word": display_word, "start": current_time, "end": current_time + duration})
                    current_time += duration
                except Exception as e:
                    print(f"❌ Error loading video {video_path}: {e}")
                    word_timings.append({"word": display_word, "start": current_time, "end": current_time})
            else:
                print(f"⚠️ Missing Video for: {word}")
                word_timings.append({"word": display_word, "start": current_time, "end": current_time})

        if not generated_clips:
            return jsonify({
                "error": "No videos found",
                "ssl_grammar": ssl_words,
                "ssl_grammar_display": ssl_display_words
            }), 404

        final_clip = concatenate_videoclips(generated_clips, method="compose")
        filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(OUTPUT_DIR, filename)
        final_clip.write_videofile(output_path, codec="libx264", fps=24)
        final_clip.close()

        # AI Avatar Style
        if style == 'ai_real' and AI_AVAILABLE:
            try:
                sk_gen = SkeletonGenerator()
                driver_path = os.path.join(OUTPUT_DIR, f"driver_{filename}")
                skeleton_path = sk_gen.create_skeleton_video([output_path], driver_path)
                if skeleton_path:
                    ai_engine = NeuralAvatarEngine("config/vox-256.yaml", "checkpoints/vox-cpk.pth.tar")
                    teacher_img = os.path.join("assets", "teacher.jpg")
                    ai_filename = f"ai_{filename}"
                    ai_output_path = os.path.join(OUTPUT_DIR, ai_filename)
                    result_path = ai_engine.animate_avatar(teacher_img, skeleton_path, ai_output_path)
                    if result_path and os.path.exists(result_path):
                        return jsonify({
                            "video_url": f"http://localhost:5002/{OUTPUT_DIR}/{ai_filename}",
                            "ssl_grammar": ssl_words,
                            "ssl_grammar_display": ssl_display_words,
                            "word_timings": word_timings,
                            "mode": "ai_real"
                        })
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"❌ AI Generation Crash: {e}")

        # Skeleton Style
        if style == 'skeleton':
            from avatar_engine import generate_avatar_video
            sk_filename = f"sk_{filename}"
            sk_output_path = os.path.join(OUTPUT_DIR, sk_filename)
            success = generate_avatar_video(output_path, sk_output_path, style='skeleton')
            if success:
                return jsonify({
                    "video_url": f"http://localhost:5002/{OUTPUT_DIR}/{sk_filename}",
                    "ssl_grammar": ssl_words,
                    "ssl_grammar_display": ssl_display_words,
                    "word_timings": word_timings,
                    "mode": "skeleton"
                })

        # Normal
        return jsonify({
            "video_url": f"http://localhost:5002/{OUTPUT_DIR}/{filename}",
            "ssl_grammar": ssl_words,
            "ssl_grammar_display": ssl_display_words,
            "word_timings": word_timings,
            "mode": "normal"
        })

    except Exception as e:
        print(f"❌ Server Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/avatars', methods=['GET'])
def list_avatars():
    try:
        files = [f for f in os.listdir(AVATAR_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if os.path.exists('source.png'):
            files.insert(0, 'source.png')
        return jsonify({"avatars": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload_avatar', methods=['POST'])
def upload_avatar():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if file:
            filename = file.filename
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                return jsonify({"error": "Invalid file type. Only PNG/JPG allowed."}), 400
            file.save(os.path.join(AVATAR_DIR, filename))
            return jsonify({"message": "File uploaded successfully", "filename": filename})
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/static/outputs/<path:filename>')
def serve_video(filename):
    return send_from_directory(OUTPUT_DIR, filename)


if __name__ == '__main__':
    print("🎬 SSL Translator API running on http://localhost:5002")
    app.run(debug=True, port=5002)
