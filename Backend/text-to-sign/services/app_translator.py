import sys
import os

# ── path bootstrap ────────────────────────────────────────────────────────────
# This file lives at:  Backend/text-to-sign/services/app_translator.py
# Make sibling packages importable regardless of how the script is invoked.
_HERE = os.path.dirname(os.path.abspath(__file__))   # .../text-to-sign/services
_TS   = os.path.dirname(_HERE)                        # .../text-to-sign
_ROOT = os.path.dirname(_TS)                          # .../Backend
for _p in [
    _HERE,                                             # video_manager, avatar_engine, ai_avatar_engine
    os.path.join(_TS, "nlp"),                          # nlp_grammar, context_engine, sinhala_sentence_parser
    os.path.join(_TS, "ai", "concepts"),               # concepts, concept_registry
    os.path.join(_TS, "ai", "models"),                 # skeleton_generator, inference_engine
    os.path.join(_TS, "ai", "embeddings"),             # embeddings_handler
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)
# ──────────────────────────────────────────────────────────────────────────────

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from nlp_grammar import get_ssl_sequence, get_ssl_display_sequence, get_ssl_sequence_with_blocks
from concepts import get_sinhala_display
from video_manager import find_video_path

# moviepy import (supports both 1.x and 2.x API)
try:
    # moviepy 2.x
    from moviepy import VideoFileClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # moviepy 1.x
        from moviepy.editor import VideoFileClip, concatenate_videoclips
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False
        print(
            "Warning: moviepy is not installed or misconfigured. "
            "/translate endpoint will be disabled. "
            "Install it with: python -m pip install moviepy"
        )

import uuid
import shutil
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

# Output Directory — absolute so write and serve always resolve correctly
OUTPUT_DIR = os.path.join(_ROOT, "static", "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Avatar Assets Directory
AVATAR_DIR = os.path.join(_TS, "assets", "avatars")
os.makedirs(AVATAR_DIR, exist_ok=True)


#When the user types a Sinhala sentence, it comes here.
@app.route('/translate', methods=['POST'])
def translate():
    if not MOVIEPY_AVAILABLE:
        return jsonify({
            "error": "dependency_missing",
            "message": "moviepy is not installed in the backend environment. "
                       "Please install it with 'python -m pip install moviepy' "
                       "and restart the backend server."
        }), 500

    try:
        data = request.json
        text = data.get('text', '')
        style = data.get('style', 'normal')
        source_image = data.get('source_image', 'source.png')

        print(f"📨 Request: '{text}' (Style: {style}, Source: {source_image})")

        processed_text = process_input(text)
        print(f"🧠 Processed Text: '{processed_text}'")

        # ── NEW: sentence-aware multi-block pipeline ─────────────────────────
        # IMPORTANT: pass the ORIGINAL text (with commas / periods) so that
        # the semantic parser can segment clauses correctly.  process_input()
        # strips punctuation and collapses clause boundaries - it is only used
        # by the legacy flat pipeline fallback path.
        parsed = get_ssl_sequence_with_blocks(text)
        ssl_words        = parsed["flat_sequence"]
        ssl_display_words= parsed["flat_display"]
        animation_blocks = parsed["blocks"]        # per-clause data for frontend
        semantic_json    = parsed["semantic_json"]  # full parse tree

        print(f"🔤 SSL Sequence  : {ssl_words}")
        print(f"🔤 SSL Display   : {ssl_display_words}")
        print(f"📦 Clauses found : {len(animation_blocks)}")

        #  video stitching (unchanged logic, operates on flat sequence) 
        # MANUAL IMPLEMENTATION
        # Word-to-video timing synchronization: cumulative duration tracking per sign clip
        # Produces word_timings array [{word, start_sec, end_sec}] aligned to output video
        # Enables frontend word highlight sync during sign playback for language learners
        generated_clips = []
        word_timings    = []
        current_time    = 0.0

        for i, word in enumerate(ssl_words):
            display_word = ssl_display_words[i] if i < len(ssl_display_words) else word
            video_path   = find_video_path(word)

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
                "error":              "concept_not_found",
                "message":            f'Sign Language video not found for: "{text}". Try a simpler or different Sinhala word.',
                "ssl_grammar":        ssl_words,
                "ssl_grammar_display": ssl_display_words,
                "animation_blocks":   animation_blocks,
                "semantic_json":      semantic_json,
            }), 200
 # Crearte single video clip from multiple video clips 
        final_clip = concatenate_videoclips(generated_clips, method="compose")
        filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(OUTPUT_DIR, filename)
        final_clip.write_videofile(output_path, codec="libx264", fps=24)
        final_clip.close()

        # CUSTOM OPTIMIZATION
        # Three-tier avatar rendering with graceful fallback: ai_real → skeleton → normal
        # Exception handling per tier with resource cleanup prevents total failure
        # Ensures sign output is always delivered regardless of GPU/model availability
        # AI Avatar Style
        if style == 'ai_real' and AI_AVAILABLE:
            try:
                sk_gen = SkeletonGenerator()
                driver_path = os.path.join(OUTPUT_DIR, f"driver_{filename}")
                skeleton_path = sk_gen.create_skeleton_video([output_path], driver_path)
                if skeleton_path:
                    ai_engine = NeuralAvatarEngine("core/config/vox-256.yaml", "text-to-sign/checkpoints/vox-cpk.pth.tar")
                    teacher_img = os.path.join("text-to-sign", "assets", "teacher.jpg")
                    ai_filename = f"ai_{filename}"
                    ai_output_path = os.path.join(OUTPUT_DIR, ai_filename)
                    result_path = ai_engine.animate_avatar(teacher_img, skeleton_path, ai_output_path)
                    if result_path and os.path.exists(result_path):
                        return jsonify({
                            "video_url": f"http://localhost:5002/videos/{ai_filename}",
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
                    "video_url": f"http://localhost:5002/videos/{sk_filename}",
                    "ssl_grammar": ssl_words,
                    "ssl_grammar_display": ssl_display_words,
                    "word_timings": word_timings,
                    "mode": "skeleton"
                })

        # Normal
         #After generating video file, upload video to the frontend using this return statement 
        return jsonify({
            "video_url":            f"http://localhost:5002/videos/{filename}",
            "ssl_grammar":          ssl_words,
            "ssl_grammar_display":  ssl_display_words,
            "word_timings":         word_timings,
            "animation_blocks":     animation_blocks,   # NEW: per-clause blocks
            "semantic_json":        semantic_json,       # NEW: full parse tree
            "mode":                 "normal"
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

#The finished video is used to stream (display) to the Frontend.
@app.route('/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory(OUTPUT_DIR, filename)

# Sinhala characters are set to display correctly even on the server's console.
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    print("SSL Translator API running on http://localhost:5002")
    app.run(debug=True, port=5002)
